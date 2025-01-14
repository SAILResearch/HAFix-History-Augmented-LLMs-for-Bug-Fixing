import json
import copy
import numpy as np
from argparse import ArgumentParser
from util import HistoryCategory

BUG_IDs = {'2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '16', '17', '18', '19', '20', '21', '22', '23', '24',
           '25', '26', '27', '28', '29', '30', '31', '32', '33', '35', '36', '37', '38', '41', '42', '43', '44', '45',
           '46', '47', '48', '49', '50', '51', '52', '53', '54', '60', '61', '66', '67', '68'}


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--evaluation_path', type=str)
    parser.add_argument('--history_settings', type=str)
    parser.add_argument('--has_nucleus_sampling', type=str)
    return parser


args = get_parser().parse_args()


def report_pass_at_k_result(evaluation_path, history_setting_list, do_nucleus_sampling):
    # has_nucleus_sampling = bool(int(args.has_nucleus_sampling))
    if do_nucleus_sampling:
        k_list = [1, 3, 5, 10]
    else:
        k_list = [1]

    for history_flag in history_setting_list:
        evaluate_path = f"{evaluation_path}/unittest_result_{HistoryCategory(history_flag).name}.json"

        # calculate pass@k, when k=5 or 10, using nucleus sampling
        result_ = _evaluate_average_pass_at_k(evaluate_path, k_list)
        print(f'Evaluating pass_at_k result: {result_}\n')

        pass_k_result_path = f"{evaluation_path}/pass_k_result_{HistoryCategory(history_flag).name}.txt"
        pass_k_result = open(pass_k_result_path, 'a')
        pass_k_result.write(f'adjust pass_at_k_final: {result_}\n')
        pass_k_result.close()


def _evaluate_average_pass_at_k(eval_result_path, k_list):
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
        pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in greedy_passed.items()])
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
        print(f'neucleus_passed[bug_id]: {neucleus_passed}')
        for k in k_list_temp:
            pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
            # pass_at_k_result[f"pass@{k}"] = f"{pass_at_k * 100}%"
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
    return pass_at_k_result


def _compute_pass_at_k(n, c, k):
    """
    n: total number of completions per task
    c: number of completions that pass all tests
    k: k in pass_at_k
    """
    if n - c < k:
        return 1
    else:
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


if __name__ == "__main__":
    evaluation_path = args.evaluation_path
    history_settings = args.history_settings.split(',')
    has_nucleus_sampling = bool(int(args.has_nucleus_sampling))
    report_pass_at_k_result(evaluation_path, history_settings, has_nucleus_sampling)
