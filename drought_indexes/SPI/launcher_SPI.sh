#!/bin/bash
#-----------------------------------------------------------------------------------------
# Get file information


working_dir="/home/sequia/drought/code/SPI/"

virtual_env_name="sequia"

script_file='SPI_Index.py'

#-----------------------------------------------------------------------------------------
# Setting parameters

# Run period in month(s)
months=2

# Get information (-u to get gmt time)
time_now=$(date -u +"%Y%m")

#-----------------------------------------------------------------------------------------

#activate virtual env
echo "conda activate $virtual_env_name"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate $virtual_env_name

cd $working_dir

#update statistics
#python SPI_stat_base.py

#compute index for the last "timerange" months
python $script_file --dateend=$time_now --timerange=$months
