#!/bin/sh
eval "$(conda shell.bash hook)"

PROJECT_ROOT=$(cd $(dirname $0); cd ../; pwd -P)
echo "Project root path: $PROJECT_ROOT"
conda activate replay-env

# ========== CONFIGURATION ==========
bug_dataset=$1  # e.g., defects4j, bugsinpy
model_id=$2  # e.g., codellama:7b-instruct-fp16, deepseek-coder:6.7b-instruct-fp16, deepseek-coder-v2:16b-lite-instruct-fp16
style=$3  # e.g., Instruction, InstructionLabel, InstructionMask
api_port=$4  # e.g., codellama on bugsinpy 11430, 11431 and 11432 for 3 prompt styles. 11434, 11435 for deepseek-coder and v2
num_return_sequences=${5:-10}  # optional, default 10. use 60 to add when compare with hafix
history_category_flags=${6:-"1 2 3 4 5 6 7 8"}  # optional, default all

# Input validation
if [ $# -lt 4 ]; then
  echo "Usage: $0 <bug_dataset> <model_id> <style> <api_port> [num_return_sequences] [history_category_flags]"
  exit 1
fi

# ===================================

model_name=$(echo "$model_id" | tr ':-' '_')
model_serving_api=http://localhost:$api_port/api/generate

mkdir -p log/$bug_dataset/${model_name}_${style}
timestamp=$(date +"%Y%m%d_%H%M%S")

for history_category_flag in $history_category_flags; do
  echo "-------------------- Start history_category_flag: $history_category_flag ---------------------"
  python -u ollama_model_generate.py \
      --dataset $bug_dataset \
      --prompt_style $style \
      --subject_model_id $model_id \
      --model_serving_api $model_serving_api \
      --history_category $history_category_flag \
      --bugs_meta_data_file $PROJECT_ROOT/dataset/$bug_dataset/${bug_dataset}_bugs_meta_data.json \
      --bugs_description_file $PROJECT_ROOT/dataset/$bug_dataset/${bug_dataset}_bugs_description_clean.json \
      --history_data_path $PROJECT_ROOT/dataset/$bug_dataset/history_blame \
      --result_output_path $PROJECT_ROOT/model_inference/$bug_dataset \
      --num_return_sequences $num_return_sequences \
      > log/$bug_dataset/${model_name}_${style}/${model_name}_${bug_dataset}_${style}_${history_category_flag}_${timestamp}.log
  echo "-------------------- Done history_category_flag: $history_category_flag ---------------------"
done

conda deactivate
