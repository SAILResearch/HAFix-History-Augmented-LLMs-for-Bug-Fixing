import json
# os.environ["cuda_visible_devices"] = "1,2,3,4,5,6,7"
import os.path
from argparse import ArgumentParser
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from datetime import datetime

from prompt_construction_infill import construct_prompt_infill
from util import HistoryCategory, bugs_fail_ground_test
from model_output_parser import (parse_output_codellama_34b_instruct,
                                 parse_output_codellama_34b_python,
                                 parse_output_codellama_70b_instruct,
                                 parse_output_codellama_70b_python, parse_output_infill)
from prompt_construction import (construct_prompt_codellama_34b_instruct,
                                 construct_prompt_codellama_34b_python,
                                 construct_prompt_codellama_70b_instruct,
                                 construct_prompt_codellama_70b_python)


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--prompt_style', type=str, choices=['instruct', 'infill'])
    parser.add_argument('--subject_model_id', type=str)
    parser.add_argument('--history_category', type=str)
    parser.add_argument('--bugs_meta_data_file', type=str)
    parser.add_argument('--bugs_description_file', type=str)
    parser.add_argument('--history_data_path', type=Path)
    parser.add_argument('--result_output_path', type=Path)
    parser.add_argument('--has_nucleus_sampling', type=str)
    parser.add_argument('--is_buggy_line_labeled', type=str)
    parser.add_argument('--bug_id_list', nargs='+')
    return parser


args = get_parser().parse_args()


def main():
    # only 7B and 13B Code Llama and Code Llama - Instruct variants support infilling based on surrounding content.

    gpu_num = torch.cuda.device_count()
    print(f"The number of GPU available is: {gpu_num}\n")

    # narrow the scope of subject projects
    subject_projects = ["luigi", "youtube-dl", "keras", "thefuck"]

    prompt_style = args.prompt_style
    model_id = args.subject_model_id
    history_category_flag = str(args.history_category)
    bugs_meta_data_file = args.bugs_meta_data_file
    bugs_description_file = args.bugs_description_file
    history_data_path = args.history_data_path
    result_output_path = args.result_output_path
    has_nucleus_sampling = bool(int(args.has_nucleus_sampling))
    is_buggy_line_labeled = bool(int(args.is_buggy_line_labeled))
    bug_id_list = args.bug_id_list
    print(f"function_level_history flag: {history_category_flag}")
    print(f"Target bug_id_list is: {bug_id_list}")

    # for model_id in subject_models:
    print("==============================================================================================")
    print(f"{model_id}, history category: {HistoryCategory(history_category_flag).name} start generation!")
    model_generation(
        prompt_style,
        model_id,
        subject_projects,
        bugs_fail_ground_test,
        history_category_flag,
        bugs_meta_data_file,
        bugs_description_file,
        history_data_path,
        result_output_path,
        has_nucleus_sampling,
        is_buggy_line_labeled,
        bug_id_list
    )
    print(f"{model_id}, history category: {HistoryCategory(history_category_flag).name} finish generation!")
    print("==============================================================================================")


