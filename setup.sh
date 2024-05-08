#!/usr/bin/env bash

action() {
    #
    # global variables
    #

    # determine the directory of this file
    cd nanoaod_base_analysis
    #local this_file="$( [ ! -z "$ZSH_VERSION" ] && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    #local this_dir="$( cd "$( dirname "$this_file" )" && pwd )"
    export CMT_BASE="DUMMY"
    if [[ "$CMT_BASE" == "DUMMY" ]]; then
        echo "Need to change the path stored in CMT_BASE to the present folder"
        return "1"
    fi 

    # check if this setup script is sourced by a remote job
    if [ "$CMT_ON_HTCONDOR" = "1" ]; then
        export CMT_REMOTE_JOB="1"
    else
        export CMT_REMOTE_JOB="0"
    fi

    # check if we're on lxplus
    if [[ "$( hostname )" = lxplus*.cern.ch ]]; then
        export CMT_ON_LXPLUS="1"
    else
        export CMT_ON_LXPLUS="0"
    fi

    # check if we're at ic
    if [[ "$( hostname -f )" = *.hep.ph.ic.ac.uk ]]; then
        export CMT_ON_IC="1"
    else
        export CMT_ON_IC="0"
    fi

    # default cern name
    if [ -z "$CMT_CERN_USER" ]; then
        if [ "$CMT_ON_LXPLUS" = "1" ]; then
            export CMT_CERN_USER="$( whoami )"
        elif [ "$CMT_ON_IC" = "0" ]; then
            2>&1 echo "please set CMT_CERN_USER to your CERN user name and try again"
            return "1"
        fi
    fi

    # default ciemat name
    if [ -z "$CMT_IC_USER" ]; then
        if [ "$CMT_ON_IC" = "1" ]; then
            export CMT_IC_USER="$( whoami )"
        # elif [ "$CMT_ON_LXPLUS" = "0" ]; then
            # 2>&1 echo "please set CMT_IC_USER to your CIEMAT user name and try again"
            # return "1"
        fi
    fi

    # default data directory
    if [ -z "$CMT_DATA" ]; then
        if [ "$CMT_ON_LXPLUS" = "1" ]; then
            export CMT_DATA="$CMT_BASE/data"
        else
            # TODO: better default when not on lxplus
            export CMT_DATA="$CMT_BASE/data"
        fi
    fi

    # other defaults
    [ -z "$CMT_SOFTWARE" ] && export CMT_SOFTWARE="$CMT_DATA/software"
    [ -z "$CMT_STORE_LOCAL" ] && export CMT_STORE_LOCAL="$CMT_DATA/store"
    if [ -n "$CMT_IC_USER" ]; then
      [ -z "$CMT_STORE_EOS" ] && export CMT_STORE_EOS="/vols/cms/$CMT_IC_USER/cmt"
    elif [ -n "$CMT_CERN_USER" ]; then
      [ -z "$CMT_STORE_EOS" ] && export CMT_STORE_EOS="/eos/user/${CMT_CERN_USER:0:1}/$CMT_CERN_USER/cmt"
    fi
    [ -z "$CMT_STORE" ] && export CMT_STORE="$CMT_STORE_EOS"
    [ -z "$CMT_JOB_DIR" ] && export CMT_JOB_DIR="$CMT_DATA/jobs"
    [ -z "$CMT_TMP_DIR" ] && export CMT_TMP_DIR="$CMT_DATA/tmp"
    [ -z "$CMT_CMSSW_BASE" ] && export CMT_CMSSW_BASE="$CMT_DATA/cmssw"
    [ -z "$CMT_SCRAM_ARCH" ] && export CMT_SCRAM_ARCH="el9_amd64_gcc11"
    [ -z "$CMT_CMSSW_VERSION" ] && export CMT_CMSSW_VERSION="CMSSW_13_0_13"
    [ -z "$CMT_PYTHON_VERSION" ] && export CMT_PYTHON_VERSION="3"

    # specific eos dirs
    [ -z "$CMT_STORE_EOS_PREPROCESSING" ] && export CMT_STORE_EOS_PREPROCESSING="$CMT_STORE_EOS"
    [ -z "$CMT_STORE_EOS_CATEGORIZATION" ] && export CMT_STORE_EOS_CATEGORIZATION="$CMT_STORE_EOS"
    [ -z "$CMT_STORE_EOS_MERGECATEGORIZATION" ] && export CMT_STORE_EOS_MERGECATEGORIZATION="$CMT_STORE_EOS"
    [ -z "$CMT_STORE_EOS_SHARDS" ] && export CMT_STORE_EOS_SHARDS="$CMT_STORE_EOS"
    [ -z "$CMT_STORE_EOS_EVALUATION" ] && export CMT_STORE_EOS_EVALUATION="$CMT_STORE_EOS"
    if [ -n "$CMT_IC_USER" ]; then
       if [ -n "$CMT_TMPDIR" ]; then
         export TMPDIR="$CMT_TMPDIR"
       else
         export TMPDIR="${CMT_STORE_EOS}/tmp"
       fi
       mkdir -p "$TMPDIR"
    fi

    if [[ $CMT_IC_USER == jleonhol ]]; then
        echo "running export CMT_STORE_EOS_CATEGORIZATION=/vols/cms/khl216/cmt..."
        export CMT_STORE_EOS_CATEGORIZATION=/vols/cms/khl216/cmt
    fi

    # create some dirs already
    mkdir -p "$CMT_TMP_DIR"


    #
    # helper functions
    #

    cmt_pip_install() {
        if [ "$CMT_PYTHON_VERSION" = "2" ]; then
            env pip install --ignore-installed --no-cache-dir --upgrade --prefix "$CMT_SOFTWARE" "$@"
        else
            env pip3 install --ignore-installed --no-cache-dir --upgrade --prefix "$CMT_SOFTWARE" "$@"
        fi
    }
    export -f cmt_pip_install

    cmt_add_py() {
        export PYTHONPATH="$1:$PYTHONPATH"
    }
    export -f cmt_add_py

    cmt_add_bin() {
        export PATH="$1:$PATH"
    }
    export -f cmt_add_bin

    cmt_add_lib() {
        export LD_LIBRARY_PATH="$1:$LD_LIBRARY_PATH"
    }
    export -f cmt_add_lib

    cmt_add_root_inc() {
        export ROOT_INCLUDE_PATH="$ROOT_INCLUDE_PATH:$1"
    }
    export -f cmt_add_root_inc



    #
    # minimal software stack
    #

    # add this repo to PATH and PYTHONPATH
    cmt_add_bin "$CMT_BASE/bin"
    cmt_add_py "$CMT_BASE"
    cmt_add_py "$CMT_BASE/../"

    # variables for external software
    export GLOBUS_THREAD_MODEL="none"
    export CMT_GFAL_DIR="$CMT_SOFTWARE/gfal2"
    export GFAL_PLUGIN_DIR="$CMT_GFAL_DIR/lib/gfal2-plugins"

    # certificate proxy handling
    [ "$CMT_REMOTE_JOB" != "1" ] && export X509_USER_PROXY="$CMT_BASE/x509up"

    # software that is used in this project
    cmt_setup_software() {
        local origin="$( pwd )"
        local mode="$1"

        # remove software directories when forced
        if [ "$mode" = "force" ] || [ "$mode" = "force_cmssw" ]; then
            echo "remove CMSSW checkout in $CMT_CMSSW_BASE/$CMT_CMSSW_VERSION"
            rm -rf "$CMT_CMSSW_BASE/$CMT_CMSSW_VERSION"
        fi

        if [ "$mode" = "force" ] || [ "$mode" = "force_py" ]; then
            echo "remove software stack in $CMT_SOFTWARE"
            rm -rf "$CMT_SOFTWARE"
        fi

        if [ "$mode" = "force" ] || [ "$mode" = "force_gfal" ]; then
            echo "remove gfal installation in $CMT_GFAL_DIR"
            rm -rf "$CMT_GFAL_DIR"
        fi

        # setup cmssw
        export SCRAM_ARCH="$CMT_SCRAM_ARCH"
        source "/cvmfs/cms.cern.ch/cmsset_default.sh" ""
        if [ ! -d "$CMT_CMSSW_BASE/$CMT_CMSSW_VERSION" ]; then
            echo "setting up $CMT_CMSSW_VERSION at $CMT_CMSSW_BASE"
            mkdir -p "$CMT_CMSSW_BASE"
            cd "$CMT_CMSSW_BASE"
            scramv1 project CMSSW "$CMT_CMSSW_VERSION"
        fi
        cd "$CMT_CMSSW_BASE/$CMT_CMSSW_VERSION/src"
        
        eval `scramv1 runtime -sh`

        compile="0"
        export NANOTOOLS_PATH="PhysicsTools/NanoAODTools"
        if [ ! -d "$NANOTOOLS_PATH" ]; then
          git clone https://github.com/cms-nanoAOD/nanoAOD-tools.git PhysicsTools/NanoAODTools
          compile="1"
        fi

        export BASEMODULES_PATH="Base/Modules"
        if [ ! -d "$BASEMODULES_PATH" ]; then
          git clone https://gitlab.cern.ch/cms-phys-ciemat/cmt-base-modules.git Base/Modules
          compile="1"
        fi

        export BASEFILTERS_PATH="Base/Filters"
        if [ ! -d "$BASEFILTERS_PATH" ]; then
          git clone https://gitlab.cern.ch/cms-phys-ciemat/event-filters.git Base/Filters
          compile="1"
        fi

        export DQCD_PATH="DQCD/Modules"
        if [ ! -d "$DQCD_PATH" ]; then
          git clone https://github.com/ic-dqcd/dqcd-modules.git DQCD/Modules
          compile="1"
        fi

        export CORRECTIONS_PATH="Corrections"
        cmt_add_root_inc $(correction config --incdir)
        if [ ! -d "$CORRECTIONS_PATH" ]; then
           git clone https://gitlab.cern.ch/cms-phys-ciemat/jme-corrections.git Corrections/JME
           cd Corrections/JME/data
           wget https://github.com/cms-jet/JECDatabase/raw/master/tarballs/Summer19UL18_V5_MC.tar.gz
           wget https://github.com/cms-jet/JECDatabase/raw/master/tarballs/Summer19UL17_V5_MC.tar.gz
           wget https://github.com/cms-jet/JECDatabase/raw/master/tarballs/Summer19UL16_V7_MC.tar.gz
           wget https://github.com/cms-jet/JECDatabase/raw/master/tarballs/Summer19UL16APV_V7_MC.tar.gz
           cd -

          git clone https://gitlab.cern.ch/cms-phys-ciemat/lum-corrections.git Corrections/LUM
          # git clone https://gitlab.cern.ch/cms-phys-ciemat/muo-corrections.git Corrections/MUO
          # git clone https://gitlab.cern.ch/cms-phys-ciemat/egm-corrections.git Corrections/EGM
          # git clone https://gitlab.cern.ch/cms-phys-ciemat/btv-corrections.git Corrections/BTV
          compile="1"
        fi

        export COMBINE_PATH="HiggsAnalysis/CombinedLimit"
        if [ ! -d "$COMBINE_PATH" ]; then
          git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git -b v9.1.0 HiggsAnalysis/CombinedLimit
          compile="1"
        fi

        export COMBINEHARVESTER_PATH="CombineHarvester"
        if [ ! -d "$COMBINEHARVESTER_PATH" ]; then
          git clone https://github.com/cms-analysis/CombineHarvester -b v2.1.0
          cd CombineHarvester
          rm -r CombinePdfs
          rm CombineTools/bin/*
          rm CombineTools/src/*
          rm CombineTools/interface/*
          rm CombineTools/macros/*
          cd -
          compile="1"
        fi

        if [ "$compile" == "1" ]
        then
            scram b
        fi

        #export COMBINE_PATH="HiggsAnalysis/CombinedLimit"
        #if [ ! -d "$COMBINE_PATH" ]; then
        #    git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git $COMBINE_PATH
        #    cd $COMBINE_PATH
        #    git checkout v8.0.1
        #    cd -
        #    scram b -j5
        #fi
        eval `scramv1 runtime -sh`
        cd "$origin"

        # get the python version
        if [ "$CMT_PYTHON_VERSION" = "2" ]; then
            local pyv="$( python -c "import sys; print('{0.major}.{0.minor}'.format(sys.version_info))" )"
        else
            local pyv="$( python3 -c "import sys; print('{0.major}.{0.minor}'.format(sys.version_info))" )"
        fi

        # ammend software paths
        cmt_add_bin "$CMT_SOFTWARE/bin"
        cmt_add_py "$CMT_SOFTWARE/lib/python$pyv/site-packages:$CMT_SOFTWARE/lib64/python$pyv/site-packages"

        # setup custom software
        if [ ! -d "$CMT_SOFTWARE" ]; then
            echo "installing software stack at $CMT_SOFTWARE"
            mkdir -p "$CMT_SOFTWARE"

            cmt_pip_install pip
            cmt_pip_install flake8
            cmt_pip_install luigi==2.8.13
            cmt_pip_install tabulate
            cmt_pip_install git+https://gitlab.cern.ch/cms-phys-ciemat/analysis_tools.git
            cmt_pip_install git+https://gitlab.cern.ch/cms-phys-ciemat/plotting_tools.git
            cmt_pip_install --no-deps git+https://github.com/riga/law
            cmt_pip_install --no-deps git+https://github.com/riga/plotlib
            cmt_pip_install --no-deps git+https://github.com/riga/LBN
            cmt_pip_install --no-deps gast==0.5.3  # https://github.com/tensorflow/autograph/issues/1
            cmt_pip_install sphinx==5.2.2
            cmt_pip_install sphinx_rtd_theme
            cmt_pip_install sphinx_design
            cmt_pip_install envyaml
            cmt_pip_install matplotlib==3.4.3
        fi

        # gfal python bindings
        cmt_add_bin "$CMT_GFAL_DIR/bin"
        cmt_add_py "$CMT_GFAL_DIR/lib/python3/site-packages"
        cmt_add_lib "$CMT_GFAL_DIR/lib"

        if [ ! -d "$CMT_GFAL_DIR" ]; then
            local lcg_base="/cvmfs/grid.cern.ch/centos7-ui-4.0.3-1_umd4v3/usr"
            if [ ! -d "$lcg_base" ]; then
                2>&1 echo "LCG software directory $lcg_base not existing"
                return "1"
            fi

            mkdir -p "$CMT_GFAL_DIR"
            (
                cd "$CMT_GFAL_DIR"
                mkdir -p include bin lib/gfal2-plugins lib/python3/site-packages
                ln -s "$lcg_base"/include/gfal2* include
                ln -s "$lcg_base"/bin/gfal-* bin
                ln -s "$lcg_base"/lib64/libgfal* lib
                ln -s "$lcg_base"/lib64/gfal2-plugins/libgfal* lib/gfal2-plugins
                ln -s "$lcg_base"/lib64/python3/site-packages/gfal* lib/python3/site-packages
                cd lib/gfal2-plugins
                rm libgfal_plugin_http.so libgfal_plugin_xrootd.so
                curl https://cernbox.cern.ch/index.php/s/qgrogVY4bwcuCXt/download > libgfal_plugin_xrootd.so
            )
        fi
    }
    export -f cmt_setup_software

    # setup the software initially when no explicitly skipped
    if [ "$CMT_SKIP_SOFTWARE" != "1" ]; then
        if [ "$CMT_FORCE_SOFTWARE" = "1" ]; then
            cmt_setup_software force
        else
            if [ "$CMT_FORCE_CMSSW" = "1" ]; then
                cmt_setup_software force_cmssw
            else
                cmt_setup_software silent
            fi
        fi
    fi


    #
    # law setup
    #

    export LAW_HOME="$CMT_DATA/law"
    export LAW_CONFIG_FILE="$CMT_BASE/../law.cfg"
    [ -z "$CMT_SCHEDULER_PORT" ] && export CMT_SCHEDULER_PORT="80"
    if [ -z "$CMT_LOCAL_SCHEDULER" ]; then
        if [ -z "$CMT_SCHEDULER_HOST" ]; then
            export CMT_LOCAL_SCHEDULER="True"
        else
            export CMT_LOCAL_SCHEDULER="False"
        fi
    fi
    if [ -z "$CMT_LUIGI_WORKER_KEEP_ALIVE" ]; then
        if [ "$CMT_REMOTE_JOB" = "0" ]; then
            export CMT_LUIGI_WORKER_KEEP_ALIVE="False"
        else
            export CMT_LUIGI_WORKER_KEEP_ALIVE="False"
        fi
    fi

    # try to source the law completion script when available
    which law &> /dev/null && source "$( law completion )" ""
}
action "$@"
cd ..
#voms-proxy-init --voms cms -valid 192:0
