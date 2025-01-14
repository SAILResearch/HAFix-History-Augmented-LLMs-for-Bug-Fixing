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


def report_pass_at_k_hafix_140(evaluation_path_1_run, evaluation_path_2_run, history_setting_list, k_list):
    n = 140
    neucleus_passed = {}
    neucleus_passed_array = {}
    pass_at_k_result = {}
    pass_at_k_each_bug = {}

    for bug_id_ in BUG_IDs:
        neucleus_passed[bug_id_] = 0
    for bug_id_ in BUG_IDs:
        neucleus_passed_array[bug_id_] = []

    for history_flag in history_setting_list:
        evaluate_path = f"{evaluation_path_1_run}/unittest_result_{HistoryCategory(history_flag).name}.json"
        eval_result_json: dict = json.load(open(evaluate_path, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
                    neucleus_passed_array[bug_id].append(1)
                else:
                    neucleus_passed_array[bug_id].append(0)

        # second run
        evaluate_path_2 = f"{evaluation_path_2_run}/unittest_result_{HistoryCategory(history_flag).name}.json"
        eval_result_json_2: dict = json.load(open(evaluate_path_2, 'r'))
        for bug_id, eval_result in eval_result_json_2.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
                    neucleus_passed_array[bug_id].append(1)
                else:
                    neucleus_passed_array[bug_id].append(0)

        # Get the keys from eval_result_json
        eval_result_keys_1 = set(eval_result_json.keys())
        # Check for missing keys
        missing_keys_1 = BUG_IDs - eval_result_keys_1
        # Create a new dictionary for missing keys with an array of seventy 0s
        for bug_id in missing_keys_1:
            neucleus_passed_array[bug_id].extend([0] * 10)
        # Get the keys from eval_result_json
        eval_result_keys_2 = set(eval_result_json_2.keys())
        # Check for missing keys
        missing_keys_2 = BUG_IDs - eval_result_keys_2
        # Create a new dictionary for missing keys with an array of seventy 0s
        for bug_id in missing_keys_2:
            neucleus_passed_array[bug_id].extend([0] * 10)

    print(f'neucleus_passed total size: {len(neucleus_passed)}')
    print(f'neucleus_passed: {neucleus_passed}')

    # Check that the number of keys is 51
    assert len(neucleus_passed_array) == 51, f"Expected 51 keys, but got {len(neucleus_passed_array)}"
    # Check that each value (array) has 140 elements
    for key, value in neucleus_passed_array.items():
        assert len(value) == 140, f"Key {key} has {len(value)} values, but expected 140"

    print(f'\nk value(hafix)')
    for k in k_list:
        pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
        pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
        print(f'{k} {pass_at_k_result[f"pass@{k}"]}')

    print(f'\nbug_id pass@70(hafix)')
    for bug_id_, pass_num in dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))).items():
        k_70 = 70
        pass_at_k_each_bug[bug_id_] = "{:.2%}".format(round(_compute_pass_at_k(n, pass_num, k_70), 4))
        print(f'{bug_id_} {pass_at_k_each_bug[bug_id_]}')

    print(f'\nbug_id pass@140(hafix)')
    for bug_id_, pass_num in dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))).items():
        k_140 = 140
        pass_at_k_each_bug[bug_id_] = "{:.2%}".format(round(_compute_pass_at_k(n, pass_num, k_140), 4))
        print(f'{bug_id_} {pass_at_k_each_bug[bug_id_]}')

    print(f'\nEvaluating hafix pass_at_k result: {pass_at_k_result}\n')
    return pass_at_k_result, dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))), dict(
        sorted(neucleus_passed_array.items(), key=lambda item: int(item[0])))


