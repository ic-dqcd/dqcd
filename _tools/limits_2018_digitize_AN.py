#!/usr/bin/env python3
"""
Digitise the 2018 limit plots of the analysis note (AN2023_119, Fig. 57 scenario A / Fig. 58 scenario B1) from the
PDF's vector paths (no pixel work): PyMuPDF get_drawings() gives every matplotlib path with its colour, dash pattern
and vertices in page coordinates; the log axes are calibrated from the major tick marks and their "10^k" labels.

Per panel: expected = black dashed line, observed = black solid line, 68% band = green fill, 95% band = yellow fill
(fill_between polygons: upper edge forward, lower edge backwards). Values are tabulated at the ctau vertices of the
expected line, bands interpolated there in log-log.

Output: limits_2018/limits_2018_AN_sc<A|B1>_mA<m>.txt, same columns as the HEPData files
    ctau_mm observed expected exp68_down exp68_up exp95_down exp95_up
Usage: limits_2018_digitize_AN.py <AN.pdf> [--pages 56,57] [--out limits_2018] [--check check.pdf]
"""
import argparse, os, re, sys
import numpy as np

YELLOW = (0.9607843160629272, 0.7333333492279053, 0.3294117748737335)   # 95% band
GREEN = (0.3764705955982208, 0.4627451002597809, 0.2549019455909729)    # 68% band


def close(a, b, tol=0.01):
    return all(abs(x - y) < tol for x, y in zip(a, b))


def spans(page):
    out = []
    for b in page.get_text("dict")["blocks"]:
        for l in b.get("lines", []):
            for s in l["spans"]:
                out.append((s["bbox"], s["text"], s["size"]))
    return out


def axes_rects(drawings):
    """matplotlib: figure background (white) then axes background (white) inside it."""
    whites = [d["rect"] for d in drawings if d["type"] == "f" and d["fill"] == (1.0, 1.0, 1.0)]
    return [r for r in whites if any(o != r and o.contains(r) for o in whites)]


def tick_labels(sp, ax, axis):
    """(coordinate, decade exponent) of the "10^k" labels along the bottom (x) or left (y) of the axes rect."""
    base = [(bb, t, size) for bb, t, size in sp if t == "10"]
    bsize = max(size for _, _, size in base) if base else 0
    sup = [(bb, t) for bb, t, size in sp if size < 0.85 * bsize]        # exponents are smaller glyphs
    out = []
    for bb, _, size in base:
        if size < 0.85 * bsize:
            continue
        x0, y0, x1, y1 = bb
        if axis == "x" and not (ax.y1 - 1 < y0 < ax.y1 + 12 and ax.x0 - 8 < x0 < ax.x1 + 2):
            continue
        if axis == "y" and not (x1 < ax.x0 + 1 and x1 > ax.x0 - 10 and ax.y0 - 6 < y0 < ax.y1 + 2):
            continue
        exp = "".join(t for sb, t in sorted(sup, key=lambda s: s[0][0])
                      if x1 - 0.5 <= sb[0] <= x1 + 10 and abs(sb[1] - y0) < 3)
        # the minus sign is "−", or an unmapped glyph that comes out as a blank (ROOT-style pages)
        exp = exp.replace("−", "-").replace("–", "-").replace(" ", "-").strip()
        if not re.fullmatch(r"-?\d+", exp):
            continue
        out.append(((x0 + x1) / 2 if axis == "x" else (y0 + y1) / 2, int(exp)))
    return out


def major_ticks(drawings, ax, axis):
    """Positions of the longest tick marks on the bottom / left spine."""
    ticks = []
    for d in drawings:
        if d["type"] not in ("fs", "s") or len(d["items"]) != 1 or d["items"][0][0] != "l":
            continue
        r = d["rect"]
        # ticks drawn outward (y0 on the spine) or inward (y1 on the spine)
        if axis == "x" and r.width < 0.05 and min(abs(r.y0 - ax.y1), abs(r.y1 - ax.y1)) < 0.5 \
                and ax.x0 - 1 <= r.x0 <= ax.x1 + 1 and r.height < 8:
            ticks.append((r.x0, r.height))
        if axis == "y" and r.height < 0.05 and min(abs(r.x1 - ax.x0), abs(r.x0 - ax.x0)) < 0.5 \
                and ax.y0 - 1 <= r.y0 <= ax.y1 + 1 and r.width < 8:
            ticks.append((r.y0, r.width))
    if not ticks:
        return []
    lmax = max(l for _, l in ticks)
    return sorted({round(p, 3) for p, l in ticks if l > 0.8 * lmax})


