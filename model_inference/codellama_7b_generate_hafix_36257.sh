#!/bin/sh
eval "$(conda shell.bash hook)"

PROJECT_ROOT=$(cd $(dirname $0); cd ../; pwd -P)
echo "Project root path: $PROJECT_ROOT"

conda activate replay-env


# shellcheck disable=SC2112
#          --prompt_style infill \
function codellama_generate() {
    history_category_flag=36257
    style=instruct

    CUDA_VISIBLE_DEVICES=1 nohup \
    python -u codellama_generate.py \
        --prompt_style $style \
        --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
        --history_category $history_category_flag \
        --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
        --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
        --history_data_path $PROJECT_ROOT/dataset/history_blame \
        --result_output_path $PROJECT_ROOT/model_inference_ \
        --has_nucleus_sampling 1 \
        --is_buggy_line_labeled 0 > log/hafix/codellama_7b_${style}_${history_category_flag}_.log &
    echo "--------------------history_category_flag: $history_category_flag---------------------"

}

codellama_generate
conda deactivate
