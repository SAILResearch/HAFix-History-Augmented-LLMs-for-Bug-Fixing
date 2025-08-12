import requests
import json
import os.path
from argparse import ArgumentParser
from pathlib import Path
import torch
from datetime import datetime

from util import HistoryCategory, bugsinpy_bugs_fail_ground_test
from model_output_parser import parse_output_deepseek_coder, parse_output_codellama_instruct, parse_output_infill
from prompt_construction import construct_prompt, BUG_MASK_TOKEN

DATASET_LANGUAGES = {
    "bugsinpy": "Python",
    "defects4j": "Java"
}


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--dataset', type=str)
    parser.add_argument('--prompt_style', type=str, choices=['Instruction', 'InstructionLabel', 'InstructionMask'])
    parser.add_argument('--subject_model_id', type=str)
    parser.add_argument('--model_serving_api', type=str)
    parser.add_argument('--history_category', type=str)
    parser.add_argument('--bugs_meta_data_file', type=str)
    parser.add_argument('--bugs_description_file', type=str)
    parser.add_argument('--history_data_path', type=Path)
    parser.add_argument('--result_output_path', type=Path)
    parser.add_argument('--num_return_sequences', type=int, default=10)

    return parser


args = get_parser().parse_args()


def main():
    # only 7B and 13B Code Llama and Code Llama - Instruct variants support infilling based on surrounding content.

    gpu_num = torch.cuda.device_count()
    print(f"The number of GPU available is: {gpu_num}\n")

    dataset_name = args.dataset
    prompt_style = args.prompt_style
    model_id = args.subject_model_id
    model_serving_api = args.model_serving_api
    history_category_flag = str(args.history_category)
    bugs_meta_data_file = args.bugs_meta_data_file
    bugs_description_file = args.bugs_description_file
    history_data_path = args.history_data_path
    result_output_path = args.result_output_path
    num_return_sequences = args.num_return_sequences
    print(f"function_level_history flag: {history_category_flag}")

    # for model_id in subject_models:
    print("==============================================================================================")
    print(f"dataset_name: {dataset_name}\nprompt_style: {prompt_style}\nmodel_id: {model_id}\n"
          f"history_category_flag: {history_category_flag}\nmodel_serving_api: {model_serving_api}\n"
          f"num_return_sequences: {num_return_sequences}\nstart generation!")
    model_generation(
        dataset_name,
        prompt_style,
        model_id,
        model_serving_api,
        bugsinpy_bugs_fail_ground_test,
        history_category_flag,
        bugs_meta_data_file,
        bugs_description_file,
        history_data_path,
        result_output_path,
        num_return_sequences
    )
    print(f"dataset_name: {dataset_name}\nprompt_style: {prompt_style}\nmodel_id: {model_id}\n"
          f"history_category_flag: {history_category_flag}\nmodel_serving_api: {model_serving_api}\n"
          f"num_return_sequences: {num_return_sequences}\nfinish generation!")
    print("==============================================================================================")