def calibrate(drawings, sp, ax, axis):
    """log10(value) = a + b * coord, from major ticks matched to the nearest 10^k label."""
    ticks, labels = major_ticks(drawings, ax, axis), tick_labels(sp, ax, axis)
    pairs = []
    for t in ticks:
        if labels:
            c, k = min(labels, key=lambda l: abs(l[0] - t))
            if abs(c - t) < 6:
                pairs.append((t, k))
    if len(pairs) < 2:
        sys.exit(f"axis {axis}: cannot calibrate ({len(ticks)} ticks, {len(labels)} labels, {len(pairs)} pairs)")
    ts, ks = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs], float)
    b, a = np.polyfit(ts, ks, 1)
    resid = np.abs(a + b * ts - ks).max()
    return (lambda c: 10 ** (a + b * np.asarray(c))), len(pairs), resid, pairs


def vertices(d):
    pts = []
    for it in d["items"]:
        for p in it[1:]:
            if hasattr(p, "x"):
                q = (p.x, p.y)
                if not pts or not close(pts[-1], q, 1e-3):
                    pts.append(q)
    return np.array(pts)


def band_edges(poly):
    """fill_between polygon -> (upper, lower) vertex arrays sorted in x (upper = smaller page y).
    The path runs forward along one edge to the largest x and back along the other; when the band is
    clipped at the frame, the two edge points at the same x sit next to each other at the turns."""
    x = poly[:, 0]
    i1 = int(np.argmax(x))
    fwd, bwd = poly[:i1 + 1], poly[i1 + 1:]
    if len(fwd) > 1 and abs(fwd[0, 0] - fwd[1, 0]) < 1e-6:     # clip corner: first point belongs to the way back
        bwd, fwd = np.vstack([bwd, fwd[:1]]), fwd[1:]
    span = x.max() - x.min()
    if len(fwd) < 2 or len(bwd) < 2 or np.ptp(fwd[:, 0]) < 0.5 * span or np.ptp(bwd[:, 0]) < 0.5 * span:
        sys.exit(f"band polygon not understood: {len(fwd)} / {len(bwd)} edge points")
    fwd, bwd = fwd[np.argsort(fwd[:, 0], kind="stable")], bwd[np.argsort(bwd[:, 0], kind="stable")]
    return (fwd, bwd) if fwd[:, 1].mean() < bwd[:, 1].mean() else (bwd, fwd)


def interp_loglog(xq, pts, fx, fy):
    X, Y = np.log10(fx(pts[:, 0])), np.log10(fy(pts[:, 1]))
    o = np.argsort(X)
    return 10 ** np.interp(np.log10(xq), X[o], Y[o])


def panel_meta(sp, fig_rect):
    txt = [(bb, t) for bb, t, size in sp if fig_rect.contains(fitz.Point(bb[0], bb[1]))]
    scen = next((re.search(r"Scenario (\w+)", t).group(1) for bb, t in txt if "Scenario" in t), None)
    masses = sorted((bb[1], float(m.group(1))) for bb, t in txt for m in [re.search(r"=\s*([\d.]+)\s*GeV", t)] if m)
    return scen, [m for _, m in masses]


