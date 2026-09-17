#!/bin/tcsh -f
#
# F2000climo at f09 on 96 cores (climate01 + climate02) -- a timing test.
#
# The same case as F_f09_cam6clm5.csh, which measured 18.6 h/model-year on one
# 48-core node (Model Cost 894 pe-hrs/yr, 1.29 yr/day; timing file
# cesm_timing.F_2000climo_f09.8446).  This one spans both compute nodes to
# find out what a two-node job actually buys here: mvapich2 across nodes has
# never been tried on this machine (CLAUDE.md says "48 is the ceiling" for
# that reason, not because it was measured).
#
# Three things differ from the 48-core script:
#   - NTASKS=96 with 48 per node, so PBS has to hand over two nodes
#     (F_2000climo_f09_96pe.pbs asks for climate01+climate02 explicitly)
#   - CAM's decomposition npr_yz follows the task count: 48 x 2 (see below)
#   - one model year, not two; the per-year cost is what is being measured
#
# Built from scratch rather than cloned, so that the whole configuration is in
# this one file.  This case is disposable: the script deletes and rebuilds it
# each time.  Do not point CNAME at anything whose output matters.

cd ~/CESM/cime/scripts

set CCSMROOT = /home/ydkoh/CESM
set CNAME = F_2000climo_f09_96pe
set COMPSET = F2000climo
set RES = f09_f09_mg17

# f19_f19 puts ocn/ice on the atmosphere grid; f09_f09_mg17 is the f09
# counterpart.  There is no bare "f09_f09" alias -- the mask suffix is required.

if ( "$CNAME" !~ *_96pe ) then
  echo "ABORT: CNAME must end in _96pe; refusing to delete $CNAME"
  exit 1
endif
rm -rf $CCSMROOT/cases/$CNAME
rm -rf /data2/ydkoh/cesm2_output/$CNAME

./create_newcase --case $CCSMROOT/cases/$CNAME \
                 --compset $COMPSET \
                 --res $RES \
                 --machine climate00 \
                 --compiler intel \
                 --mpilib mvapich2 \
                 --run-unsupported

cd $CCSMROOT/cases/$CNAME

# --- PE layout: two 48-core nodes --------------------------------------------
# 96 tasks, 48 per node.  MAX_*_PER_NODE stays 48 so CIME counts two nodes;
# the PBS script requests exactly those two hosts.
./xmlchange NTASKS=96,NTHRDS=1,ROOTPE=0
./xmlchange MAX_TASKS_PER_NODE=48,MAX_MPITASKS_PER_NODE=48

./case.setup

# --- make mpirun follow the PBS allocation -----------------------------------
# The machine default is a fixed hostfile naming climate01 only.  With two
# nodes that would be wrong twice over: 96 ranks would be launched on a single
# node.  Point the case at its own hostfile and let the PBS wrapper write it
# from $PBS_NODEFILE, one "host:48" line per node.  (Same fix as the 48-core
# script; CLM5 notes 7k for the history.)
sed -i "s|-hostfile /home/ydkoh/mvapich2.hosts|-hostfile $CCSMROOT/cases/$CNAME/mpi.hosts|" \
    env_mach_specific.xml
echo "=== hostfile now: ==="
grep -o "hostfile [^ ]*" env_mach_specific.xml | head -1

# --- run length --------------------------------------------------------------
./xmlchange STOP_N=1,STOP_OPTION=nyears
./xmlchange REST_N=1,REST_OPTION=nyears
./xmlchange CONTINUE_RUN=FALSE

# --- CAM history -------------------------------------------------------------
# npr_y x npr_z must equal NTASKS, and each y-subdomain needs at least three
# latitudes.  f09 has 192, so 48 x 2 leaves 4 apiece (the 48-core case used
# 24 x 2 -> 8).  Fewer latitudes per subdomain means more halo exchange per
# unit of work, which is part of what this test is measuring.
cat >> user_nl_cam << EOF
 npr_yz = 48,2,2,48
 inithist = 'YEARLY'
 empty_htapes = .true.
 nhtfrq = 0
 mfilt  = 1
 ndens  = 2
 fincl1 = 'TREFHT:A','TS:A','PSL:A','PS:A','PRECT:A','PRECC:A','PRECL:A',
          'LHFLX:A','SHFLX:A','FLNS:A','FSNS:A','U:A','V:A','T:A','Z3:A','OMEGA:A','Q:A'
EOF

# --- CLM history -------------------------------------------------------------
# Same list the 48-core case runs, checked field by field against CLM5's
# master list (no HTOP, no plain BTRAN -- an unknown name aborts the run).
cat >> user_nl_clm << EOF
 hist_nhtfrq = 0
 hist_mfilt  = 1
 hist_empty_htapes = .false.
 hist_fincl2 = 'TLAI:A','TSAI:A','FSH:A','EFLX_LH_TOT:A',
               'H2OSOI:A','TSOI:A','SOILLIQ:A','H2OSNO:A','SNOWDP:A','FSNO:A',
               'TSA:A','RH2M:A','QSOIL:A','QVEGT:A','QVEGE:A','BTRAN2:A'
EOF

./preview_namelists

# --- input data --------------------------------------------------------------
# The f09 CAM initial condition and topography were downloaded by the 48-core
# case and live in the shared inputdata tree, so this should find nothing
# missing; kept so the script stands on its own.
echo "=== check_input_data: downloading anything missing ==="
./check_input_data --download

echo "=== still missing after download (should be empty) ==="
./check_input_data | grep -i "missing" | head -20

echo "=== PE layout ==="
./pelayout

./case.build

# Do not run it from here.  BATCH_SYSTEM is none, so case.submit executes
# wherever it is called -- from this script that is the login node.
echo ""
echo "built.  submit with:  qsub ~/run_scripts/F_2000climo_f09_96pe.pbs"
echo "  (or let run_F96_then_prod.sh submit it and then start the CLM5 production chain)"
