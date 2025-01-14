import os
import json
import csv
from copy import deepcopy

from prompt_construction import construct_prompt_codellama_34b_instruct
from util import HistoryCategory, bugs_fail_ground_test, bugs_all_51_ids
from transformers import AutoTokenizer

# https://openai.com/api/pricing/
# gpt-3.5-turbo-instruct
# $0.00150 / 1K input tokens
# $0.00200 / 1K output tokens

# source_path =f"/home/22ys22/project/fm-apr-replay/backup/model_inference/codellama_7b_instruct_hf_instruct-newprompt/"
# source_path =f"/home/22ys22/project/fm-apr-replay/backup/model_inference/codellama_7b_instruct_hf_infill-newprompt/"

bugs_meta_data_file = "/home/22ys22/project/fm-apr-replay/dataset/bugs_meta_data.json"
history_data_path = "/home/22ys22/project/fm-apr-replay/dataset/history_blame"
bugs_description_file = "/home/22ys22/project/fm-apr-replay/dataset/github_issue/bugs_description.json"


def main():

    source_path = f"/home/22ys22/project/fm-apr-replay/backup/model_inference/codellama_7b_instruct_hf_instruct_oldprompt/"
    model_id = 'codellama/CodeLlama-7b-Instruct-hf'
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    instruct_actual = f"/home/22ys22/project/fm-apr-replay/analysis/RQ3/cost_instruct_actual.csv"
    if os.path.exists(instruct_actual):
        os.remove(instruct_actual)
    cost_actual(tokenizer, source_path, instruct_actual)

    instruct_simulate_10_times = f"/home/22ys22/project/fm-apr-replay/analysis/RQ3/cost_instruct_simulate_10_times.csv"
    if os.path.exists(instruct_simulate_10_times):
        os.remove(instruct_simulate_10_times)
    cost_simulate_10_times(tokenizer, source_path, instruct_simulate_10_times)


def save_result(save_csv_file, model_id, setting_id, setting_name, bug_id, input_size, output_size, test_result):
    if not os.path.exists(save_csv_file):
        with open(save_csv_file, 'w') as f:
            csv_write = csv.writer(f)
            csv_head = ["model_id", "setting_id", "setting_name", "bug_id", "input_tokens", "output_tokens", "cost"]
            csv_write.writerow(csv_head)
    with open(save_csv_file, 'a+') as f:
        csv_write = csv.writer(f)
        csv_row = [model_id, setting_id, setting_name, bug_id, input_size, output_size, test_result]
        csv_write.writerow(csv_row)


def cost_actual(tokenizer, analysis_file_dir, output_csv_file):
    for file_name in os.listdir(analysis_file_dir):
        if file_name.endswith('.json'):
            for setting in HistoryCategory:
                if f'{setting.name}.json' == file_name:
                    name_suf_dict = json.load(open(os.path.join(analysis_file_dir, file_name), 'r'))

                    result_save_path = os.path.join(analysis_file_dir, f'unittest_result_{setting.name}_cost.json')

                    if os.path.exists(result_save_path):
                        os.remove(result_save_path)
                    all_51_bugs = deepcopy(bugs_all_51_ids)
                    for bug_id, result in name_suf_dict.items():
                        if str(bug_id) not in bugs_all_51_ids:
                            continue
                        all_51_bugs.remove(bug_id)

                        input_prompt = result['input']['prompt']
                        encode_input_prompt = tokenizer.encode(input_prompt)
                        input_prompt_length = len(encode_input_prompt)
                        print(input_prompt_length)

                        # output_prompt_greedy = result['output_original']['greedy_search']
                        # encode_output_prompt_greedy = tokenizer.encode(output_prompt_greedy)
                        # output_prompt_greedy_length = len(encode_output_prompt_greedy)
                        output_prompt_nucleus_list = [tokenizer.encode(s) for s in list(result['output_original']['nucleus_sampling'])]
                        output_prompt_nucleus_length = sum(len(s) for s in output_prompt_nucleus_list)
                        # output_prompt_length = output_prompt_greedy_length + output_prompt_nucleus_length
                        output_prompt_length = output_prompt_nucleus_length
                        print(output_prompt_length)

                        cost = input_prompt_length * 0.0015 / 1000 + output_prompt_length * 0.002 / 1000
                        save_result(output_csv_file, f"codellama_7b_instruct", setting.value, setting.name,
                                    bug_id, input_prompt_length, output_prompt_length, cost)

                    # When there are some case being missed (meet OOM)
                    if len(all_51_bugs) > 0:
                        print(f"The following are added. {all_51_bugs}")
                        for bug_id in all_51_bugs:
                            bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
                            bug_value = bugs_meta_data[bug_id]
                            history_category_flag = setting.value
                            history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                            history_meta_data: dict = json.load(open(history_save_path, 'r'))
                            bugs_description_data: dict = json.load(open(bugs_description_file, 'r'))
                            bugs_description: dict = bugs_description_data[bug_id]

                            input_prompt = construct_prompt_codellama_34b_instruct(
                                bug_value,
                                history_category_flag,
                                history_meta_data,
                                bugs_description,
                                False
                            )
                            encode_input_prompt = tokenizer.encode(input_prompt)
                            input_prompt_length = len(encode_input_prompt)
                            print(input_prompt_length)

                            output_prompt_length = 0
                            cost = input_prompt_length * 0.0015 / 1000 + output_prompt_length * 0.002 / 1000
                            save_result(output_csv_file, f"codellama_7b_instruct", setting.value, setting.name,
                                        bug_id, input_prompt_length, output_prompt_length, cost)


