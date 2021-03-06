#!/bin/bash
#MSUB -l nodes=1:ppn=16
#MSUB -l walltime=5:00:00
#MSUB -l pmem=3000mb
#MSUB -N probsat-dynamic
#MSUB -o /work/ul/ul_student/ul_pwn14/output/probsat_dynamic
#MSUB -M sascha.rechenberger@uni-ulm.de
#MSUB -m bea
#MSUB -q singlenode

CB=$1

module load devel/python/3.5.2

python -O run_experiment.py $WORK/input/n512 \
  --dynamic 100 20000 \
  --probsat $CB \
  --poolsize 16 \
  --database_file $WORK/output/walksat`echo $CB`.dynamic.db \
