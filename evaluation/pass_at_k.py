import json
import copy
import os
import numpy as np
from argparse import ArgumentParser
from util import HistoryCategory, initialize_result_dict

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--dataset', type=str)
    parser.add_argument('--model_inference_dirs', type=str)
    parser.add_argument('--history_settings', type=str)
    parser.add_argument('--k_list', type=str, required=True, help="Comma-separated list of k values, e.g., '1,3,5,10'")
    return parser


args = get_parser().parse_args()
dataset_name = args.dataset


def main():
    k_list = [int(k) for k in args.k_list.split(',')]
    for model_inference_dir in args.model_inference_dirs.split(','):
        print(f'Evaluating pass_at_k result for {dataset_name} on {model_inference_dir}')
        for history_flag in args.history_settings.split(','):
            _evaluate_path = f"{CURRENT_DIR_PATH}/{dataset_name}/{model_inference_dir}"
            if not os.path.exists(_evaluate_path):
                raise ValueError(f'error: _evaluate_path {_evaluate_path} not exist!!')
            evaluate_file = f"{_evaluate_path}/unittest_result_{HistoryCategory(history_flag).name}.json"

            # calculate pass@k, when k=5 or 10, using nucleus sampling
            result_ = _evaluate_average_pass_at_k(evaluate_file, k_list)
            print(f'heuristic_{history_flag}: {result_}\n')

            pass_k_result_path = f"{_evaluate_path}/pass_k_result_{HistoryCategory(history_flag).name}.txt"
            pass_k_result = open(pass_k_result_path, 'a')
            pass_k_result.write(f'pass_at_k_final: {result_}\n')
            pass_k_result.close()


def _evaluate_average_pass_at_k(eval_result_path, k_list):
    pass_at_k_result = {}
    eval_result_json: dict = json.load(open(eval_result_path, 'r'))
    # if 1 in k_list:
    #     # first calculate pass@1 for greedy search
    #     n = 1
    #     k = 1
    #     greedy_passed = {}
    #
    #     for bug_id_ in BUG_IDs:
    #         greedy_passed[bug_id_] = 0
    #
    #     for bug_id, eval_result in eval_result_json.items():
    #         # if bug_id not in greedy_passed:
    #         #     greedy_passed[bug_id] = 0
    #         if eval_result['greedy_search_flag'] == 'Pass':
    #             greedy_passed[bug_id] += 1
    #     pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in greedy_passed.items()])
    #     # pass_at_k_result[f"pass@{k}"] = f"{pass_at_k * 100}%"
    #     pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))

    if len(set(k_list)) > 1:
        # second calculate pass@k for nucleus sampling
        k_list_temp = copy.deepcopy(k_list)
        # while 1 in k_list_temp:
        #     k_list_temp.remove(1)
        n = 10
        neucleus_passed, _ = initialize_result_dict(dataset_name)
        if neucleus_passed is None:
            return

        for bug_id, eval_result in eval_result_json.items():
            # if bug_id not in neucleus_passed:
            #     neucleus_passed[bug_id] = 0
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
        # print(f'neucleus_passed[bug_id]: {neucleus_passed}')
        for k in k_list_temp:
            pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
            # pass_at_k_result[f"pass@{k}"] = f"{pass_at_k * 100}%"
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
    return pass_at_k_result


def _compute_pass_at_k(n, c, k):
    """
    n: total number of samples per task
    c: number of samples that pass all tests
    k: k in pass@k
    """
    if n - c < k:
        return 1
    else:
        return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))


if __name__ == "__main__":
    main()