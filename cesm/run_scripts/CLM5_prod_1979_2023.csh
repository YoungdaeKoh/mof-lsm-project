#!/bin/tcsh -f
#
# CLM5-BGC offline production run, 1979-2023, WFDE5 forcing.
#
# The counterpart to LM4+'s lm4p_ctl_1979-2024: same period, same forcing data,
# so that the two models can be compared without the forcing being a free
# variable.  LM4+ stopped at 2023 because LUH2 land-use transitions end there;
# this run uses the same end year for the same reason.
#
# Start it only after post-AD has finished and been judged:
#   ssh climate "cd ~/CESM/cases/clm5_bgc_pad; \
#                nohup bash clm5_bgc_pad_chain.sh 100 >& ~/clm5_bgc_pad_chain.out &"
#   python cesm/scripts/clm5_postad_convergence.py 20
# then set FINIDAT below to post-AD's final restart.
#
# This script only creates and builds the case.  It deliberately does not run it:
# a 45-year integration is driven in chunks from outside, because BATCH_SYSTEM is
# none here and CESM cannot resubmit itself.  Use clm5_prod_chain.sh for that.

set CCSMROOT = /home/ydkoh/CESM
set CNAME    = clm5_prod_1979_2023
set COMPSET  = 2000_DATM%GSWP3v1_CLM50%BGC_SICE_SOCN_MOSART_CISM2%NOEVOLVE_SWAV
set RES      = f09_g17
set NPE      = 48
set HOSTNODE = climate01

# post-AD's last restart.  Set this after post-AD finishes; the placeholder is
# year 0093, where it stands as of 2026-09-08.
set FINIDAT  = /data2/ydkoh/cesm2_output/clm5_bgc_pad/run/clm5_bgc_pad.clm2.r.0093-01-01-00000.nc

# ---------------------------------------------------------------- guards ----
if ( ! -f $FINIDAT ) then
  echo "ABORT: FINIDAT not found: $FINIDAT"
  exit 1
endif
if ( -d $CCSMROOT/cases/$CNAME ) then
  echo "ABORT: case already exists: $CCSMROOT/cases/$CNAME"
  echo "  remove it deliberately if you mean to rebuild -- it is not deleted"
  echo "  automatically, unlike the spin-up scripts, because this one carries"
  echo "  45 years of output."
  exit 1
endif

setenv PERL5LIB /home/ydkoh/perl5/lib/perl5

# ------------------------------------------------------------ create ---------
cd $CCSMROOT/cime/scripts

./create_newcase --case $CCSMROOT/cases/$CNAME \
                 --compset $COMPSET \
                 --res $RES \
                 --machine climate00 \
                 --compiler intel \
                 --mpilib mvapich2 \
                 --run-unsupported

cd $CCSMROOT/cases/$CNAME

# ------------------------------------------------------------ PE layout ------
# 48 ranks on one node, every component on the same PEs.  climate01 and
# climate02 have 48 cores each and two-node jobs are not available here, so 48
# is the ceiling.  Measured 1.79 h/model-year in post-AD at this layout.
./xmlchange NTASKS=$NPE,NTHRDS=1,ROOTPE=0
./xmlchange MAX_TASKS_PER_NODE=$NPE,MAX_MPITASKS_PER_NODE=$NPE

./case.setup

# ------------------------------------------------------------ run config -----
# Normal turnover, not accelerated: the AD phase is over.
./xmlchange CLM_ACCELERATED_SPINUP=off
./xmlchange CLM_FORCE_COLDSTART=off

# Transient period.  RUN_STARTDATE is the real calendar date, unlike the spin-up
# cases which counted from year 0001.
./xmlchange RUN_TYPE=startup
./xmlchange RUN_STARTDATE=1979-01-01
./xmlchange CONTINUE_RUN=FALSE
./xmlchange STOP_OPTION=nyears,STOP_N=5
./xmlchange REST_OPTION=nyears,REST_N=1
./xmlchange RESUBMIT=0,DOUT_S=FALSE

./xmlchange DATM_CLMNCEP_YR_START=1979
./xmlchange DATM_CLMNCEP_YR_END=2023
./xmlchange DATM_CLMNCEP_YR_ALIGN=1979

# ------------------------------------------------------------ namelists ------
# finidat has to be stated.  With CONTINUE_RUN=FALSE, CLM reads it, and the
# built-in default for this compset is a 1.9x2.5 BgcCrop file -- wrong grid and
# wrong configuration.  See CLM5_SPINUP_NOTES 7g.
cat >> user_nl_clm << EOF

! start from the post-AD spin-up, not from the built-in default
finidat = '$FINIDAT'

! monthly history, one file per month
hist_nhtfrq = 0
hist_mfilt  = 1
EOF

# WFDE5 forcing, the same files LM4+ was driven with.  Copied from the post-AD
# case rather than rewritten, so the two cases cannot drift apart.
foreach s (Precip Solar TPQW)
  cp $CCSMROOT/cases/clm5_bgc_pad/user_datm.streams.txt.CLMGSWP3v1.$s .
end
cp $CCSMROOT/cases/clm5_bgc_pad/user_nl_datm .

./preview_namelists

# ------------------------------------------------------------ checks ---------
echo ""
echo "=== namelist check ==="
grep -E "^ *(finidat|spinup_state|use_cn|use_crop)" \
     /data2/ydkoh/cesm2_output/$CNAME/run/lnd_in
echo ""
echo "=== PE layout ==="
./pelayout

# ------------------------------------------------------------ build ----------
./case.build

echo ""
echo "built.  To run, drive it in chunks from outside:"
echo "  cd $CCSMROOT/cases/$CNAME"
echo "  nohup bash clm5_prod_chain.sh 2023 >& ~/clm5_prod_chain.out &"
