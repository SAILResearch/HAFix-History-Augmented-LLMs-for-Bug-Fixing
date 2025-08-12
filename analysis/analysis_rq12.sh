#!/bin/sh
eval "$(conda shell.bash hook)"

PROJECT_ROOT=$(cd $(dirname $0); cd ../; pwd -P)
echo "Project root path: $PROJECT_ROOT"
conda activate replay-env

# 3 models on 3 prompt styles
CODELLAMA_DEEPSEEK_CODER_INSTRUCTION_LABEL_MASK="codellama_7b_instruct_fp16_Instruction,codellama_7b_instruct_fp16_InstructionLabel,codellama_7b_instruct_fp16_InstructionMask,deepseek_coder_6.7b_instruct_fp16_Instruction,deepseek_coder_6.7b_instruct_fp16_InstructionLabel,deepseek_coder_6.7b_instruct_fp16_InstructionMask,deepseek_coder_v2_16b_lite_instruct_fp16_Instruction,deepseek_coder_v2_16b_lite_instruct_fp16_InstructionLabel,deepseek_coder_v2_16b_lite_instruct_fp16_InstructionMask"

python3 -u evaluate_to_csv.py \
    --datasets bugsinpy,defects4j \
    --evaluation_dirs "$CODELLAMA_DEEPSEEK_CODER_INSTRUCTION_LABEL_MASK"

python3 -u create_venn_diagrams.py \
    --datasets bugsinpy,defects4j \
    --evaluation_dirs "$CODELLAMA_DEEPSEEK_CODER_INSTRUCTION_LABEL_MASK"

python3 -u create_line_charts.py \
    --datasets bugsinpy,defects4j \
    --evaluation_dirs "$CODELLAMA_DEEPSEEK_CODER_INSTRUCTION_LABEL_MASK"

# manual check the model-generated correct samples
#python3 -u inspect_model_output.py \
#    --datasets defects4j \
#    --evaluation_dirs codellama_7b_instruct_fp16_Instruction \
#    --history_settings "5"\
#    --bugs_meta_data_file $PROJECT_ROOT/dataset/defects4j/defects4j_bugs_meta_data.json \
