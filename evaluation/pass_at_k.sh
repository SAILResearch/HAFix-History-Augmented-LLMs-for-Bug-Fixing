#!/bin/sh

#python3 pass_at_k.py --evaluation_path "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct_labelled" \
#python3 pass_at_k.py --evaluation_path "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_infill" \
#python3 pass_at_k.py --evaluation_path "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct" \
#    --history_settings "1,2,3,4,5,6,7,8" \
#    --has_nucleus_sampling 1 \


python3 pass_at_k_hafix.py --evaluation_path "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct" \
    --history_settings "2,3,4,5,6,7,8" \
    --has_nucleus_sampling 1 \

