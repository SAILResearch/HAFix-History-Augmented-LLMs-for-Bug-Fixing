#!/bin/sh
eval "$(conda shell.bash hook)"

PROJECT_ROOT=$(cd $(dirname $0); cd ../; pwd -P)
echo "Project root path: $PROJECT_ROOT"

conda activate replay-env

# update the runtime for the following cases
# '31', '32', '33', '35', '36', '37', '38', '41', '42', '43'

# shellcheck disable=SC2112
#function codellama_generate() {
#    history_category_flag=8
#    style=instruct
#    CUDA_VISIBLE_DEVICES=0 nohup \
#    python -u codellama_generate_manual.py \
#        --bug_id_list '31' '32' '33' '35' '36' '37' '38' '41' '42' '43' \
#        --prompt_style $style \
#        --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
#        --history_category $history_category_flag \
#        --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
#        --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
#        --history_data_path $PROJECT_ROOT/dataset/history_blame \
#        --result_output_path $PROJECT_ROOT/model_inference \
#        --has_nucleus_sampling 1 \
#        --is_buggy_line_labeled 0 > log/old_prompt/setting_8/codellama_7b_${style}_${history_category_flag}_0_refine_runtime.log &
#    echo "--------------------history_category_flag: $history_category_flag---------------------"
#


function codellama_generate() {
    history_category_flag=8
    style=instruct
    CUDA_VISIBLE_DEVICES=0 nohup \
    python -u codellama_generate_manual.py \
        --bug_id_list '44' '45' '46' \
        --prompt_style $style \
        --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
        --history_category $history_category_flag \
        --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
        --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
        --history_data_path $PROJECT_ROOT/dataset/history_blame \
        --result_output_path $PROJECT_ROOT/model_inference_manual_0 \
        --has_nucleus_sampling 1 \
        --is_buggy_line_labeled 0 > log/instruct_2nd_run/codellama_7b_${style}_${history_category_flag}_0.log &
    echo "--------------------history_category_flag: $history_category_flag---------------------"

    CUDA_VISIBLE_DEVICES=1 nohup \
    python -u codellama_generate_manual.py \
        --bug_id_list '47' '48' '49' \
        --prompt_style $style \
        --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
        --history_category $history_category_flag \
        --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
        --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
        --history_data_path $PROJECT_ROOT/dataset/history_blame \
        --result_output_path $PROJECT_ROOT/model_inference_manual_1 \
        --has_nucleus_sampling 1 \
        --is_buggy_line_labeled 0 > log/instruct_2nd_run/codellama_7b_${style}_${history_category_flag}_1.log &
    echo "--------------------history_category_flag: $history_category_flag---------------------"

    CUDA_VISIBLE_DEVICES=2 nohup \
    python -u codellama_generate_manual.py \
        --bug_id_list '50' '51' '52' \
        --prompt_style $style \
        --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
        --history_category $history_category_flag \
        --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
        --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
        --history_data_path $PROJECT_ROOT/dataset/history_blame \
        --result_output_path $PROJECT_ROOT/model_inference_manual_2 \
        --has_nucleus_sampling 1 \
        --is_buggy_line_labeled 0 > log/instruct_2nd_run/codellama_7b_${style}_${history_category_flag}_2.log &
    echo "--------------------history_category_flag: $history_category_flag---------------------"

    CUDA_VISIBLE_DEVICES=3 nohup \
    python -u codellama_generate_manual.py \
        --bug_id_list '53' '54' '60' \
        --prompt_style $style \
        --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
        --history_category $history_category_flag \
        --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
        --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
        --history_data_path $PROJECT_ROOT/dataset/history_blame \
        --result_output_path $PROJECT_ROOT/model_inference_manual_3 \
        --has_nucleus_sampling 1 \
        --is_buggy_line_labeled 0 > log/instruct_2nd_run/codellama_7b_${style}_${history_category_flag}_3.log &
    echo "--------------------history_category_flag: $history_category_flag---------------------"

    CUDA_VISIBLE_DEVICES=4 nohup \
    python -u codellama_generate_manual.py \
        --bug_id_list '61' '66' '67' '68' \
        --prompt_style $style \
        --subject_model_id codellama/CodeLlama-7b-Instruct-hf \
        --history_category $history_category_flag \
        --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
        --bugs_description_file $PROJECT_ROOT/dataset/github_issue/bugs_description.json \
        --history_data_path $PROJECT_ROOT/dataset/history_blame \
        --result_output_path $PROJECT_ROOT/model_inference_manual_4 \
        --has_nucleus_sampling 1 \
        --is_buggy_line_labeled 0 > log/instruct_2nd_run/codellama_7b_${style}_${history_category_flag}_4.log &
    echo "--------------------history_category_flag: $history_category_flag---------------------"
}

codellama_generate
conda deactivate
