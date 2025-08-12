#!/bin/sh

#================ defects4j =======================
# 1. codellama-7b
#python3 pass_at_k.py \
#    --dataset defects4j \
#    --model_inference_dirs "codellama_7b_instruct_fp16_Instruction" \
#    --history_settings "1,2,3,4,5,6,7,8" \
#    --k_list "1,5,10" \

# 2. deepseek-coder
#python3 pass_at_k.py \
#    --dataset defects4j \
#    --model_inference_dirs "deepseek_coder_6.7b_instruct_fp16_Instruction,deepseek_coder_v2_16b_lite_instruct_fp16_Instruction" \
#    --history_settings "1,2,3,4,5,6,7,8" \
#    --k_list "1,5,10" \


##================ bugsinpy =======================
# 1. codellama-7b
#python3 pass_at_k.py \
#    --dataset bugsinpy \
#    --model_inference_dirs "codellama_7b_instruct_fp16_Instruction,codellama_7b_instruct_fp16_InstructionLabel,codellama_7b_instruct_fp16_InstructionMask" \
#    --history_settings "1,2,3,4,5,6,7,8" \
#    --k_list "1,3,5,10" \


##================ all =======================

python3 pass_at_k.py \
    --dataset defects4j \
    --model_inference_dirs "codellama_7b_instruct_fp16_InstructionLabel,codellama_7b_instruct_fp16_InstructionMask,deepseek_coder_6.7b_instruct_fp16_InstructionLabel,deepseek_coder_6.7b_instruct_fp16_InstructionMask,deepseek_coder_v2_16b_lite_instruct_fp16_InstructionLabel,deepseek_coder_v2_16b_lite_instruct_fp16_InstructionMask" \
    --history_settings "1,2,3,4,5,6,7,8" \
    --k_list "1,5,10" \
