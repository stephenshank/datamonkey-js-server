#!/bin/bash
#PBS -l nodes=1:ppn=32

export PATH=/usr/local/bin:$PATH
source /etc/profile.d/modules.sh

module load openmpi/gnu/1.6.3
module load gcc/6.1.0

FN=$fn
CWD=$cwd
TREE_FN=$tree_fn
STATUS_FILE=$sfn
PROGRESS_FILE=$pfn
RESULTS_FN=$rfn
GENETIC_CODE=$genetic_code
RATE_VARIATION=1

HYPHY=$CWD/../../.hyphy-2.3.1-alpha/HYPHYMP
HYPHY_PATH=$CWD/../../.hyphy-2.3.1-alpha/res/
FEL=$HYPHY_PATH/TemplateBatchFiles/SelectionAnalyses/FEL.bf

export HYPHY_PATH=$HYPHY_PATH

trap 'echo "Error" > $STATUS_FILE; exit 1' ERR

echo '(echo '$GENETIC_CODE'; echo '$FN'; echo '$TREE_FN'; echo 4; echo '$RATE_VARIATION'; echo '0.1';) | '$HYPHY' LIBPATH='$HYPHY_PATH' ' $FEL''
(echo $GENETIC_CODE; echo $FN; echo $TREE_FN; echo "4"; echo $RATE_VARIATION; echo "0.1";) | $HYPHY LIBPATH=$HYPHY_PATH $FEL > $PROGRESS_FILE
echo "Completed" > $STATUS_FILE
