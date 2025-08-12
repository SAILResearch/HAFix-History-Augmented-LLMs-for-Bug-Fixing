import json
import os
import subprocess
import textwrap
from argparse import ArgumentParser
from datetime import datetime
from dataset_adapter import BugsInPy, Defects4J, DatasetAdapter
from util import HistoryCategory

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))
MODEL_INFERENCE_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'model_inference'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--dataset', type=str)
    parser.add_argument('--model_inference_dirs', type=str)
    parser.add_argument('--history_settings', type=str)
    parser.add_argument('--bug_id_list', type=str, default='')
    return parser


def adapter_factory(dataset_name):
    if dataset_name == "bugsinpy":
        return BugsInPy()
    elif dataset_name == "defects4j":
        return Defects4J()
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")


def main():
    args = get_parser().parse_args()
    adapter = adapter_factory(args.dataset)

    bug_filter = set(args.bug_id_list.split(',')) if args.bug_id_list else None

    evaluate_dir_to_file_dict = {}
    for model_inference_dir in args.model_inference_dirs.split(','):
        evaluate_dir_to_file_dict[model_inference_dir] = {}
        for history_flag in args.history_settings.split(','):
            path = f"{MODEL_INFERENCE_BASE_PATH}/{adapter.dataset_name}/{model_inference_dir}/{HistoryCategory(history_flag).name}.json"
            if os.path.exists(path):
                evaluate_dir_to_file_dict[model_inference_dir][path] = json.load(open(path, 'r'))
    print(f"construct evaluate_dir_to_file_dict length: {len(evaluate_dir_to_file_dict)}")

    bugs_meta_data_file = f"{PROJECT_DIR_BASE}/dataset/{adapter.dataset_name}/{adapter.dataset_name}_bugs_meta_data.json"
    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
    ground_error = {}

    for bug_id, bug_meta_data in bugs_meta_data.items():
        # debug
        # if str(bug_id) != '1':
        #     continue

        if bug_filter and bug_id not in bug_filter:
            continue

        # refactoring to skip the broken cases
        if adapter.should_skip_bug(bug_id):
            continue

        bug_id_key = 'bugsinpy_id' if adapter.dataset_name == 'bugsinpy' else 'defects4j_id'
        project_name = adapter.map_project_name(bug_meta_data['project_name'])
        project_checkout_path = adapter.build_project_path(project_name, str(bug_meta_data[bug_id_key]))

        # 1. setup environment: checkout
        # setup_flag = setup_evaluation(adapter, project_name, str(bug_meta_data[bug_id_key]), project_checkout_path)
        # First checkout teh project to bug-fixing snapshot
        checkout_flag = adapter.checkout(project_name, str(bug_meta_data[bug_id_key]), project_checkout_path)
        print(f"after checkout, the current working directory is: {os.getcwd()}")
        if not checkout_flag:
            ground_error[bug_id] = 'Error: checkout'
            print(f"Ground {ground_error[bug_id]}, skip this broken case: {bug_id}")
            continue

        # 2. setup environment: compile
        # Bugsinpy will checkout to project_checkout_path + project name, different with Defects4J
        project_checkout_path = os.path.join(project_checkout_path, project_name) if adapter.dataset_name == 'bugsinpy' else project_checkout_path
        compile_flag = adapter.compile(project_checkout_path)
        if not compile_flag:
            ground_error[bug_id] = 'Error: compile'
            print(f"Ground {ground_error[bug_id]}, skip this broken case: {bug_id}")
            continue

        # 3. test ground fixed code
        test_ground_flag = adapter.test(project_checkout_path)
        if test_ground_flag != 'Plausible':
            ground_error[bug_id] = test_ground_flag
            # broken case2: if ground fixed code cannot pass test cases, skip
            print(f"Ground {test_ground_flag}, skip this broken case: {bug_id}")
            continue
        print("The ground fixed code pass the test case, continue evaluating model's code!")
        print("===========================================================================\n\n")

        # 4. test model-generated code
        # For each code evaluation: will return 'Error: empty', 'Fail', 'Error: test', 'Pass'
        for model_inference_dir, path_file_dict in evaluate_dir_to_file_dict.items():
            _evaluate_path = f"{CURRENT_DIR_PATH}/{adapter.dataset_name}/{model_inference_dir}"
            os.makedirs(_evaluate_path, exist_ok=True)
            for path, model_inference_json in path_file_dict.items():

                if bug_id not in model_inference_json.keys():
                    continue
                inference_value = model_inference_json[bug_id]

                # create the evaluation result files
                name_suf = os.path.split(path)[1].split('.json')[0]
                evaluate_path = f"{_evaluate_path}/unittest_result_{name_suf}_{bug_id}.json"
                # if os.path.exists(evaluate_path):
                #     os.remove(evaluate_path)
                pass_k_result_path = f"{_evaluate_path}/pass_k_result_{name_suf}.txt"
                # if os.path.exists(pass_k_result_path):
                #     os.remove(pass_k_result_path)

                pass_k_result = open(pass_k_result_path, 'a')
                # pass_k_result.write(f"{current_time()}: Start evaluation\n")
                pass_k_result.write("=========================================\n")
                result_bug_id = {'nucleus_sampling': inference_value['output']['nucleus_sampling'],
                                 'nucleus_sampling_flags': []}
                print(f"{current_time()} Start evaluation: {adapter.dataset_name}, {model_inference_dir}, heuristic_{HistoryCategory[name_suf].value}")
                # if len(set(k_list)) > 1:
                # when k has more than one value, using nucleus sampling result
                for index, nucleus_inference_code in enumerate(result_bug_id['nucleus_sampling']):
                    if nucleus_inference_code is None or nucleus_inference_code == "":
                        result_bug_id['nucleus_sampling_flags'].append('Error: empty')
                        continue
                    test_flag_n = execution_tests(adapter, project_checkout_path, bug_meta_data, nucleus_inference_code)
                    print(f'[{index+1}] bug {bug_id} testing result: {project_name}-{bug_meta_data[bug_id_key]}, {test_flag_n}')
                    result_bug_id['nucleus_sampling_flags'].append(test_flag_n)

                print("------------------------------nucleus sampling result------------------------------")
                print(
                    f"{current_time()} bug id {bug_id} {project_name}-{bug_meta_data[bug_id_key]}, by nucleus_sampling, unittest result:\n{result_bug_id['nucleus_sampling_flags']}\n")
                pass_k_result.write(
                    f"{current_time()} bug id {bug_id} {project_name}-{bug_meta_data[bug_id_key]}, by nucleus_sampling, unittest result:\n{result_bug_id['nucleus_sampling_flags']}\n")
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

    # # clean the checkout path
    # adapter.clean_checkout_dir()

    print(f"The bugs who cannot pass the ground test is: {ground_error}\n")
    print(f"ALL unittest finished!")


