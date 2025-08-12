import json
import os
from argparse import ArgumentParser
import pandas as pd
from util import HistoryCategory, get_model_and_prompt_enum

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
RQ_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, 'RQ1_2'))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))
EVALUATION_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup/evaluation'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--datasets', type=str)
    parser.add_argument('--evaluation_dirs', type=str)
    parser.add_argument('--history_settings', type=str)
    parser.add_argument('--bugs_meta_data_file', type=str)
    return parser


def main():
    args = get_parser().parse_args()
    sample_size = 10  # 1, 5, 10
    bugs_meta_data_file = args.bugs_meta_data_file
    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))

    for dataset_name in args.datasets.split(','):
        for evaluation_dir in args.evaluation_dirs.split(','):
            # first parse the model name and prompt style
            model_name_enum, prompt_style_enum = get_model_and_prompt_enum(evaluation_dir)
            model_name, prompt_style = model_name_enum.value, prompt_style_enum.value
            if not model_name or not prompt_style:
                print(f"the evaluation_dir is not a valid path name: {evaluation_dir}")
                continue

            bug_fixed_csv_file = f"{RQ_BASE}/{dataset_name}/{evaluation_dir}/hafix_bugs_fixed_number.csv"
            evaluation_result_path = f"{EVALUATION_BASE_PATH}/{dataset_name}/{evaluation_dir}"
            bug_id_inspect_path = f"{CURRENT_DIR_PATH}/manual_check/{dataset_name}/{evaluation_dir}"
            os.makedirs(bug_id_inspect_path, exist_ok=True)

            df = pd.read_csv(bug_fixed_csv_file)
            baseline = "setting_1"
            baseline_fails = df[df[baseline] == '0']

            for history_flag in args.history_settings.split(','):
                # Find bugs where baseline=0 but history_setting=1
                history_unique_fixes = baseline_fails[baseline_fails[f"setting_{history_flag}"] == '1']
                bug_ids = history_unique_fixes['bug_id'].tolist()
                print(f"heuristics_{history_flag} can uniquely fix {len(history_unique_fixes)} bugs:\n{bug_ids}")
                cases_print = {}
                file_name = f'unittest_result_{HistoryCategory(history_flag).name}.json'
                name_suf_dict = json.load(open(os.path.join(evaluation_result_path, file_name), 'r'))
                for bug_id, result in name_suf_dict.items():
                    if bug_id not in bug_ids:
                        continue
                    for index, test_flag in enumerate(list(result['nucleus_sampling_flags'])[:sample_size]):
                        if test_flag == 'Pass':
                            if bug_id not in cases_print:
                                cases_print[bug_id] = []
                            cases_print[bug_id].append(result["nucleus_sampling"][index])

                for bug_id, solution_list in cases_print.items():
                    bug_inspect_file = f"{bug_id_inspect_path}/{bug_id}.txt"
                    # Delete if exists
                    if os.path.exists(bug_inspect_file):
                        os.remove(bug_inspect_file)
                    bug_id_inspect_result = open(bug_inspect_file, 'a')
                    bug_id_inspect_result.write(f"####### inspect model-generated code for bug {bug_id} on history heuristic_{history_flag}: {HistoryCategory(history_flag).name} #######\n")
                    bug_value = bugs_meta_data.get(bug_id)
                    buggy_code = bug_value['function']['function_before']
                    ground_fixed_code = bug_value['function']['function_after']
                    buggy_line_content = bug_value['buggy_line_content']
                    bug_id_inspect_result.write(f"#1. buggy_line\n{buggy_line_content}\n\n")
                    bug_id_inspect_result.write(f"#2. buggy code\n{buggy_code}\n\n")
                    bug_id_inspect_result.write(f"#3. ground fixed code\n{ground_fixed_code}\n\n")
                    for solution in solution_list:
                        bug_id_inspect_result.write(f"{solution}\n")


if __name__ == "__main__":
    main()
