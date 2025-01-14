import copy
import json
import logging
import os
import numpy as np
import subprocess
import textwrap
import bugsinpy_command
from argparse import ArgumentParser
from datetime import datetime

from util import HistoryCategory, bugs_fail_ground_test

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))
MODEL_INFERENCE_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'model_inference'))
BUGSINPY_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, '../BugsInPy'))
PROJECTS_BASE_BUGSINPY = os.path.abspath(os.path.join(BUGSINPY_PATH, 'framework/bin/temp/'))

BUG_IDs = {'2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '16', '17', '18', '19', '20', '21', '22', '23', '24',
           '25', '26', '27', '28', '29', '30', '31', '32', '33', '35', '36', '37', '38', '41', '42', '43', '44', '45',
           '46', '47', '48', '49', '50', '51', '52', '53', '54', '60', '61', '66', '67', '68'}

def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--model_inference_dirs', type=str)
    parser.add_argument('--history_settings', type=str)
    parser.add_argument('--has_nucleus_sampling', type=str)
    return parser


args = get_parser().parse_args()


def main():
    has_nucleus_sampling = bool(int(args.has_nucleus_sampling))
    if has_nucleus_sampling:
        k_list = [1, 3, 5, 10]
    else:
        k_list = [1]

    evaluate_dir_to_file_dict = {}
    for model_inference_dir in args.model_inference_dirs.split(','):
        evaluate_dir_to_file_dict[model_inference_dir] = {}
        for history_flag in args.history_settings.split(','):
            path = f"{MODEL_INFERENCE_BASE_PATH}/{model_inference_dir}/{HistoryCategory(history_flag).name}.json"
            if os.path.exists(path):
                evaluate_dir_to_file_dict[model_inference_dir][path] = json.load(open(path, 'r'))
    print(f"construct evaluate_dir_to_file_dict length: {len(evaluate_dir_to_file_dict)}")

    bugs_meta_data_file = f"{PROJECT_DIR_BASE}/dataset/bugs_meta_data.json"
    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
    ground_error = {}

    for bug_id, bug_meta_data in bugs_meta_data.items():
        # if str(bug_id) == '2':
        #     break
        # map the git_project_name and bugsinpy_project_name

        # refactoring to skip the broken cases
        if str(bug_id) in bugs_fail_ground_test:
            continue
        bugsinpy_project_name = map_git_to_bugsinpy_project_name(bug_meta_data['project_name'])
        # 1. setup environment: checkout + compile
        setup_flag = setup_evaluation(bugsinpy_project_name, bug_meta_data)
        if setup_flag != "True":
            ground_error[bug_id] = setup_flag
            # broken case1: if ground fixed code cannot be checkout or compile, skip
            print(f"Ground {setup_flag}, skip this broken case: {bug_id}")
            continue
        # 2. test ground fixed code
        test_ground_flag = execution_tests_ground(bugsinpy_project_name)
        if test_ground_flag != 'Pass':
            ground_error[bug_id] = test_ground_flag
            # broken case2: if ground fixed code cannot pass test cases, skip
            print(f"Ground {test_ground_flag}, skip this broken case: {bug_id}")
            continue
        print("The ground fixed code pass the test case, continue evaluating model's code!")
        print("===========================================================================\n\n")

        # need to consider running test for all settings, to reduce the time-consuming checkout/compile
        # 3. start calculating pass@k
        # For each code evaluation: will return 'Error: empty', 'Fail', 'Error: test', 'Pass'

        for model_inference_dir, path_file_dict in evaluate_dir_to_file_dict.items():
            _evaluate_path = f"{CURRENT_DIR_PATH}/{model_inference_dir}"
            os.makedirs(_evaluate_path, exist_ok=True)
            for path, model_inference_json in path_file_dict.items():

                if bug_id not in model_inference_json.keys():
                    continue
                inference_value = model_inference_json[bug_id]

                # create the evaluation result files
                name_suf = os.path.split(path)[1].split('.json')[0]
                evaluate_path = f"{_evaluate_path}/unittest_result_{name_suf}.json"
                # if os.path.exists(evaluate_path):
                #     os.remove(evaluate_path)
                pass_k_result_path = f"{_evaluate_path}/pass_k_result_{name_suf}.txt"
                # if os.path.exists(pass_k_result_path):
                #     os.remove(pass_k_result_path)

                pass_k_result = open(pass_k_result_path, 'a')
                # pass_k_result.write(f"{current_time()}: Start evaluation\n")
                pass_k_result.write("=========================================\n")
                print(f"{current_time()}: Start evaluation\n")
                result_bug_id = {}
                if 1 in k_list:
                    # when k=1, using greedy search result

                    inference_code = inference_value['output']['greedy_search']
                    if inference_code is None or inference_code == "":
                        result_bug_id['greedy_search_flag'] = 'Error: empty'
                    else:
                        test_flag_g = execution_tests(bugsinpy_project_name, bug_meta_data, inference_code)
                        result_bug_id['greedy_search_flag'] = test_flag_g
                    result_bug_id['greedy_search'] = inference_code
                    print("------------------------------greedy search result------------------------------")
                    print(
                        f"{current_time()}, bug id {bug_id}, by greedy_search, unittest result: {result_bug_id['greedy_search_flag']}\n")
                    pass_k_result.write(
                        f"{current_time()}, bug id {bug_id}, by greedy_search, unittest result: {result_bug_id['greedy_search_flag']}\n")
                    print("--------------------------------------------------------------------------------\n")

                if len(set(k_list)) > 1:
                    # when k has more than one value, using nucleus sampling result
                    result_bug_id['nucleus_sampling'] = inference_value['output']['nucleus_sampling']
                    result_bug_id['nucleus_sampling_flags'] = []
                    for nucleus_inference_code in result_bug_id['nucleus_sampling']:
                        if nucleus_inference_code is None or nucleus_inference_code == "":
                            result_bug_id['nucleus_sampling_flags'].append('Error: empty')
                            continue
                        test_flag_n = execution_tests(bugsinpy_project_name, bug_meta_data, nucleus_inference_code)
                        result_bug_id['nucleus_sampling_flags'].append(test_flag_n)

                    print("------------------------------nucleus sampling result------------------------------")
                    print(
                        f"{current_time()}, bug id {bug_id}, by nucleus_sampling, unittest result: {result_bug_id['nucleus_sampling_flags']}\n")
                    pass_k_result.write(
                        f"{current_time()}, bug id {bug_id}, by nucleus_sampling, unittest result: {result_bug_id['nucleus_sampling_flags']}\n")
                    print("------------------------------nucleus sampling result------------------------------\n")
                pass_k_result.close()

                a_new_result = {bug_id: result_bug_id}
                if not os.path.exists(evaluate_path):
                    with open(evaluate_path, 'w') as evaluate_file_create:
                        json.dump(a_new_result, evaluate_file_create, indent=2)
                    evaluate_file_create.close()
                else:
                    result: dict = json.load(open(evaluate_path, 'r'))
                    result[bug_id] = result_bug_id
                    with open(evaluate_path, 'w') as evaluate_file_exist:
                        json.dump(result, evaluate_file_exist, indent=2)
                    evaluate_file_exist.close()
    print(f"The bugs who cannot pass the ground test is: {ground_error}\n")
    print(f"ALL unittest finished! Start calculating pass@k!")

    for model_inference_dir, path_file_dict in evaluate_dir_to_file_dict.items():
        _evaluate_path = f"{CURRENT_DIR_PATH}/{model_inference_dir}"
        for path, _ in path_file_dict.items():
            # create the evaluation result files
            name_suf = os.path.split(path)[1].split('.json')[0]
            evaluate_path = f"{_evaluate_path}/unittest_result_{name_suf}.json"

            # calculate pass@k, when k=5 or 10, using nucleus sampling
            result_ = evaluate_average_pass_at_k(evaluate_path, k_list)
            print(f'Evaluating pass_at_k result: {result_}\n')

            pass_k_result_path = f"{_evaluate_path}/pass_k_result_{name_suf}.txt"
            pass_k_result = open(pass_k_result_path, 'a')
            pass_k_result.write(f"The bugs who cannot pass the ground test is: {ground_error}\n")
            pass_k_result.write(f'pass_at_k_final: {result_}\n')
            pass_k_result.close()


