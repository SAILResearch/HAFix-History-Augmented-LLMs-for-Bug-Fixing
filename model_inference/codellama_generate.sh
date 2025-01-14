#!/bin/sh
eval "$(conda shell.bash hook)"

PROJECT_ROOT=/home/22ys22/project/fm-apr-replay

conda activate replay

# history_category: {0: baseline 1: function-level history 2: file-level history}


# ===================CodeLlama-34b-Instruct==========================
# --------------------------0.Baseline-------------------------------
CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7 python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-34b-Instruct-hf \
    --history_category 0 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ----------------------1.Function-history---------------------------
CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7 python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-34b-Instruct-hf \
    --history_category 1 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ------------------------2.File-history-----------------------------
CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7 python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-34b-Instruct-hf \
    --history_category 2 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \


# ===================CodeLlama-34b-Python==========================
# --------------------------0.Baseline-------------------------------
CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7 python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-34b-Python-hf \
    --history_category 0 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ----------------------1.Function-history---------------------------
CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7 python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-34b-Python-hf \
    --history_category 1 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ------------------------2.File-history-----------------------------
CUDA_VISIBLE_DEVICES=1,2,3,4,5,6,7 python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-34b-Python-hf \
    --history_category 2 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \



# ===================CodeLlama-70b-Instruct==========================
# --------------------------0.Baseline-------------------------------
python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-70b-Instruct-hf \
    --history_category 0 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ----------------------1.Function-history---------------------------
python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-70b-Instruct-hf \
    --history_category 1 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ------------------------2.File-history-----------------------------
python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-70b-Instruct-hf \
    --history_category 2 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \


# ===================CodeLlama-70b-Python==========================
# --------------------------0.Baseline-------------------------------
python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-70b-Python-hf \
    --history_category 0 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ----------------------1.Function-history---------------------------
python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-70b-Python-hf \
    --history_category 1 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \

# ------------------------2.File-history-----------------------------
python codellama_generate.py \
    --subject_model_id codellama/CodeLlama-70b-Python-hf \
    --history_category 2 \
    --bugs_meta_data_file $PROJECT_ROOT/dataset/bugs_meta_data.json \
    --history_data_path $PROJECT_ROOT/dataset/history \
    --result_output_path $PROJECT_ROOT/model_inference \



