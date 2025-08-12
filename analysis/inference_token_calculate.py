import os
import json
import csv
from argparse import ArgumentParser
from inference_cost_util import process_early_stop_custom_settings_order, generate_all_scenarios_summary_csv, \
    all_scenarios_symmetry_summary_csv, generate_setting_acc_scatter_csv, get_setting_order_es_accsorted, get_setting_order_es_unisorted, \
    get_evaluation_test_result
from util import HistoryCategory, get_model_and_prompt_enum, initialize_result_dict
from transformers import AutoTokenizer

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
RQ_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, 'RQ3'))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))
EVALUATION_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup/evaluation'))
MODEL_INFERENCE_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup/model_inference'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--datasets', type=str)
    parser.add_argument('--model_inference_dirs', type=str)
    return parser


def main():
    args = get_parser().parse_args()
    # debug
    # args.datasets = 'bugsinpy'
    # args.model_inference_dirs = 'codellama_7b_instruct_fp16_Instruction'
    for dataset_name in args.datasets.split(','):
        output_path_dataset = os.path.join(RQ_BASE, dataset_name)
        os.makedirs(output_path_dataset, exist_ok=True)

        all_bugs, _ = initialize_result_dict(dataset_name)
        all_bug_ids = all_bugs.keys()

        for model_inference_dir in args.model_inference_dirs.split(','):
            # First obtain the test cases result of each bug
            evaluation_result_path = f"{EVALUATION_BASE_PATH}/{dataset_name}/{model_inference_dir}"
            test_case_result_dict_all_bug_setting = get_evaluation_test_result(evaluation_result_path)
            assert test_case_result_dict_all_bug_setting.keys() == all_bug_ids, "Bug missing when obtain the test result"

            # Then parse the model name and prompt style
            model_name_enum, prompt_style_enum = get_model_and_prompt_enum(model_inference_dir)
            model_name, prompt_style = model_name_enum.value, prompt_style_enum.value
            if not model_name or not prompt_style:
                print(f"the model_inference_dir is not a valid path name: {model_inference_dir}")
                continue

            output_path_model = os.path.join(output_path_dataset, model_inference_dir)
            os.makedirs(output_path_model, exist_ok=True)

            model_inference_path = f"{MODEL_INFERENCE_BASE_PATH}/{dataset_name}/{model_inference_dir}"
            output_csv_exhaustive = f"{output_path_model}/token_exhaustive.csv"
            if os.path.exists(output_csv_exhaustive):
                os.remove(output_csv_exhaustive)

            tokenizer = AutoTokenizer.from_pretrained(model_name_enum.tokenizer_name)
            print(f"load tokenizer: {model_name_enum.tokenizer_name}\nmodel_max_length:{tokenizer.model_max_length}")

            # Sort settings to ensure ascending order
            setting_order_default = ['1', '2', '3', '4', '5', '6', '7', '8']
            # 1. exhaustive scenario
            token_calculate_exhaustive(model_name, model_inference_path, output_csv_exhaustive, tokenizer, all_bug_ids,
                                       test_case_result_dict_all_bug_setting, setting_order_default)

            # 2. early_stop scenario
            output_csv_early_stop = f"{output_path_model}/token_early_stop.csv"
            setting_order_early_stop = setting_order_default
            process_early_stop_custom_settings_order(output_csv_exhaustive, output_csv_early_stop,
                                                     setting_order_early_stop)

            # 3. ES-AccSorted scenario
            output_csv_es_accsorted = f"{output_path_model}/token_es_accsorted.csv"
            setting_order_es_accsorted = get_setting_order_es_accsorted(test_case_result_dict_all_bug_setting)
            print(f"setting_order_es_accsorted: {setting_order_es_accsorted}")
            process_early_stop_custom_settings_order(output_csv_exhaustive, output_csv_es_accsorted,
                                                     setting_order_es_accsorted)

            # 4. ES-UniSorted scenario
            output_csv_es_unisorted = f"{output_path_model}/token_es_unisorted.csv"
            setting_order_es_unisorted = get_setting_order_es_unisorted(test_case_result_dict_all_bug_setting)
            print(f"setting_order_es_unisorted: {setting_order_es_unisorted}")
            process_early_stop_custom_settings_order(output_csv_exhaustive, output_csv_es_unisorted,
                                                     setting_order_es_unisorted)

            # 5. Summary of 4 scenarios
            all_scenarios_csv_file_dict = {
                'exhaustive': output_csv_exhaustive,
                'early_stop': output_csv_early_stop,
                'es_accsorted': output_csv_es_accsorted,
                'es_unisorted': output_csv_es_unisorted
            }
            output_csv_summary = f"{output_path_model}/token_summary.csv"
            generate_all_scenarios_summary_csv(all_scenarios_csv_file_dict, output_csv_summary,
                                               value_field='total_length')

            # add2: after checking OpenAI, Claude and DeepSeek Models Pricing, the output tokens are normally 4 times expensive than input tokens
            output_csv_summary_weighted = f"{output_path_model}/token_summary_weighted.csv"
            generate_all_scenarios_summary_csv(all_scenarios_csv_file_dict, output_csv_summary_weighted,
                                               value_field='total_length_weighted')

            all_scenarios_setting_order_dict = {
                'exhaustive': setting_order_default,
                'early_stop': setting_order_early_stop,
                'es_accsorted': setting_order_es_accsorted,
                'es_unisorted': setting_order_es_unisorted
            }
            # 6. Symmetry summary of 4 scenarios
            output_csv_summary_symmetry = f"{output_path_model}/token_summary_symmetry.csv"
            all_scenarios_symmetry_summary_csv(all_scenarios_csv_file_dict, all_scenarios_setting_order_dict, output_csv_summary_symmetry,
                                               value_field='total_length')

            # add3: after checking OpenAI, Claude and DeepSeek Models Pricing, the output tokens are normally 4 times expensive than input tokens
            output_csv_summary_symmetry_weighted = f"{output_path_model}/token_summary_symmetry_weighted.csv"
            all_scenarios_symmetry_summary_csv(all_scenarios_csv_file_dict, all_scenarios_setting_order_dict, output_csv_summary_symmetry_weighted,
                                               value_field='total_length_weighted')

            # 7. Only for exhaustive scenario, do scatter plot of token per setting and percentage of bug fixed per setting
            output_csv_accuracy_vs_token = f"{output_path_model}/token_vs_accuracy.csv"
            generate_setting_acc_scatter_csv(test_case_result_dict_all_bug_setting, output_csv_exhaustive, output_csv_accuracy_vs_token,
                                             value_field='total_length')

            # add4: after checking OpenAI, Claude and DeepSeek Models Pricing, the output tokens are normally 4 times expensive than input tokens
            output_csv_accuracy_vs_token_weighted = f"{output_path_model}/token_vs_accuracy_weighted.csv"
            generate_setting_acc_scatter_csv(test_case_result_dict_all_bug_setting, output_csv_exhaustive, output_csv_accuracy_vs_token_weighted,
                                             value_field='total_length_weighted')