def report_pass_at_k_baseline_140(evaluation_path_baseline, history_setting, k_list):
    n = 140
    neucleus_passed = {}
    neucleus_passed_array = {}
    pass_at_k_result = {}
    pass_at_k_each_bug = {}

    for bug_id_ in BUG_IDs:
        neucleus_passed[bug_id_] = 0
    for bug_id_ in BUG_IDs:
        neucleus_passed_array[bug_id_] = []

    for i in range(14):
        evaluate_path = f"{evaluation_path_baseline}/unittest_result_{HistoryCategory(history_setting).name}_{i}.json"
        eval_result_json: dict = json.load(open(evaluate_path, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
                    neucleus_passed_array[bug_id].append(1)
                else:
                    neucleus_passed_array[bug_id].append(0)

    print(f'neucleus_passed total size: {len(neucleus_passed)}')
    print(f'neucleus_passed_bug_2: {neucleus_passed}')

    # Check that the number of keys is 51
    assert len(neucleus_passed_array) == 51, f"Expected 51 keys, but got {len(neucleus_passed_array)}"
    # Check that each value (array) has 140 elements
    for key, value in neucleus_passed_array.items():
        assert len(value) == 140, f"Key {key} has {len(value)} values, but expected 140"

    print(f'k value(baseline)')
    for k in k_list:
        pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
        pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
        print(f'{k} {pass_at_k_result[f"pass@{k}"]}')

    print(f'bug_id pass@70(baseline)')
    for bug_id_, pass_num in dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))).items():
        k_70 = 70
        pass_at_k_each_bug[bug_id_] = "{:.2%}".format(round(_compute_pass_at_k(n, pass_num, k_70), 4))
        print(f'{bug_id_} {pass_at_k_each_bug[bug_id_]}')

    print(f'bug_id pass@140(baseline)')
    for bug_id_, pass_num in dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))).items():
        k_140 = 140
        pass_at_k_each_bug[bug_id_] = "{:.2%}".format(round(_compute_pass_at_k(n, pass_num, k_140), 4))
        print(f'{bug_id_} {pass_at_k_each_bug[bug_id_]}')

    print(f'Evaluating baseline pass_at_k result: {pass_at_k_result}\n')
    return pass_at_k_result, dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))), dict(
        sorted(neucleus_passed_array.items(), key=lambda item: int(item[0])))


