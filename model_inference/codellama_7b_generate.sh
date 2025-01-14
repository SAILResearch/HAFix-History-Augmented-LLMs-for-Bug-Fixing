#!/bin/sh
eval "$(conda shell.bash hook)"

PROJECT_ROOT=$(cd $(dirname $0); cd ../; pwd -P)
echo "Project root path: $PROJECT_ROOT"

conda activate replay-env


# shellcheck disable=SC2112
#          --prompt_style infill \
function codellama_generate() {
#    history_category_flag=1
    history_category_flag=2
    style=instruct
    #      CUDA_VISIBLE_DEVICES=$device_id \
#    for device_id in 0 1 2 3 4 5 6 7; do
    for device_id in 0 1 2 3 4 5 6; do
      CUDA_VISIBLE_DEVICES=$device_id nohup \
      python -u codellama_generate.py \
          --prompt_style $style \
          --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
          --history_category $history_category_flag \
          --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
          --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
          --history_data_path $PROJECT_ROOT/dataset/history_blame \
          --result_output_path $PROJECT_ROOT/model_inference \
          --has_nucleus_sampling 1 \
          --is_buggy_line_labeled 0 > log/instruct_2nd_run/codellama_7b_${style}_${history_category_flag}.log &
      echo "--------------------history_category_flag: $history_category_flag---------------------"
      ((history_category_flag++))
    done
}

codellama_generate
conda deactivate
