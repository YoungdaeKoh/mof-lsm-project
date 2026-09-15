#!/bin/tcsh -f
#
# F2000climo at f09 -- a timing test, not a science run.
#
# The f19 case measured 4.29 h/model-year on 48 cores.  f09 is twice the
# resolution in each horizontal direction, so four times the columns, and the
# dynamics substeps more finely on top of that; the usual CESM ratio is 3.5-4x,
# which would put two years somewhere around 30-34 h.  The point of this case is
# to replace that guess with a measurement.
#
# Built from F_spinup_cam6clm5.csh.  Three things differ beyond the resolution:
#   - the f09 CAM initial condition and topography are not on /data1, so
#     check_input_data downloads them before the build
#   - mpirun is made to follow the PBS allocation rather than a fixed hostfile
#     (see below -- this is the bug that sent post-AD to the wrong node)
#   - two years, not two years of spin-up: restart yearly and stop
#
# This case is disposable: the script deletes and rebuilds it each time.  Do not
# point CNAME at anything whose output matters.

cd ~/CESM/cime/scripts

set CCSMROOT = /home/ydkoh/CESM
set CNAME = F_2000climo_f09
set COMPSET = F2000climo
set RES = f09_f09_mg17

# f19_f19 puts ocn/ice on the atmosphere grid; f09_f09_mg17 is the f09
# counterpart.  There is no bare "f09_f09" alias -- the mask suffix is required.

if ( "$CNAME" !~ *_f09 ) then
  echo "ABORT: CNAME must end in _f09; refusing to delete $CNAME"
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

# --- PE layout: one 48-core node ---------------------------------------------
./xmlchange NTASKS=48,NTHRDS=1,ROOTPE=0
./xmlchange MAX_TASKS_PER_NODE=48,MAX_MPITASKS_PER_NODE=48

./case.setup

# --- make mpirun follow the PBS allocation -----------------------------------
# The machine default is a fixed hostfile naming climate01.  Submitting this to
# climate02 while that file still said climate01 would land 48 ranks on
# climate01, on top of the post-AD spin-up -- which is exactly how post-AD ended
# up on the wrong node for three weeks without anything crashing (CLM5 notes 7k).
# So point the case at its own hostfile and let the PBS wrapper write it from
# $PBS_NODEFILE.  Then the allocation and the launch cannot disagree.
sed -i "s|-hostfile /home/ydkoh/mvapich2.hosts|-hostfile $CCSMROOT/cases/$CNAME/mpi.hosts|" \
    env_mach_specific.xml
echo "=== hostfile now: ==="
grep -o "hostfile [^ ]*" env_mach_specific.xml | head -1

# --- run length --------------------------------------------------------------
./xmlchange STOP_N=2,STOP_OPTION=nyears
./xmlchange REST_N=1,REST_OPTION=nyears
./xmlchange CONTINUE_RUN=FALSE

# --- CAM history -------------------------------------------------------------
# npr_y x npr_z must equal NTASKS, and each y-subdomain needs at least three
# latitudes.  f09 has 192, so 24 x 2 leaves 8 apiece -- twice the headroom f19
# had at the same layout.
cat >> user_nl_cam << EOF
 npr_yz = 24,2,2,24
 inithist = 'YEARLY'
 empty_htapes = .true.
 nhtfrq = 0
 mfilt  = 1
 ndens  = 2
 fincl1 = 'TREFHT:A','TS:A','PSL:A','PS:A','PRECT:A','PRECC:A','PRECL:A',
          'LHFLX:A','SHFLX:A','FLNS:A','FSNS:A','U:A','V:A','T:A','Z3:A','OMEGA:A','Q:A'
EOF

# --- CLM history -------------------------------------------------------------
# Same list the f19 case runs, which was checked field by field against CLM5's
# master list.  HTOP and plain BTRAN are not in it -- HTOP is a CLM4 name and
# CLM5 has only BTRAN2/BTRANMN/BTRANAV -- and an unknown name aborts the run in
# htapes_fieldlist rather than being ignored.
cat >> user_nl_clm << EOF
 hist_nhtfrq = 0
 hist_mfilt  = 1
 hist_empty_htapes = .false.
 hist_fincl2 = 'TLAI:A','TSAI:A','FSH:A','EFLX_LH_TOT:A',
               'H2OSOI:A','TSOI:A','SOILLIQ:A','H2OSNO:A','SNOWDP:A','FSNO:A',
               'TSA:A','RH2M:A','QSOIL:A','QVEGT:A','QVEGE:A','BTRAN2:A'
EOF

./preview_namelists

# --- fetch what f09 needs and f19 did not ------------------------------------
# /data1 has the f09 CLM surface dataset but no f09 CAM initial condition and no
# f09 topography, so the namelist points at files that are not there.  The run
# would fail at open, not at build, so pull them now.  The CESM inputdata server
# is reachable from climate00.
echo "=== check_input_data: downloading anything missing ==="
./check_input_data --download

echo "=== still missing after download (should be empty) ==="
./check_input_data | grep -i "missing" | head -20

./case.build

# Do not run it from here.  BATCH_SYSTEM is none, so case.submit executes
# wherever it is called -- from this script that is the login node.
echo ""
echo "built.  submit with:  qsub ~/run_scripts/F_2000climo_f09.pbs"
