#!/bin/sh
eval "$(conda shell.bash hook)"

PROJECT_ROOT=$(cd $(dirname $0); cd ../; pwd -P)
echo "Project root path: $PROJECT_ROOT"

conda activate replay-env

CUDA_VISIBLE_DEVICES=2 python -u cost_calculate.py

conda deactivate