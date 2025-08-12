import os
import re
import csv
import subprocess
from argparse import ArgumentParser
from datetime import datetime
from typing import Dict
from util import initialize_result_dict, get_model_and_prompt_enum
from inference_cost_util import process_early_stop_custom_settings_order, get_evaluation_test_result, get_setting_order_es_unisorted, \
    get_setting_order_es_accsorted, generate_setting_acc_scatter_csv, generate_all_scenarios_summary_csv, all_scenarios_symmetry_summary_csv

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
RQ_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, 'RQ3'))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))
EVALUATION_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup/evaluation'))
MODEL_INFERENCE_LOG_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup/model_inference/log'))


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

            model_inference_log_path = f"{MODEL_INFERENCE_LOG_BASE_PATH}/{dataset_name}/{model_inference_dir}"
            output_csv_exhaustive = f"{output_path_model}/time_exhaustive.csv"

            # Sort settings to ensure ascending order
            setting_order_default = ['1', '2', '3', '4', '5', '6', '7', '8']

            # be very careful that there is model_name_enum.name_in_path not model_name
            log_file_name_prefix = f"{model_name_enum.name_in_path}_{dataset_name}_{prompt_style}"
            # 1. exhaustive scenario
            time_calculate_exhaustive(model_name, model_inference_log_path, output_csv_exhaustive, log_file_name_prefix, all_bug_ids,
                                      test_case_result_dict_all_bug_setting, setting_order_default)

            # 2. early_stop scenario
            output_csv_early_stop = f"{output_path_model}/time_early_stop.csv"
            setting_order_early_stop = setting_order_default
            process_early_stop_custom_settings_order(output_csv_exhaustive, output_csv_early_stop,
                                                     setting_order_early_stop)

            # 3. ES-AccSorted scenario
            output_csv_es_accsorted = f"{output_path_model}/time_es_accsorted.csv"
            setting_order_es_accsorted = get_setting_order_es_accsorted(test_case_result_dict_all_bug_setting)
            print(f"setting_order_es_accsorted: {setting_order_es_accsorted}")
            process_early_stop_custom_settings_order(output_csv_exhaustive, output_csv_es_accsorted,
                                                     setting_order_es_accsorted)

            # 4. ES-UniSorted scenario
            output_csv_es_unisorted = f"{output_path_model}/time_es_unisorted.csv"
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
            output_csv_summary = f"{output_path_model}/time_summary.csv"
            generate_all_scenarios_summary_csv(all_scenarios_csv_file_dict, output_csv_summary,
                                               value_field='duration_second')

            all_scenarios_setting_order_dict = {
                'exhaustive': setting_order_default,
                'early_stop': setting_order_early_stop,
                'es_accsorted': setting_order_es_accsorted,
                'es_unisorted': setting_order_es_unisorted
            }
            # 6. Symmetry summary of 4 scenarios
            output_csv_summary_symmetry = f"{output_path_model}/time_summary_symmetry.csv"
            all_scenarios_symmetry_summary_csv(all_scenarios_csv_file_dict, all_scenarios_setting_order_dict, output_csv_summary_symmetry,
                                               value_field='duration_second')

            # 7. Only for exhaustive scenario, do scatter plot of time per setting and percentage of bug fixed per setting
            output_csv_accuracy_vs_time = f"{output_path_model}/time_vs_accuracy.csv"
            generate_setting_acc_scatter_csv(test_case_result_dict_all_bug_setting, output_csv_exhaustive, output_csv_accuracy_vs_time,
                                             value_field='duration_second')