def execution_tests(adapter: DatasetAdapter, project_path, bug_meta_data, inference_code) -> str:
    # First backup the original file and inject the model-generated code
    try:
        target_file_path = os.path.join(project_path, bug_meta_data['file']['file_path'])
        # head_tail = os.path.split(target_file_path)
        # target_file_path_backup = os.path.join(head_tail[0], 'backup_' + head_tail[1])
        target_file_path_backup = target_file_path + '.backup'

        # rename the original completion file as tmp_completion
        subprocess.run(['cp', target_file_path, target_file_path_backup])

        function_start = bug_meta_data['function']['function_after_start_line']
        function_end = bug_meta_data['function']['function_after_end_line']

        # Handle Defects4J special cases verified by defects4j_function_location_verify.py
        if adapter.dataset_name == "defects4j":
            function_start, function_end = handle_defects4j_special_cases(
                bug_meta_data, function_start, function_end
            )

        old_file_lines = []
        with open(target_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                old_file_lines.append(line)
        start_line = old_file_lines[function_start - 1]
        lstrip_start_line = start_line.lstrip(" ")
        start_indent = len(start_line) - len(lstrip_start_line)
        inference_code_indent = adjust_indent(inference_code, start_indent)
        # print(f'function_start: {function_start}\nstart_line: {start_line}\nlast sentence: {old_file_lines[:function_start - 1][len(old_file_lines[:function_start - 1])-1]}\n')
        # print(f'inference_code:\n{inference_code}\ninference_code_indent: \n{inference_code_indent}\n')
        new_file_lines = old_file_lines[:function_start - 1] + [inference_code_indent, '\n'] + old_file_lines[function_end:]
        with open(target_file_path, 'w', encoding='utf-8') as f:
            # f.writelines(file_lines)
            f.write(''.join(new_file_lines))
    except Exception as e:
        print(f"Meet error when execute test:\n{e}")
        subprocess.run(['mv', target_file_path_backup, target_file_path])
        return 'Error: before test'

    # Run the test case
    try:
        test_flag = adapter.test(project_path)
    except:
        # restore the original file status
        subprocess.run(['mv', target_file_path_backup, target_file_path])
        return 'Error: test'
    # restore the original file status
    subprocess.run(['mv', target_file_path_backup, target_file_path])
    return 'Pass' if test_flag == 'Plausible' else 'Fail'


def setup_evaluation(adapter: DatasetAdapter, project_name, dataset_bug_id, project_path) -> str:
    # First checkout teh project to bug-fixing snapshot
    try:
        checkout_flag = adapter.checkout(project_name, dataset_bug_id, project_path)
        print(f"after checkout, the current working directory is: {os.getcwd()}")
    except Exception as e:
        print(f"Meet error when checkout:\n{e}")
        return 'Error: checkout'
    if not checkout_flag:
        return 'Error: checkout'

    try:
        compile_flag = adapter.compile(project_path)
    except Exception as e:
        print(f"Meet error when compile:\n{e}")
        return 'Error: compile'
    if not compile_flag:
        return 'Error: compile'
    return "True"


def adjust_indent(code, new_indent):
    # remove original indentation
    dedent_code = textwrap.dedent(code)
    # add new indentation
    indented_code = textwrap.indent(dedent_code, ' ' * new_indent)
    return indented_code


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def handle_defects4j_special_cases(bug_meta_data, default_start, default_end):
    """Handle hardcoded function ranges for known Defects4J special cases."""
    project = bug_meta_data.get("project_name")
    defects4j_bug_id = str(bug_meta_data.get("defects4j_id"))

    if project == "jfreechart":
        special_cases = {
            "1": (1790, 1822),
            "9": (918, 956),
            "12": (143, 158),
            "13": (422, 489),
            "24": (123, 129),
        }
        return special_cases.get(defects4j_bug_id, (default_start, default_end))
    return default_start, default_end


if __name__ == '__main__':
    main()