def token_calculate_exhaustive(model_name, model_inference_path, output_csv_file, tokenizer, expected_bug_ids, bug_setting_result, setting_order):
    for setting in setting_order:
        file_name = f'{HistoryCategory(setting).name}.json'
        file_path = os.path.join(model_inference_path, file_name)
        assert os.path.exists(file_path), f"Cannot find the json file: {file_path}"

        model_inference_json = json.load(open(os.path.join(model_inference_path, file_name), 'r'))
        # print(f"load file: {os.path.join(model_inference_path, file_name)}")
        # first make sure all bugs are in the json result file
        assert model_inference_json.keys() == expected_bug_ids, "Model inference JSON keys don't match bug IDs"

        for bug_id, result in model_inference_json.items():
            input_prompt = result['input']['prompt']
            encode_input_prompt = tokenizer.encode(input_prompt)
            query_time = len(result['output_original']['nucleus_sampling'])
            input_prompt_length = len(encode_input_prompt) * query_time
            # print(input_prompt_length)

            output_prompt_nucleus_list = []
            for code in list(result['output_original']['nucleus_sampling']):
                try:
                    output_prompt_nucleus_list.append(tokenizer.encode(code))
                except Exception:
                    print(f"Meet error when encoding code for {output_csv_file}:\n{code}")
                    continue

            output_prompt_length = sum(len(s) for s in output_prompt_nucleus_list)
            # print(output_prompt_length)
            total = input_prompt_length + output_prompt_length

            # add1: after checking OpenAI, Claude and DeepSeek Models Pricing, the output tokens are normally 4 times expensive than input tokens
            total_weighted = input_prompt_length + output_prompt_length * 4

            test_flag = bug_setting_result[bug_id][HistoryCategory(setting).value]
            save_result(output_csv_file, model_name, HistoryCategory(setting).value, bug_id, input_prompt_length, output_prompt_length, total,
                        total_weighted, test_flag)
    print(f"Saved: {output_csv_file}")


def save_result(save_csv_file, model_name, setting_id, bug_id, input_length, output_length, total_length, total_length_weighted, test_flag):
    if not os.path.exists(save_csv_file):
        with open(save_csv_file, 'w') as f:
            csv_write = csv.writer(f)
            csv_head = ["model_id", "setting_id", "bug_id", "input_length", "output_length", "total_length", "total_length_weighted", "test_result"]
            csv_write.writerow(csv_head)
    with open(save_csv_file, 'a+') as f:
        csv_write = csv.writer(f)
        csv_row = [model_name, setting_id, bug_id, input_length, output_length, total_length, total_length_weighted, test_flag]
        csv_write.writerow(csv_row)


if __name__ == '__main__':
    main()
