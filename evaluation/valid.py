import json
import os
from util import HistoryCategory

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))


def main():
    
    model_size = '7b' # 34b 7b

    history_data_path = "/home/22ys22/project/fm-apr-replay/dataset/history_blame"
    evaluate_path = os.path.join(CURRENT_DIR_PATH, f"codellama_{model_size}_instruct_hf")

    for file_name in os.listdir(evaluate_path):
        if not file_name.endswith('.json'):
            continue
        # baseline
        if file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                result['valid'] = 1
        # 2
        if file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline_co_evolved_functions_name_modified_file_blame.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                # check if it is valid or not
                history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                bug_history_info: dict = json.load(open(history_save_path, 'r'))
                if bug_history_info['blame_commit'] and bug_history_info['blame_commit']['function'][
                    'functions_name_co_evolved_modified_file']:
                    result['valid'] = 1
                else:
                    result['valid'] = 0

        # 3
        elif file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline_co_evolved_functions_name_all_files_blame.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                # check if it is valid or not
                history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                bug_history_info: dict = json.load(open(history_save_path, 'r'))
                if bug_history_info['blame_commit'] and bug_history_info['blame_commit']['function'][
                    'functions_name_co_evolved_all_files']:
                    result['valid'] = 1
                else:
                    result['valid'] = 0
        # 4
        elif file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline_all_functions_name_modified_file_blame.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                # check if it is valid or not
                history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                bug_history_info: dict = json.load(open(history_save_path, 'r'))
                if bug_history_info['blame_commit'] and bug_history_info['blame_commit']['function'][
                    'functions_name_modified_file']:
                    result['valid'] = 1
                else:
                    result['valid'] = 0
        # 5
        elif file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline_all_functions_name_all_files_blame.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                # check if it is valid or not
                history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                bug_history_info: dict = json.load(open(history_save_path, 'r'))
                if bug_history_info['blame_commit'] and bug_history_info['blame_commit']['function'][
                    'functions_name_all_files']:
                    result['valid'] = 1
                else:
                    result['valid'] = 0
        # 6
        elif file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline_all_co_evolved_files_name_blame.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                # check if it is valid or not
                history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                bug_history_info: dict = json.load(open(history_save_path, 'r'))
                if bug_history_info['blame_commit'] and bug_history_info['blame_commit']['file'][
                    'files_name_in_blame_commit']:
                    result['valid'] = 1
                else:
                    result['valid'] = 0
        # 7
        elif file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline_function_code_pair_blame.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                # check if it is valid or not
                history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                bug_history_info: dict = json.load(open(history_save_path, 'r'))
                if (bug_history_info['blame_commit'] and
                        (bug_history_info['blame_commit']['function']['function_code_before'] or
                         bug_history_info['blame_commit']['function']['function_code_after'])):
                    result['valid'] = 1
                else:
                    result['valid'] = 0
        # 8
        elif file_name == f'unittest_result_codellama_{model_size}_instruct_hf_{HistoryCategory.baseline_file_code_patch_blame.name}.json':
            name_suf_dict = json.load(open(os.path.join(evaluate_path, file_name), 'r'))
            for bug_id, result in name_suf_dict.items():
                # check if it is valid or not
                history_save_path = os.path.join(history_data_path, f"{bug_id}.json")
                bug_history_info: dict = json.load(open(history_save_path, 'r'))
                if bug_history_info['blame_commit'] and bug_history_info['blame_commit']['file']['file_patch']:
                    result['valid'] = 1
                else:
                    result['valid'] = 0
        with open(os.path.join(evaluate_path, file_name), 'w') as f:
            json.dump(name_suf_dict, f, indent=2)


if __name__ == "__main__":
    main()
