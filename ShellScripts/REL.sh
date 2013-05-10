DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &&  pwd )"
. $DIR/Globals.sh

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/

rm -f $ABS_DIR/Analyses/REL/spool/$1*progress
rm -f $ABS_DIR/Analyses/REL/spool/$1*out

(echo $1; echo $2; echo $3; echo $4; echo $5) | mpirun -np 10 -exclude $EXCLUDE_NODES /usr/local/bin/HYPHYMPI  USEPATH=$ABS_DIR/Analyses/REL/ $ABS_DIR/Analyses/REL/REL.bf  > $ABS_DIR/Analyses/REL/hpout 2>&1 &