def execution_tests(bugsinpy_project_name, bug_id_meta_data, inference_code) -> str:
    # First backup the original file and inject the model-generated code
    try:
        project_path = os.path.join(PROJECTS_BASE_BUGSINPY, bugsinpy_project_name)
        target_file_path = os.path.join(project_path, bug_id_meta_data['file']['file_path'])
        head_tail = os.path.split(target_file_path)
        target_file_path_backup = os.path.join(head_tail[0], 'backup_' + head_tail[1])

        # rename the original completion file as tmp_completion
        subprocess.run(['cp', target_file_path, target_file_path_backup])

        function_start = bug_id_meta_data['function']['function_after_start_line']
        function_end = bug_id_meta_data['function']['function_after_end_line']
        # write the new completion file
        old_file_lines = []
        with open(target_file_path, 'r') as f:
            for line in f:
                old_file_lines.append(line)
        start_line = old_file_lines[function_start - 1]
        lstrip_start_line = start_line.lstrip(" ")
        start_indent = len(start_line) - len(lstrip_start_line)
        inference_code_indent = adjust_indent(inference_code, start_indent)

        new_file_lines = old_file_lines[:function_start - 1] + ['\n', inference_code_indent, '\n'] + old_file_lines[
                                                                                                     function_end:]
        with open(target_file_path, 'w') as f:
            # f.writelines(file_lines)
            f.write(''.join(new_file_lines))
    except Exception as e:
        print(f"Meet error when execute test:\n{e}")
        return 'Error: before test'

    # Run the test case
    try:
        test_flag = bugsinpy_command.bugsinpy_test(project_path)
    except:
        # restore the original file status
        subprocess.run(['mv', target_file_path_backup, target_file_path])
        return 'Error: test'
    # restore the original file status
    subprocess.run(['mv', target_file_path_backup, target_file_path])
    return 'Pass' if test_flag else 'Fail'