def parse_inference_start_end_with_bug_id(log_file_path: str) -> dict:
    with open(log_file_path, "r") as f:
        log_text = f.read()
    # Regex to find all start lines with bug id
    start_pattern = list(re.finditer(
        r"Current time (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): Start model\.generate\(\) to generate fixed code for bug (\d+)\.\.\.\.\.\.",
        log_text
    ))

    # Pre-extract all "Start generation" timestamps
    generation_starts = list(re.finditer(
        r"Current time (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}): Start generation",
        log_text
    ))

    results = {}
    last_pos = 0  # for optimizing search

    for start_match in start_pattern:
        start_time_str, bug_id_str = start_match.groups()
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        bug_id = str(bug_id_str)
        start_pos = start_match.end()
        end_time = None

        # Find the first "Start generation" after this start
        for i in range(last_pos, len(generation_starts)):
            gen_match = generation_starts[i]
            if gen_match.start() > start_pos:
                end_time_str = gen_match.group(1)
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                last_pos = i  # next search can begin from here
                break

        # handle the last one
        if not end_time:
            assert start_match == start_pattern[-1], "Only the end time of the final bug could be empty!"
            end_time = get_file_last_modify_time(log_file_path)
        if end_time:
            duration_seconds = int((end_time - start_time).total_seconds())
            results[bug_id] = (start_time, end_time, duration_seconds)
        else:
            print(f"Warning: Cannot get end time for bug {bug_id}")
    return results


def get_file_last_modify_time(log_file_path):
    try:
        command = ["date", "-r", log_file_path, "+%Y-%m-%d %H:%M:%S"]
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        out, err = p.communicate()

        if p.returncode != 0:
            raise RuntimeError(f"Error fetching file time: {err.strip()}")

        return datetime.strptime(out.strip(), "%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"Error getting file modification time: {e}")
        return None


def get_log_file_name(log_file_name_like, log_path):
    for file_name in os.listdir(log_path):
        if file_name.startswith(log_file_name_like):
            return file_name


def time_calculate_exhaustive(model_name, model_inference_log_path, output_csv_file, log_file_name_prefix, expected_bug_ids, test_case_result_dict,
                              setting_order):
    # If file exist, remove it first
    if os.path.exists(output_csv_file):
        os.remove(output_csv_file)
    result_settings = {}
    for setting_flag in setting_order:
        log_file_name = get_log_file_name(f"{log_file_name_prefix}_{setting_flag}", model_inference_log_path)
        assert log_file_name is not None, f"Cannot find the log file under this directory: {model_inference_log_path}"
        log_file_path = f"{model_inference_log_path}/{log_file_name}"
        result_dict = parse_inference_start_end_with_bug_id(log_file_path)
        assert result_dict.keys() == expected_bug_ids, f"bugs id in log file not match to the expected bugs id! {log_file_path}\nresult_dict:\n{result_dict.keys()}\nexpected_bug_ids\n{expected_bug_ids}"
        if result_dict.keys() != expected_bug_ids:
            print(f"bugs id in log file not match to the expected bugs id! {log_file_path}\nresult_dict:\n{result_dict.keys()}\nexpected_bug_ids\n{expected_bug_ids}")
            continue
        result_settings[setting_flag] = result_dict
    save_result(output_csv_file, model_name, result_settings, test_case_result_dict)


def save_result(output_csv_file: str, model_name: str, result_settings: Dict[str, Dict[str, tuple]],
                test_case_result_dict: Dict[int, Dict[str, int]]):
    """
    Save inference time results to CSV file with the specified column format.

    Args:
        output_csv_file: Path to output CSV file
        model_name: Name of the model being tested
        result_settings: Dictionary with setting_flag as key and result_dict as value
                        where result_dict has bug_id as key and (start_time, end_time, duration_seconds) tuple as value
        test_case_result_dict: Dictionary with bug_id as key and setting results as value
                              where setting results is a dict with setting_flag as key and test result (0/1) as value
    """
    # If file exist, remove it first
    with open(output_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        header = ['model_id', 'setting_id', 'bug_id', 'start_time', 'end_time', 'duration_second', 'test_result']
        writer.writerow(header)

        # Write data rows
        for setting_flag, result_dict in result_settings.items():
            for bug_id, (start_time, end_time, duration) in result_dict.items():
                # Get test result for this bug and setting
                test_result = test_case_result_dict.get(bug_id).get(setting_flag)
                row = [
                    model_name,
                    setting_flag,
                    bug_id,
                    start_time,
                    end_time,
                    duration,
                    test_result
                ]
                writer.writerow(row)

    print(f"Saved {output_csv_file}")


if __name__ == '__main__':
    main()
