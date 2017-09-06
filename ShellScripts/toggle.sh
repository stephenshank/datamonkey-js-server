DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &&  pwd )"
. $DIR/Globals.sh

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/

rm -f $ABS_DIR/Analyses/Toggle/spool/$1*progress
rm -f $ABS_DIR/Analyses/Toggle/spool/$1*out

# Beowulf MPI
#(echo $1; echo $2; echo $3; echo $4;) | mpirun -np 41 -exclude $EXCLUDE_NODES /usr/local/bin/HYPHYMPI  USEPATH=/dev/null USEPATH=$ABS_DIR/Analyses/Toggle/ $ABS_DIR/Analyses/Toggle/FELtoggle.bf > $ABS_DIR/Analyses/Toggle/hpout 2>&1 & 

# OpenMPI
(echo $1; echo $2; echo $3; echo $4;) | mpirun -np 41 -hostfile $HOSTFILE /usr/local/bin/HYPHYMPI  USEPATH=/dev/null USEPATH=$ABS_DIR/Analyses/Toggle/ $ABS_DIR/Analyses/Toggle/FELtoggle.bf > $ABS_DIR/Analyses/Toggle/hpout 2>&1 & 