def execution_tests_ground(bugsinpy_project_name):
    project_path = os.path.join(PROJECTS_BASE_BUGSINPY, bugsinpy_project_name)
    # Run the test case
    try:
        test_flag = bugsinpy_command.bugsinpy_test(project_path)
    except:
        return 'Error: test'
    return 'Pass' if test_flag else 'Fail'


def setup_evaluation(bugsinpy_project_name, bug_id_meta_data) -> str:
    # First checkout teh project to bug-fixing snapshot
    try:
        checkout_flag = bugsinpy_command.bugsinpy_checkout(bugsinpy_project_name, bug_id_meta_data['bugsinpy_id'])
    except:
        return 'Error: checkout'
    if not checkout_flag:
        return 'Error: checkout'

    project_path = os.path.join(PROJECTS_BASE_BUGSINPY, bugsinpy_project_name)
    try:
        compile_flag = bugsinpy_command.bugsinpy_compile(project_path)
    except:
        return 'Error: compile'
    if not compile_flag:
        return 'Error: compile'
    return "True"


def evaluate_average_pass_at_k(eval_result_path, k_list):
    pass_at_k_result = {}
    eval_result_json: dict = json.load(open(eval_result_path, 'r'))
    if 1 in k_list:
        # first calculate pass@1 for greedy search
        n = 1
        k = 1
        greedy_passed = {}
        for bug_id_ in BUG_IDs:
            greedy_passed[bug_id_] = 0
        for bug_id, eval_result in eval_result_json.items():
            # if bug_id not in greedy_passed:
            #     greedy_passed[bug_id] = 0
            if eval_result['greedy_search_flag'] == 'Pass':
                greedy_passed[bug_id] += 1
        pass_at_k = np.mean([compute_pass_at_k(n, pass_num, k) for _, pass_num in greedy_passed.items()])
        # pass_at_k_result[f"pass@{k}"] = f"{pass_at_k * 100}%"
        pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))

    if len(set(k_list)) > 1:
        # second calculate pass@k for nucleus sampling
        k_list_temp = copy.deepcopy(k_list)
        while 1 in k_list_temp:
            k_list_temp.remove(1)
        n = 10
        neucleus_passed = {}
        for bug_id_ in BUG_IDs:
            neucleus_passed[bug_id_] = 0
        for bug_id, eval_result in eval_result_json.items():
            # if bug_id not in neucleus_passed:
            #     neucleus_passed[bug_id] = 0
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
        for k in k_list_temp:
            pass_at_k = np.mean([compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
            # pass_at_k_result[f"pass@{k}"] = f"{pass_at_k * 100}%"
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
    return pass_at_k_result


def compute_pass_at_k(n, c, k):
    """
    n: total number of completions per task
    c: number of completions that pass all tests
    k: k in pass_at_k
    """
    if n - c < k:
        return 1
    else:
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


def adjust_indent(code, new_indent):
    # remove original indentation
    dedent_code = textwrap.dedent(code)
    # add new indentation
    indented_code = textwrap.indent(dedent_code, ' ' * new_indent)
    return indented_code


def map_git_to_bugsinpy_project_name(git_project_name: str):
    if git_project_name == "cli":
        bugsinpy_project_name = "httpie"
    elif git_project_name == "spaCy":
        bugsinpy_project_name = "spacy"
    else:
        bugsinpy_project_name = git_project_name
    return bugsinpy_project_name


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def command(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = process.communicate()
    if output != b'' or err != b'':
        print(output)
        print(err)
    return output, err


if __name__ == '__main__':
    main()
