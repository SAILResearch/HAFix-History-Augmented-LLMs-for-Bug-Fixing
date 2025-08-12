#!/bin/sh

# 3 models on 3 prompt styles
#CODELLAMA_DEEPSEEK_CODER_INSTRUCTION_LABEL_MASK="codellama_7b_instruct_fp16_Instruction,codellama_7b_instruct_fp16_InstructionLabel,codellama_7b_instruct_fp16_InstructionMask,deepseek_coder_6.7b_instruct_fp16_Instruction,deepseek_coder_6.7b_instruct_fp16_InstructionLabel,deepseek_coder_6.7b_instruct_fp16_InstructionMask,deepseek_coder_v2_16b_lite_instruct_fp16_Instruction,deepseek_coder_v2_16b_lite_instruct_fp16_InstructionLabel,deepseek_coder_v2_16b_lite_instruct_fp16_InstructionMask"
CODELLAMA_DEEPSEEK_CODER_INSTRUCTION="codellama_7b_instruct_fp16_Instruction,deepseek_coder_6.7b_instruct_fp16_Instruction,deepseek_coder_v2_16b_lite_instruct_fp16_Instruction"

##============================================== all ==============================================
python3 -u inference_token_calculate.py \
    --datasets bugsinpy,defects4j \
    --model_inference_dirs "$CODELLAMA_DEEPSEEK_CODER_INSTRUCTION"

python3 -u inference_time_calculate.py \
    --datasets bugsinpy,defects4j \
    --model_inference_dirs "$CODELLAMA_DEEPSEEK_CODER_INSTRUCTION"


