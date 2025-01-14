#!/bin/sh

#python3 evaluate.py --model_names "codellama_34b_instruct_hf,codellama_34b_python_hf,codellama_70b_instruct_hf,codellama_70b_python_hf" \
#    --history_settings "01,11,3,4,5,6,31,41,51,61" \
#    --has_nucleus_sampling 0 \

#python3 evaluate.py --model_names "codellama_34b_instruct_hf" \
#    --history_settings "1,2,3,4,5,6,7,8" \
#    --has_nucleus_sampling 0 \

#python3 evaluate.py --model_names "codellama_7b_instruct_hf,codellama_13b_instruct_hf" \
#python3 evaluate.py --model_inference_dirs "codellama_7b_instruct_hf_instruct" \
#    --history_settings "1,2,3,4,5,6,7,8" \
#    --has_nucleus_sampling 1 \

#python3 evaluate.py --model_inference_dirs "codellama_7b_instruct_hf_instruct" \
#    --history_settings "2,3,4,5,6,7,8" \
#    --has_nucleus_sampling 1 \

#python3 evaluate.py --model_inference_dirs "codellama_7b_instruct_hf_instruct" \
#    --history_settings "36,362,3625,36258,362587,36257" \
#    --has_nucleus_sampling 1 \

#python3 evaluate.py --model_inference_dirs "codellama_7b_instruct_hf_instruct_0,codellama_7b_instruct_hf_instruct_1,codellama_7b_instruct_hf_instruct_2,codellama_7b_instruct_hf_instruct_3,codellama_7b_instruct_hf_instruct_4,codellama_7b_instruct_hf_instruct_5,codellama_7b_instruct_hf_instruct_6" \
#    --history_settings "6" \
#    --has_nucleus_sampling 1 \

python3 evaluate.py --model_inference_dirs "codellama_7b_instruct_hf_infill_1_0,codellama_7b_instruct_hf_infill_1_1,codellama_7b_instruct_hf_infill_1_2,codellama_7b_instruct_hf_infill_1_3,codellama_7b_instruct_hf_infill_1_4,codellama_7b_instruct_hf_infill_1_5,codellama_7b_instruct_hf_infill_1_6,codellama_7b_instruct_hf_infill_6_0,codellama_7b_instruct_hf_infill_6_1,codellama_7b_instruct_hf_infill_6_2,codellama_7b_instruct_hf_infill_6_3,codellama_7b_instruct_hf_infill_6_4,codellama_7b_instruct_hf_infill_6_5,codellama_7b_instruct_hf_infill_6_6,codellama_7b_instruct_hf_label_1_0,codellama_7b_instruct_hf_label_1_1,codellama_7b_instruct_hf_label_1_2,codellama_7b_instruct_hf_label_1_3,codellama_7b_instruct_hf_label_1_4,codellama_7b_instruct_hf_label_1_5,codellama_7b_instruct_hf_label_1_6,codellama_7b_instruct_hf_label_6_0,codellama_7b_instruct_hf_label_6_1,codellama_7b_instruct_hf_label_6_2,codellama_7b_instruct_hf_label_6_3,codellama_7b_instruct_hf_label_6_4,codellama_7b_instruct_hf_label_6_5,codellama_7b_instruct_hf_label_6_6" \
    --history_settings "1,6" \
    --has_nucleus_sampling 1 \