def model_generation(prompt_style, model_id, subject_projects, bugs_fail_ground_test, history_category_flag, bugs_meta_data_file,
                     bugs_description_file, history_data_path, result_output_path,
                     has_nucleus_sampling, is_buggy_line_labeled, bug_id_list):
    # prompt = f"{B_INST} {B_SYS}{SYSTEM_PROMPT}{E_SYS}{pre_prompt} {E_INST}"
    # Prompt: https://www.promptingguide.ai/models/code-llama#configure-model-access
    # prompt template for codellama-python: https://huggingface.co/TheBloke/CodeLlama-7B-Python-GGUF
    # Performance comparison: https://huggingface.co/blog/codellama

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=torch.float16,
        # device_map="balanced_low_0",
        device_map="auto",
    )
    print(f"model device_map:\n{json.dumps(model.hf_device_map, indent=4)}\n")
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # quantized model
    # model = AutoModelForCausalLM.from_pretrained(
    #     model_id,
    #     # torch_dtype=torch.float16,
    #     # device_map="balanced_low_0",
    #     device_map="auto",
    #     trust_remote_code=True,
    #     revision="main"
    # )
    # print(f"model device_map:\n{json.dumps(model.hf_device_map, indent=4)}\n")
    # tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)

    # save the result
    model_name = model_id.split('/')[1].replace('-', '_').lower()
    target_path = os.path.join(result_output_path, f"{model_name}_{prompt_style}")
    os.makedirs(target_path, exist_ok=True)
    result_save_path = os.path.join(target_path, f"{HistoryCategory(history_category_flag).name}.json")

    if os.path.exists(result_save_path):
        os.remove(result_save_path)

    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
    bugs_description_data: dict = json.load(open(bugs_description_file, 'r'))
    result = {}
    for bug_id, bug_value in bugs_meta_data.items():
        if bug_id not in bug_id_list:
            continue
        # if bug_id != '1':
        #     break
        # if bug_value['project_name'] not in subject_projects:
        #     continue
        # if int(bug_id) < 60:
        #     continue
        if bug_id in bugs_fail_ground_test:
            continue

        start_generation_time, start_generation_time_format = current_time()
        print(f"Current time {start_generation_time_format}: Start generation\n")

        code_length = bug_value['function']['function_before_token_count']

        history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
        if not os.path.exists(history_save_path):
            # id = 34, 39
            # skip the bugs without history
            print(f"bug {bug_id} has no history data.")
            continue
        history_meta_data: dict = json.load(open(history_save_path, 'r'))
        bugs_description: dict = bugs_description_data[bug_id]

        if prompt_style == "instruct":
            if 'CodeLlama-34b-Instruct' in model_id or 'CodeLlama-13b-Instruct' in model_id or 'CodeLlama-7b-Instruct' in model_id:
                prompt = construct_prompt_codellama_34b_instruct(
                    bug_value,
                    history_category_flag,
                    history_meta_data,
                    bugs_description,
                    is_buggy_line_labeled
                )
                input_tokens = tokenizer(
                    prompt,
                    return_tensors="pt",
                    add_special_tokens=True
                ).input_ids.to('cuda')
            elif 'CodeLlama-34b-Python' in model_id:
                prompt = construct_prompt_codellama_34b_python(bug_value, history_category_flag, history_meta_data,
                                                               bugs_description)
                input_tokens = tokenizer(
                    prompt,
                    return_tensors="pt",
                    add_special_tokens=True
                ).input_ids.to('cuda')
            elif 'CodeLlama-70b-Instruct' in model_id:
                prompt = construct_prompt_codellama_70b_instruct(bug_value, history_category_flag, history_meta_data,
                                                                 bugs_description)
                input_tokens = tokenizer.apply_chat_template(
                    prompt,
                    return_tensors="pt"
                ).to("cuda")
            elif 'CodeLlama-70b-Python' in model_id:
                prompt = construct_prompt_codellama_70b_python(bug_value, history_category_flag, history_meta_data,
                                                               bugs_description)
                input_tokens = tokenizer(
                    prompt,
                    return_tensors="pt",
                    add_special_tokens=True
                ).input_ids.to('cuda')

            if int(code_length) < 100:
                max_gen_len = 500
            elif int(code_length) < 500:
                max_gen_len = 1000
            else:
                max_gen_len = 1500

        elif prompt_style == 'infill':
            # infill
            prompt, masked_buggy_code = construct_prompt_infill(bug_value, history_category_flag, history_meta_data,
                                                                bugs_description)
            if history_category_flag == HistoryCategory.pure_infill.value:
                prompt = masked_buggy_code

            input_tokens = tokenizer(
                prompt,
                return_tensors="pt",
                add_special_tokens=True
            ).input_ids.to('cuda')

            max_gen_len = 100

        num_tokens = input_tokens.shape[1]

        print(f"{model_id}, history category: {HistoryCategory(history_category_flag).name}, prompt is:\n{prompt}")

        return_sequences = 10
        # torch.cuda.empty_cache()

        # decoding strategy: https://michael-franke.github.io/npNLG/06-LSTMs/06d-decoding-GPT2.html
        # 1. greedy search: do_sample = False and num_beams = 1

        _, start_model_generate_time = current_time()

        print(
            f"Current time {start_model_generate_time}: Start model.generate() to generate fixed code for bug {bug_id}......")

        try:
            generation_output_greedy = model.generate(
                input_ids=input_tokens,
                max_new_tokens=max_gen_len,
            )
        except:
            print(f"bug: {bug_id} meet error on greedy search!")
            # torch.cuda.empty_cache()
            print(f"current memory summary:\n{torch.cuda.memory_summary()}")
            continue
        generation_output_greedy_fixed_code = generation_output_greedy[0][input_tokens.shape[-1]:]

        if prompt_style == "instruct":
            result_greedy_original = tokenizer.decode(generation_output_greedy_fixed_code,
                                                      skip_special_tokens=True).strip()
        elif prompt_style == 'infill':
            result_greedy_original = tokenizer.decode(generation_output_greedy_fixed_code, skip_special_tokens=True)

        finish_generation_time, finish_generation_time_format = current_time()

        generation_period_minutes = time_period_minutes(finish_generation_time, start_generation_time)

        print(f"Current time {finish_generation_time_format}: Finish generation\n")

        print(
            f"Input token size: {num_tokens}. Spend around {generation_period_minutes} minutes for bug {bug_id} on greedy inference!\n")

        try:
            if prompt_style == "instruct":
                if 'CodeLlama-34b-Instruct' in model_id or 'CodeLlama-13b-Instruct' in model_id or 'CodeLlama-7b-Instruct' in model_id:
                    result_greedy_parsed = parse_output_codellama_34b_instruct(result_greedy_original)
                elif 'CodeLlama-34b-Python' in model_id:
                    result_greedy_parsed = parse_output_codellama_34b_python(result_greedy_original)
                elif 'CodeLlama-70b-Instruct' in model_id:
                    result_greedy_parsed = parse_output_codellama_70b_instruct(result_greedy_original)
                elif 'CodeLlama-70b-Python' in model_id:
                    result_greedy_parsed = parse_output_codellama_70b_python(result_greedy_original)

            elif prompt_style == 'infill':
                result_greedy_parsed_infill_line = parse_output_infill(result_greedy_original)
                result_greedy_parsed = masked_buggy_code.replace("<FILL_ME>", result_greedy_parsed_infill_line)
        except:
            print(f"bug {bug_id}'s greedy result cannot be parsed!")
            result_greedy_parsed = ""

        if has_nucleus_sampling:
            # 2. top-p/nucleus sampling: do_sample = False and num_beams = 1
            # torch.cuda.empty_cache()
            try:
                generation_output_nucleus = model.generate(
                    input_ids=input_tokens,
                    max_new_tokens=max_gen_len,
                    do_sample=True,
                    top_p=0.95,
                    top_k=50,
                    temperature=0.4,
                    num_return_sequences=return_sequences,
                    # repetition_penalty=1.2,
                )
            except:
                print(f"bug: {bug_id} meet error on nucleus sampling!")
                # torch.cuda.empty_cache()
                print(f"current memory summary:\n{torch.cuda.memory_summary()}")
                continue

            result_nucleus_original = []
            result_nucleus_parsed = []
            for i, output in enumerate(generation_output_nucleus):
                if prompt_style == "instruct":
                    decoded_result_i = tokenizer.decode(output[input_tokens.shape[-1]:],
                                                        skip_special_tokens=True).strip()
                elif prompt_style == 'infill':
                    decoded_result_i = tokenizer.decode(output[input_tokens.shape[-1]:], skip_special_tokens=True)
                result_nucleus_original.append(decoded_result_i)
                try:
                    if prompt_style == "instruct":
                        if 'CodeLlama-34b-Instruct' in model_id or 'CodeLlama-13b-Instruct' in model_id or 'CodeLlama-7b-Instruct' in model_id:
                            decoded_result_i_parsed = parse_output_codellama_34b_instruct(decoded_result_i)
                        elif 'CodeLlama-34b-Python' in model_id:
                            decoded_result_i_parsed = parse_output_codellama_34b_python(decoded_result_i)
                        elif 'CodeLlama-70b-Instruct' in model_id:
                            decoded_result_i_parsed = parse_output_codellama_70b_instruct(decoded_result_i)
                        elif 'CodeLlama-70b-Python' in model_id:
                            decoded_result_i_parsed = parse_output_codellama_70b_python(decoded_result_i)
                    elif prompt_style == 'infill':
                        decoded_result_i_parsed_infill_line = parse_output_infill(decoded_result_i)
                        decoded_result_i_parsed = masked_buggy_code.replace("<FILL_ME>",
                                                                            decoded_result_i_parsed_infill_line)

                except:
                    print(f"bug {bug_id}'s {i}th nucleus result cannot be parsed!")
                    decoded_result_i_parsed = ""
                result_nucleus_parsed.append(decoded_result_i_parsed)
        else:
            result_nucleus_parsed = ""
            result_nucleus_original = ""

        result[bug_id] = {
            "id": bug_id,
            "ground_fixed_code": bug_value['function']['function_after'],
            "input": {
                "has_buggy_code": 1,
                "has_commit_msg": 1,
                "has_function_level_history": 1 if history_category_flag == '1' else 0,
                "has_file_level_history": 1 if history_category_flag == '2' else 0,
                "buggy_code": bug_value['function']['function_before'],
                "prompt": prompt
            },
            "output": {
                "greedy_search": result_greedy_parsed,
                "nucleus_sampling": result_nucleus_parsed
            },
            "output_original": {
                "greedy_search": result_greedy_original,
                "nucleus_sampling": result_nucleus_original
            },
        }
        json.dump(result, open(result_save_path, 'w'), indent=2)
        print(f"mode_id: {model_id}\n, history category: {HistoryCategory(history_category_flag).name}\n, "
              f"finish the bug: {bug_id}!\n"
              f"max_gen_len: {max_gen_len}\n\n"
              f"decoding_greedy_search_original_output: \n{result_greedy_original}\n\n\n"
              f"decoding_nucleus_sampling_original_output: \n{result_nucleus_original}"
              )
        print("===============================================================================")

    torch.cuda.empty_cache()


def current_time():
    current_time_ = datetime.now()
    return current_time_, current_time_.strftime("%Y-%m-%d %H:%M:%S")


def time_period_minutes(end_time, start_time):
    time_period = end_time - start_time
    total_seconds = time_period.total_seconds()
    return round(total_seconds / 60, 1)


if __name__ == "__main__":
    main()
