# 2018 scale-factor sample
# dataset : BuToJpsiK_BMuonFilter_SoftQCDnonD_TuneCP5_13TeV-pythia8-evtgen
# McM     : BPH-RunIISummer20UL16GENAPV-00009
# view    : https://cms-pdmv-prod.web.cern.ch/mcm/requests?prepid=BPH-RunIISummer20UL16GENAPV-00009
# api     : https://cms-pdmv-prod.web.cern.ch/mcm/public/restapi/requests/get/BPH-RunIISummer20UL16GENAPV-00009

import FWCore.ParameterSet.Config as cms

from Configuration.Generator.Pythia8CommonSettings_cfi import *
from Configuration.Generator.MCTunes2017.PythiaCP5Settings_cfi import *
from GeneratorInterface.EvtGenInterface.EvtGenSetting_cff import *

generator = cms.EDFilter(
    "Pythia8GeneratorFilter",
    pythiaHepMCVerbosity = cms.untracked.bool(False),
    maxEventsToPrint = cms.untracked.int32(0),
    pythiaPylistVerbosity = cms.untracked.int32(0),
    filterEfficiency = cms.untracked.double(2.100e-02),
    crossSection = cms.untracked.double(540000000.),
    comEnergy = cms.double(13000.0),
    ExternalDecays = cms.PSet(
        EvtGen130 = cms.untracked.PSet(
            decay_table = cms.string('GeneratorInterface/EvtGenInterface/data/DECAY_2014_NOLONGLIFE.DEC'),
            particle_property_file = cms.FileInPath('GeneratorInterface/EvtGenInterface/data/evt_2014.pdl'),
            user_decay_file = cms.vstring('GeneratorInterface/EvtGenInterface/data/Bu_JpsiK.dec'),
            list_forced_decays = cms.vstring('MyB+', 'MyB-'),
            operates_on_particles = cms.vint32(),
            convertPythiaCodes = cms.untracked.bool(False),
        ),
        parameterSets = cms.vstring('EvtGen130')
    ),
    PythiaParameters = cms.PSet(
        pythia8CommonSettingsBlock,
        pythia8CP5SettingsBlock,
        processParameters = cms.vstring(
            "SoftQCD:nonDiffractive = on",
            'PTFilter:filter = on', # this turn on the filter
            'PTFilter:quarkToFilter = 5', # PDG id of q quark
            'PTFilter:scaleToFilter = 1.0'),
        parameterSets = cms.vstring(
            'pythia8CommonSettings',
            'pythia8CP5Settings',
            'processParameters',
        )
    )
)


generator.PythiaParameters.processParameters.extend(EvtGenExtraParticles)

bfilter = cms.EDFilter(
    "PythiaFilter",
    MaxEta = cms.untracked.double(9999.),
    MinEta = cms.untracked.double(-9999.),
    ParticleID = cms.untracked.int32(521)
)

jpsifilter = cms.EDFilter(
    "PythiaDauVFilter",
    MotherID = cms.untracked.int32(521),
    ParticleID = cms.untracked.int32(443),
    NumberDaughters = cms.untracked.int32(2),
    DaughterIDs = cms.untracked.vint32(13, -13),
    MinPt = cms.untracked.vdouble(3.5, 3.5),
    MinEta = cms.untracked.vdouble(-2.5, -2.5),
    MaxEta = cms.untracked.vdouble(2.5, 2.5),
    verbose = cms.untracked.int32(1)
)

kfilter = cms.EDFilter(
    "PythiaDauVFilter",
    MotherID = cms.untracked.int32(0),
    ParticleID = cms.untracked.int32(521),
    NumberDaughters = cms.untracked.int32(2),
    DaughterIDs = cms.untracked.vint32(443, 321),
    MinPt = cms.untracked.vdouble(-99.0, 0.4),
    MinEta = cms.untracked.vdouble(-9999.0, -2.5),
    MaxEta = cms.untracked.vdouble(9999.0, 2.5),
    verbose = cms.untracked.int32(1)
)

ProductionFilterSequence = cms.Sequence(generator*bfilter*jpsifilter*kfilter)