def model_generation(dataset_name, prompt_style, model_id, model_serving_api, bugs_fail_ground_test,
                     history_category_flag, bugs_meta_data_file, bugs_description_file, history_data_path,
                     result_output_path, num_return_sequences):
    # Validate dataset
    if dataset_name not in DATASET_LANGUAGES:
        raise ValueError(f"Unsupported dataset: {dataset_name}. Supported: {list(DATASET_LANGUAGES.keys())}")

    dataset_language = DATASET_LANGUAGES[dataset_name]

    model_name = model_id.replace('-', '_').replace(':', '_').lower()
    target_path = os.path.join(result_output_path, f"{model_name}_{prompt_style}")
    os.makedirs(target_path, exist_ok=True)
    result_save_path = os.path.join(target_path, f"{HistoryCategory(history_category_flag).name}.json")

    if os.path.exists(result_save_path):
        os.remove(result_save_path)

    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
    bugs_description_data: dict = json.load(open(bugs_description_file, 'r'))
    result = {}
    for bug_id, bug_value in bugs_meta_data.items():
        # debug
        # if bug_id != '3':
        #     continue
        if dataset_name == "bugsinpy" and bug_id in bugs_fail_ground_test:
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

        # merge deepseek and codellama in same prompt construction function
        prompt, masked_buggy_code, indent_space_str = construct_prompt(
            dataset_name,
            model_id,
            prompt_style,
            bug_value,
            history_category_flag,
            history_meta_data,
            bugs_description,
            dataset_language
        )

        # To stop the execution of script if the prompt is empty
        assert prompt != ''

        if int(code_length) < 100:
            max_gen_len = 500
        elif int(code_length) < 500:
            max_gen_len = 1000
        else:
            max_gen_len = 1500
        print(f"{model_id}, history category: {HistoryCategory(history_category_flag).name}, prompt is:\n{prompt}")

        _, start_model_generate_time = current_time()
        print(f"Current time {start_model_generate_time}: Start model.generate() to generate fixed code for bug {bug_id}......")

        # 2. top-p/nucleus sampling: do_sample = False and num_beams = 1
        # torch.cuda.empty_cache()
        try:
            generation_output_nucleus = []
            for _ in range(num_return_sequences):
                data = {
                    "model": model_id,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.95,
                        "top_k": 50,
                        "num_predict": max_gen_len
                    }
                }
                response = requests.post(model_serving_api, json=data)
                if response.status_code == 200:
                    generation_output_nucleus.append(response.json()["response"])
                else:
                    print(f"Request failed with status code {response.status_code}")
        except:
            print(f"bug: {bug_id} meet error on nucleus sampling!")
            # torch.cuda.empty_cache()
            print(f"current memory summary:\n{torch.cuda.memory_summary()}")
            continue

        _, end_model_generate_time = current_time()
        print(f"Current time {end_model_generate_time}: End model.generate() to generate fixed code for bug {bug_id}......")

        result_nucleus_original = generation_output_nucleus
        result_nucleus_parsed = []
        for i, output in enumerate(generation_output_nucleus):
            try:
                if prompt_style == "Instruction" or prompt_style == "InstructionLabel":
                    if 'deepseek' in model_id:
                        decoded_result_i_parsed = parse_output_deepseek_coder(output, dataset_language)
                    elif 'codellama' in model_id:
                        decoded_result_i_parsed = parse_output_codellama_instruct(output, dataset_language)

                elif prompt_style == 'InstructionMask':
                    decoded_result_i_parsed = parse_output_infill(output, dataset_language)
                    decoded_result_i_parsed_add_indent = indent_space_str + decoded_result_i_parsed.lstrip() if (
                            indent_space_str != "") else decoded_result_i_parsed
                    decoded_result_i_parsed = masked_buggy_code.replace(BUG_MASK_TOKEN, decoded_result_i_parsed_add_indent)
            except:
                print(f"bug {bug_id}'s {i}th nucleus result cannot be parsed!")
                decoded_result_i_parsed = ""
            result_nucleus_parsed.append(decoded_result_i_parsed)

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
                "greedy_search": "",
                "nucleus_sampling": result_nucleus_parsed
            },
            "output_original": {
                "greedy_search": "",
                "nucleus_sampling": result_nucleus_original
            },
        }
        json.dump(result, open(result_save_path, 'w'), indent=2)
        print(f"mode_id: {model_id}\n, history category: {HistoryCategory(history_category_flag).name}\n, "
              f"finish the bug: {bug_id}!\n"
              f"max_gen_len: {max_gen_len}\n\n"
              f"decoding_greedy_search_original_output: \n"
              f"decoding_nucleus_sampling_original_output: \n{result_nucleus_original}"
              )
        print("===============================================================================")


def current_time():
    current_time_ = datetime.now()
    return current_time_, current_time_.strftime("%Y-%m-%d %H:%M:%S")


def time_period_minutes(end_time, start_time):
    time_period = end_time - start_time
    total_seconds = time_period.total_seconds()
    return round(total_seconds / 60, 1)


if __name__ == '__main__':
    main()