def cost_simulate_10_times(tokenizer, analysis_file_dir, output_csv_file):
    for file_name in os.listdir(analysis_file_dir):
        if file_name.endswith('.json'):
            for setting in HistoryCategory:
                if f'{setting.name}.json' == file_name:
                    name_suf_dict = json.load(open(os.path.join(analysis_file_dir, file_name), 'r'))

                    result_save_path = os.path.join(analysis_file_dir, f'unittest_result_{setting.name}_cost.json')

                    if os.path.exists(result_save_path):
                        os.remove(result_save_path)
                    all_51_bugs = deepcopy(bugs_all_51_ids)
                    for bug_id, result in name_suf_dict.items():
                        if str(bug_id) not in bugs_all_51_ids:
                            continue
                        all_51_bugs.remove(bug_id)

                        input_prompt = result['input']['prompt']
                        encode_input_prompt = tokenizer.encode(input_prompt)
                        input_prompt_length = len(encode_input_prompt)
                        print(input_prompt_length)

                        output_prompt_nucleus_list = [tokenizer.encode(s) for s in list(result['output_original']['nucleus_sampling'])]
                        output_prompt_nucleus_length = sum(len(s) for s in output_prompt_nucleus_list)
                        output_prompt_length = output_prompt_nucleus_length
                        print(output_prompt_length)

                        cost = 10 * input_prompt_length * 0.0015 / 1000 + output_prompt_length * 0.002 / 1000
                        save_result(output_csv_file, f"codellama_7b_instruct", setting.value, setting.name,
                                    bug_id, input_prompt_length, output_prompt_length, cost)

                    # When there are some case being missed (meet OOM)
                    if len(all_51_bugs) > 0:
                        print(f"The following are added. {all_51_bugs}")
                        for bug_id in all_51_bugs:
                            bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
                            bug_value = bugs_meta_data[bug_id]
                            history_category_flag = setting.value
                            history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                            history_meta_data: dict = json.load(open(history_save_path, 'r'))
                            bugs_description_data: dict = json.load(open(bugs_description_file, 'r'))
                            bugs_description: dict = bugs_description_data[bug_id]

                            input_prompt = construct_prompt_codellama_34b_instruct(
                                bug_value,
                                history_category_flag,
                                history_meta_data,
                                bugs_description,
                                False
                            )
                            encode_input_prompt = tokenizer.encode(input_prompt)
                            input_prompt_length = len(encode_input_prompt)
                            print(input_prompt_length)

                            output_prompt_length = 0
                            cost = 10 * input_prompt_length * 0.0015 / 1000 + output_prompt_length * 0.002 / 1000
                            save_result(output_csv_file, f"codellama_7b_instruct", setting.value, setting.name,
                                        bug_id, input_prompt_length, output_prompt_length, cost)


def cost_simulate_early_stop(tokenizer, analysis_file_dir, output_csv_file):
    for file_name in os.listdir(analysis_file_dir):
        if file_name.endswith('.json'):
            for setting in HistoryCategory:
                if f'{setting.name}.json' == file_name:
                    name_suf_dict = json.load(open(os.path.join(analysis_file_dir, file_name), 'r'))

                    result_save_path = os.path.join(analysis_file_dir, f'unittest_result_{setting.name}_cost.json')

                    if os.path.exists(result_save_path):
                        os.remove(result_save_path)
                    all_51_bugs = deepcopy(bugs_all_51_ids)
                    for bug_id, result in name_suf_dict.items():
                        if str(bug_id) not in bugs_all_51_ids:
                            continue
                        all_51_bugs.remove(bug_id)

                        input_prompt = result['input']['prompt']
                        encode_input_prompt = tokenizer.encode(input_prompt)
                        input_prompt_length = len(encode_input_prompt)
                        print(input_prompt_length)

                        output_prompt_nucleus_list = [tokenizer.encode(s) for s in list(result['output_original']['nucleus_sampling'])]
                        output_prompt_nucleus_length = sum(len(s) for s in output_prompt_nucleus_list)
                        output_prompt_length = output_prompt_nucleus_length
                        print(output_prompt_length)

                        cost = 10 * input_prompt_length * 0.0015 / 1000 + output_prompt_length * 0.002 / 1000
                        save_result(output_csv_file, f"codellama_7b_instruct", setting.value, setting.name,
                                    bug_id, input_prompt_length, output_prompt_length, cost)

                    # When there are some case being missed (meet OOM)
                    if len(all_51_bugs) > 0:
                        print(f"The following are added. {all_51_bugs}")
                        for bug_id in all_51_bugs:
                            bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
                            bug_value = bugs_meta_data[bug_id]
                            history_category_flag = setting.value
                            history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                            history_meta_data: dict = json.load(open(history_save_path, 'r'))
                            bugs_description_data: dict = json.load(open(bugs_description_file, 'r'))
                            bugs_description: dict = bugs_description_data[bug_id]

                            input_prompt = construct_prompt_codellama_34b_instruct(
                                bug_value,
                                history_category_flag,
                                history_meta_data,
                                bugs_description,
                                False
                            )
                            encode_input_prompt = tokenizer.encode(input_prompt)
                            input_prompt_length = len(encode_input_prompt)
                            print(input_prompt_length)

                            output_prompt_length = 0
                            cost = 10 * input_prompt_length * 0.0015 / 1000 + output_prompt_length * 0.002 / 1000
                            save_result(output_csv_file, f"codellama_7b_instruct", setting.value, setting.name,
                                        bug_id, input_prompt_length, output_prompt_length, cost)



if __name__ == '__main__':
    main()