def main():
    global fitz
    import fitz
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", default="56,57", help="1-based PDF pages holding the scenario A / B1 figures")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "limits_2018"))
    ap.add_argument("--check", default="", help="PDF with the digitised curves redrawn next to the page crops")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    doc = fitz.open(a.pdf)
    results = []
    for pno in [int(p) for p in a.pages.split(",")]:
        page = doc[pno - 1]
        dr, sp = page.get_drawings(), spans(page)
        for ax in axes_rects(dr):
            fig_rect = next(d["rect"] for d in dr if d["type"] == "f" and d["fill"] == (1.0, 1.0, 1.0)
                            and d["rect"] != ax and d["rect"].contains(ax))
            scen, masses = panel_meta(sp, fig_rect)
            if scen not in ("A", "B1"):
                continue
            fx, nx, rx, px = calibrate(dr, sp, ax, "x")
            fy, ny, ry, py = calibrate(dr, sp, ax, "y")
            inside = lambda d: ax.contains(d["rect"]) or (d["rect"].intersects(ax) and d["rect"].width > 5)
            black = [d for d in dr if d["type"] == "s" and d["color"] == (0, 0, 0) and inside(d)
                     and d["rect"].width > 5 and d["rect"].height > 2 and (d.get("width") or 0) > 0.3]
            dashed = [d for d in black if d.get("dashes") and "[]" not in d["dashes"]]
            solid = [d for d in black if d not in dashed]
            yellow = [d for d in dr if d["type"] == "fs" and d["fill"] and close(d["fill"], YELLOW) and inside(d) and d["rect"].width > 20]
            green = [d for d in dr if d["type"] == "fs" and d["fill"] and close(d["fill"], GREEN) and inside(d) and d["rect"].width > 20]
            if not (len(dashed) == 1 and len(solid) == 1 and len(yellow) >= 1 and len(green) == 1):
                sys.exit(f"page {pno} panel {ax}: dashed {len(dashed)} solid {len(solid)} yellow {len(yellow)} green {len(green)}")
            exp, obs = vertices(dashed[0]), vertices(solid[0])
            ct = fx(exp[:, 0])
            exp_v, obs_v = fy(exp[:, 1]), interp_loglog(ct, obs, fx, fy)
            g_up, g_lo = band_edges(vertices(green[0]))
            # the 95% band may be split in two polygons (above/below the 68% one) or be a single one
            ypoly = max(yellow, key=lambda d: d["rect"].height)
            y_up, y_lo = band_edges(vertices(ypoly))
            if len(yellow) > 1:   # two half-bands: take the outer edge of each
                tops = [band_edges(vertices(d)) for d in yellow]
                y_up = min((t[0] for t in tops), key=lambda e: e[:, 1].mean())
                y_lo = max((t[1] for t in tops), key=lambda e: e[:, 1].mean())
            rows = np.column_stack([ct, obs_v, exp_v,
                                    interp_loglog(ct, g_lo, fx, fy), interp_loglog(ct, g_up, fx, fy),
                                    interp_loglog(ct, y_lo, fx, fy), interp_loglog(ct, y_up, fx, fy)])
            mpi, mA = (masses + [np.nan, np.nan])[:2]
            name = os.path.join(a.out, f"limits_2018_AN_sc{scen}_mA{mA:g}".replace(".", "p") + ".txt")
            with open(name, "w") as o:
                o.write(f"# 2018 DQCD search (41.6 fb-1, 13 TeV), digitised from the vector paths of {os.path.basename(a.pdf)} "
                        f"page {pno} (scenario A: Fig. 57, B1: Fig. 58)\n")
                o.write(f"# scenario {scen}, m_pi3 = {mpi:g} GeV, m_A' = {mA:g} GeV\n")
                o.write(f"# axis calibration: x {nx} ticks (max residual {rx:.1e} decades), y {ny} ticks (max residual {ry:.1e} decades)\n")
                o.write("# 95% CL upper limits on BR(H -> psi psi) at the ctau vertices of the median-expected line; "
                        "observed and bands interpolated there in log-log\n")
                o.write("# columns: ctau_mm observed expected exp68_down exp68_up exp95_down exp95_up\n")
                for r in rows:
                    o.write(f"{r[0]:8.3g} " + " ".join(f"{x:11.5g}" for x in r[1:]) + "\n")
            print(f"{name}: {len(rows)} points, ctau {ct.min():.3g}..{ct.max():.3g}, x-cal {nx} ticks ({rx:.0e}), y-cal {ny} ticks ({ry:.0e})")
            results.append((pno, ax, scen, mpi, mA, rows))
    if a.check:
        check_plot(doc, results, a.check)


def check_plot(doc, results, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    with PdfPages(path) as pdf:
        for pno, ax, scen, mpi, mA, rows in results:
            page = doc[pno - 1]
            fig_rect = next(r for r in axes_rects_outer(page) if r.contains(ax))
            pix = page.get_pixmap(clip=fig_rect, dpi=300)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
            a1.imshow(img); a1.axis("off"); a1.set_title(f"AN page {pno}: scenario {scen}, m_pi3 {mpi:g}, m_A' {mA:g} GeV")
            ct = rows[:, 0]
            a2.fill_between(ct, rows[:, 5], rows[:, 6], color="#f5bb54", label="95% expected")
            a2.fill_between(ct, rows[:, 3], rows[:, 4], color="#607641", label="68% expected")
            a2.plot(ct, rows[:, 2], "k--", label="median expected")
            a2.plot(ct, rows[:, 1], "k-o", ms=3, label="observed")
            a2.set_xscale("log"); a2.set_yscale("log"); a2.set_xlabel("ctau [mm]"); a2.set_ylabel("95% CL on BR(H -> psi psi)")
            a2.legend(fontsize=8); a2.set_title("digitised")
            fig.tight_layout(); pdf.savefig(fig); plt.close(fig)


def axes_rects_outer(page):
    dr = page.get_drawings()
    whites = [d["rect"] for d in dr if d["type"] == "f" and d["fill"] == (1.0, 1.0, 1.0)]
    return [r for r in whites if not any(o != r and o.contains(r) for o in whites)]


if __name__ == "__main__":
    main()