def report_pass_at_k_individual_and_baseline(evaluation_path, history_setting_list, k_list):
    n = 10
    pass_at_k_8_groups = {}

    for history_flag in history_setting_list:
        neucleus_passed = {}
        for bug_id_ in BUG_IDs:
            neucleus_passed[bug_id_] = 0

        evaluate_path = f"{evaluation_path}/unittest_result_{HistoryCategory(history_flag).name}.json"
        eval_result_json: dict = json.load(open(evaluate_path, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1

        print(f'neucleus_passed total size: {len(neucleus_passed)}')
        print(f'neucleus_passed: {neucleus_passed}')

        pass_at_k_result = {}
        for k in k_list:
            pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
            print(f'{k} {pass_at_k_result[f"pass@{k}"]}')
        pass_at_k_8_groups[history_flag] = pass_at_k_result
    return pass_at_k_8_groups


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


def draw_hafix_baseline_diff(hafix_pass_at_k_result, baseline_pass_at_k_result):
    import matplotlib.pyplot as plt
    # Convert percentage strings to floats for plotting
    hafix_values = [float(v.strip('%')) for v in hafix_pass_at_k_result.values()]
    baseline_values = [float(v.strip('%')) for v in baseline_pass_at_k_result.values()]
    k_values = list(hafix_pass_at_k_result.keys())

    # Convert x-tick labels (e.g. 'pass@1') to just the numeric values (e.g. 1, 5, 10...)
    k_ticks = [int(k.split('@')[1]) for k in k_values]

    # Plotting the data
    plt.figure(figsize=(10, 6))
    plt.plot(k_ticks, hafix_values, label='HAFix Pass@k', marker='o', color='b')
    plt.plot(k_ticks, baseline_values, label='Baseline Pass@k', marker='s', color='r')

    # Manually set the x-tick values to show only 1, 5, 10, 15, ..., 70
    plt.xticks(k_ticks)

    # Adding custom x-axis label
    plt.xlabel('k Values')

    # Adding labels and title
    plt.ylabel('Pass@k (%)')
    plt.title('Pass@k Comparison of HAFix and Baseline Using Nucleus Sampling (n=140).')
    plt.legend()

    # Adjust layout to avoid clipping of labels
    plt.tight_layout()

    # Save the plot as a PNG file
    plt.savefig('hafix_baseline_comparison_140.png')

    # Optionally, display the plot
    plt.show()


def draw_individuals_and_baseline(data):
    import pandas as pd
    import matplotlib.pyplot as plt
    # Convert percentage strings to floats
    def convert_percentage_to_float(value):
        return float(value.strip('%'))

    # Transforming the data for plotting
    df_updated = pd.DataFrame.from_dict(data, orient='index')
    df_updated = df_updated.map(convert_percentage_to_float)

    # Convert the Pandas DataFrame to a NumPy array to avoid multi-dimensional indexing issues
    numpy_array = df_updated.to_numpy()

    # Labels for the groups
    group_labels = ['Baseline', 'CFN-modified', 'CFN-all', 'FN-modified', 'FN-all', 'FLN-all', 'FN-pair', 'FL-diff']

    # Plotting the updated data using the NumPy array
    plt.figure(figsize=(10, 6))
    for idx, group in enumerate(numpy_array):
        plt.plot(range(1, 11), group, label=group_labels[idx], marker='o')

    plt.xlabel('k Values')
    plt.ylabel('Pass@k (%)')
    plt.title('Pass@k Comparison of Individual Heuristics and Baseline Using Nucleus Sampling (n=10).')
    plt.xticks(range(1, 11))
    plt.legend()
    plt.grid(True)

    # Save the plot as a PNG file
    plt.savefig('individuals_baseline_comparison(n=10).png')
    # Optionally, display the plot
    plt.show()


if __name__ == "__main__":
    evaluation_path_hafix_1 = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct"
    evaluation_path_hafix_2 = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct_2nd_run_individual"

    history_settings = ['2', '3', '4', '5', '6', '7', '8']
    k_list = [1] + list(range(5, 141, 5))
    hafix_pass_at_k_result, hafix_dict, hafix_dict_real = report_pass_at_k_hafix_140(evaluation_path_hafix_1, evaluation_path_hafix_2, history_settings, k_list)

    evaluation_path_baseline = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct_baseline_70"
    baseline_setting = '1'
    baseline_pass_at_k_result, baseline_dict, baseline_dict_real = report_pass_at_k_baseline_140(
        evaluation_path_baseline, baseline_setting, k_list)

    draw_hafix_baseline_diff(hafix_pass_at_k_result, baseline_pass_at_k_result)

    hafix_binary_result = {key: (1 if value > 0 else 0) for key, value in hafix_dict.items()}
    baseline_binary_result = {key: (1 if value > 0 else 0) for key, value in baseline_dict.items()}
    print(f'Size: hafix: {len(hafix_binary_result)}, baseline: {len(baseline_binary_result)}')

    # Verify if the keys are the same
    if hafix_binary_result.keys() == baseline_binary_result.keys():
        print("key, hafix_value, baseline_value")
        for key in hafix_binary_result.keys():
            hafix_value = hafix_binary_result[key]
            baseline_value = baseline_binary_result[key]
            print(f"{key}   {hafix_value}   {baseline_value}")
    else:
        print("The keys of the two dictionaries are not the same.")

    print("==========================================================================================================")

    # Verify if the keys are the same
    if hafix_dict_real.keys() == baseline_dict_real.keys():
        print("key, hafix_value, baseline_value")
        for key in hafix_dict_real.keys():
            hafix_values = hafix_dict_real[key]
            baseline_values = baseline_dict_real[key]

            # Iterate through the arrays and print values
            # for hafix_value, baseline_value in zip(hafix_values, baseline_values):
            # print(f"{key}, {hafix_value}, {baseline_value}")
    else:
        print("The keys of the two dictionaries are not the same.")

    # Check the number of keys
    num_keys_hafix = len(hafix_dict_real)
    num_keys_baseline = len(baseline_dict_real)

    # Check if all values have a size of 51
    all_hafix_size_70 = all(len(value) == 140 for value in hafix_dict_real.values())
    all_baseline_size_70 = all(len(value) == 140 for value in baseline_dict_real.values())

    # Count how many values are not size 70
    not_size_70_hafix = sum(1 for value in hafix_dict_real.values() if len(value) != 70)
    not_size_70_baseline = sum(1 for value in baseline_dict_real.values() if len(value) != 70)

    # Count and store the sizes of values that are not size 70
    not_size_70_hafix_size = [len(value) for value in hafix_dict_real.values() if len(value) != 70]
    not_size_70_baseline_size = [len(value) for value in baseline_dict_real.values() if len(value) != 70]

    # Print results
    print(
        f"Hafix Dict - Number of Keys: {num_keys_hafix}, All Values Size 70: {all_hafix_size_70}, Not Size 70: {not_size_70_hafix}, real size: {not_size_70_hafix_size}")
    print(
        f"Baseline Dict - Number of Keys: {num_keys_baseline}, All Values Size 70: {all_baseline_size_70}, Not Size 70: {not_size_70_baseline}, real size: {not_size_70_baseline_size}")


    # Function to calculate total sum of all values in a dictionary
    def calculate_total_sum(data_dict):
        total_sum = 0
        for values in data_dict.values():
            total_sum += sum(values)  # Sum each list of values
        return total_sum


    # Calculate the total sums
    total_sum_hafix = calculate_total_sum(hafix_dict_real)
    total_sum_baseline = calculate_total_sum(baseline_dict_real)

    # Print the results
    print(f"Total sum in hafix_dict_real: {total_sum_hafix}")
    print(f"Total sum in baseline_dict_real: {total_sum_baseline}")

    # evaluation_path = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct"
    # history_settings = ['1', '2', '3', '4', '5', '6', '7', '8']
    # k_list = list(range(1, 11))
    # pass_at_k_8_groups = report_pass_at_k_individual_and_baseline(evaluation_path, history_settings, k_list)
    # print(f'pass_at_k_8_groups\n: {pass_at_k_8_groups}')
    # draw_individuals_and_baseline(pass_at_k_8_groups)
