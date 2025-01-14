import json
import copy
import numpy as np
from argparse import ArgumentParser
from util import HistoryCategory
import matplotlib.pyplot as plt

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


def report_pass_at_k_hafix_70(evaluation_path, history_setting_list, k_list):
    n = 70
    neucleus_passed = {}
    neucleus_passed_array = {}
    pass_at_k_result = {}
    pass_at_k_each_bug = {}

    for bug_id_ in BUG_IDs:
        neucleus_passed[bug_id_] = 0
    for bug_id_ in BUG_IDs:
        neucleus_passed_array[bug_id_] = []

    for history_flag in history_setting_list:
        evaluate_path = f"{evaluation_path}/unittest_result_{HistoryCategory(history_flag).name}.json"
        eval_result_json: dict = json.load(open(evaluate_path, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
                    neucleus_passed_array[bug_id].append(1)
                else:
                    neucleus_passed_array[bug_id].append(0)

        # Get the keys from eval_result_json
        eval_result_keys = set(eval_result_json.keys())

        # Check for missing keys
        missing_keys = BUG_IDs - eval_result_keys

        # Create a new dictionary for missing keys with an array of seventy 0s
        for bug_id in missing_keys:
            neucleus_passed_array[bug_id].extend([0] * 10)

    # print(f'neucleus_passed total size: {len(neucleus_passed)}')
    # print(f'neucleus_passed: {neucleus_passed}')

    print(f'k value(hafix)')
    for k in k_list:
        pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
        pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
        print(f'{k} {pass_at_k_result[f"pass@{k}"]}')

    # print(f'bug_id pass@70(hafix)')
    # for bug_id_, pass_num in dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))).items():
    #     k_70 = 70
    #     pass_at_k_each_bug[bug_id_] = "{:.2%}".format(round(_compute_pass_at_k(n, pass_num, k_70), 4))
    #     print(f'{bug_id_} {pass_at_k_each_bug[bug_id_]}')

    # print(f'Evaluating hafix pass_at_k result: {pass_at_k_result}\n')
    return pass_at_k_result, dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))), dict(
        sorted(neucleus_passed_array.items(), key=lambda item: int(item[0])))


def report_pass_at_k_any_setting_70(evaluation_path, history_setting_num, k_list):
    n = 70
    neucleus_passed = {}
    neucleus_passed_array = {}
    pass_at_k_result = {}
    pass_at_k_each_bug = {}

    for bug_id_ in BUG_IDs:
        neucleus_passed[bug_id_] = 0
    for bug_id_ in BUG_IDs:
        neucleus_passed_array[bug_id_] = []

    for i in range(7):
        evaluate_path = f"{evaluation_path}/unittest_result_{HistoryCategory(history_setting_num).name}_{i}.json"
        eval_result_json: dict = json.load(open(evaluate_path, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
                    neucleus_passed_array[bug_id].append(1)
                else:
                    neucleus_passed_array[bug_id].append(0)

    # print(f'neucleus_passed total size: {len(neucleus_passed)}')
    # print(f'neucleus_passed_bug_2: {neucleus_passed}')

    print(f'k value')
    for k in k_list:
        pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
        pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
        print(f'{k} {pass_at_k_result[f"pass@{k}"]}')

    # print(f'bug_id pass@70(baseline)')
    # for bug_id_, pass_num in dict(sorted(neucleus_passed.items(), key=lambda item: int(item[0]))).items():
    #     k_70 = 70
    #     pass_at_k_each_bug[bug_id_] = "{:.2%}".format(round(_compute_pass_at_k(n, pass_num, k_70), 4))
    #     print(f'{bug_id_} {pass_at_k_each_bug[bug_id_]}')

    # print(f'Evaluating baseline pass_at_k result: {pass_at_k_result}\n')
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

        # print(f'neucleus_passed total size: {len(neucleus_passed)}')
        # print(f'neucleus_passed: {neucleus_passed}')

        print(f'history_flag={history_flag} k value')
        pass_at_k_result = {}
        for k in k_list:
            pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
            print(f'{k} {pass_at_k_result[f"pass@{k}"]}')
        pass_at_k_8_groups[history_flag] = pass_at_k_result
    return pass_at_k_8_groups


def report_pass_at_k_7_runs_for_stability_check(evaluation_path, history_setting_num, k_list):
    n = 10
    pass_at_k_7_groups = {}

    for i in range(7):
        neucleus_passed = {}
        for bug_id_ in BUG_IDs:
            neucleus_passed[bug_id_] = 0

        evaluate_path = f"{evaluation_path}/unittest_result_{HistoryCategory(history_setting_num).name}_{i}.json"
        eval_result_json: dict = json.load(open(evaluate_path, 'r'))
        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    neucleus_passed[bug_id] += 1
        print(f'run times {i:} k value')
        pass_at_k_result = {}
        for k in k_list:
            pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
            print(f'{k} {pass_at_k_result[f"pass@{k}"]}')
        pass_at_k_7_groups[i] = pass_at_k_result
    return pass_at_k_7_groups


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


def draw_pass_at_k_comparison_dynamic_groups(data_groups, labels, x_label='k Values', y_label='Pass@k (%)',
                                             save_filename='comparison.png'):
    """
    Draws a comparison plot for Pass@k results for multiple data groups.

    Parameters:
    - data_groups: List of dictionaries where keys are 'pass@k' and values are percentages (e.g., {"pass@1": "90%", ...}).
    - labels: List of labels for the data groups (e.g., ["HAFix", "Baseline", "FLN_all"]).
    - x_label: Label for the x-axis.
    - y_label: Label for the y-axis.
    - save_filename: Name of the file to save the plot as.
    """
    if len(data_groups) != len(labels):
        raise ValueError("The number of data groups must match the number of labels.")

    # Define a list of markers for variety
    markers = ['o', 's', '^', 'D', 'v', 'P', '*', 'X']
    if len(data_groups) > len(markers):
        raise ValueError("Too many data groups. Increase the variety of markers.")

    # Extract k values and convert x-tick labels to integers (e.g., 'pass@1' -> 1)
    k_values = list(data_groups[0].keys())  # Assuming all groups share the same keys
    k_ticks = [int(k.split('@')[1]) for k in k_values]

    plt.figure(figsize=(10, 6))

    # Plot each data group
    for data, label, marker in zip(data_groups, labels, markers):
        values = [float(v.strip('%')) for v in data.values()]
        plt.plot(k_ticks, values, label=f'{label}', marker=marker, markersize=4)

    # # Set x-ticks
    plt.xticks(k_ticks)
    if len(data_groups[0].keys()) == 70:
        k_ticks = [1] + list(range(5, max(k_ticks) + 1, 5))
    plt.xticks(k_ticks)

    # Add a subtle grid
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # Add labels and legend
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    ncol = 3
    if len(data_groups) > 3:
        ncol = 1
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=ncol)

    # Adjust layout to avoid clipping and set y-axis starting from 0
    plt.tight_layout()
    plt.ylim(0, None)

    # Save the plot
    plt.savefig(save_filename)
    plt.show()


def draw_individual_heuristics(data, labels=None, save_filename='comparison.png'):
    if labels is None:
        labels = ['Baseline', 'CFN-modified', 'CFN-all', 'FN-modified', 'FN-all', 'FLN-all', 'FN-pair', 'FL-diff']
    import pandas as pd
    import matplotlib.pyplot as plt

    # Define a list of markers for variety
    markers = ['o', 's', '^', 'D', 'v', 'P', '*', 'X']

    # Convert percentage strings to floats
    def convert_percentage_to_float(value):
        return float(value.strip('%'))

    # Transforming the data for plotting
    df_updated = pd.DataFrame.from_dict(data, orient='index')
    df_updated = df_updated.map(convert_percentage_to_float)

    # Convert the Pandas DataFrame to a NumPy array to avoid multi-dimensional indexing issues
    numpy_array = df_updated.to_numpy()

    # Labels for the groups

    # Plotting the updated data using the NumPy array
    plt.figure(figsize=(10, 6))
    for idx, (group, marker) in enumerate(zip(numpy_array, markers)):
        plt.plot(range(1, 11), group, label=labels[idx], marker=marker)  # Use a unique marker

    # Add labels and ticks
    plt.xlabel('k Values')
    plt.ylabel('Pass@k (%)')
    plt.xticks(range(1, 11))

    # Add a subtle grid
    plt.grid(visible=True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    # Add a legend
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2)

    # Set the y-axis to start from 0
    plt.ylim(0, None)

    # Save the plot as a high-resolution PNG file
    plt.savefig(save_filename, dpi=300, bbox_inches='tight')
    # Optionally, display the plot
    plt.show()


def verify_2_comparisons(first_dict, first_dict_real, second_dict, second_dict_real):
    first_binary_result = {key: (1 if value > 0 else 0) for key, value in first_dict.items()}
    second_binary_result = {key: (1 if value > 0 else 0) for key, value in second_dict.items()}
    print(f'Size: first: {len(first_binary_result)}, second: {len(second_binary_result)}')

    # Verify if the keys are the same
    if first_binary_result.keys() == second_binary_result.keys():
        print("key, first_value, second_value")
        for key in first_binary_result.keys():
            first_value = first_binary_result[key]
            second_value = second_binary_result[key]
            print(f"{key}   {first_value}   {second_value}")
    else:
        print("The keys of the two dictionaries are not the same.")

    print("==========================================================================================================")

    # Verify if the keys are the same
    if first_dict_real.keys() == second_dict_real.keys():
        print("key, first_value, second_value")
        for key in first_dict_real.keys():
            first_values = first_dict_real[key]
            second_values = second_dict_real[key]

            # Iterate through the arrays and print values
            # for first_value, second_value in zip(first_values, second_values):
            # print(f"{key}, {first_value}, {second_value}")
    else:
        print("The keys of the two dictionaries are not the same.")

    # Check the number of keys
    num_keys_first = len(first_dict_real)
    num_keys_second = len(second_dict_real)

    # Check if all values have a size of 51
    all_first_size_70 = all(len(value) == 70 for value in first_dict_real.values())
    all_second_size_70 = all(len(value) == 70 for value in second_dict_real.values())

    # Count how many values are not size 70
    not_size_70_first = sum(1 for value in first_dict_real.values() if len(value) != 70)
    not_size_70_second = sum(1 for value in second_dict_real.values() if len(value) != 70)

    # Count and store the sizes of values that are not size 70
    not_size_70_first_size = [len(value) for value in first_dict_real.values() if len(value) != 70]
    not_size_70_second_size = [len(value) for value in second_dict_real.values() if len(value) != 70]

    # Print results
    print(
        f"first Dict - Number of Keys: {num_keys_first}, All Values Size 70: {all_first_size_70}, Not Size 70: {not_size_70_first}, real size: {not_size_70_first_size}")
    print(
        f"second Dict - Number of Keys: {num_keys_second}, All Values Size 70: {all_second_size_70}, Not Size 70: {not_size_70_second}, real size: {not_size_70_second_size}")

    # Function to calculate total sum of all values in a dictionary
    def calculate_total_sum(data_dict):
        total_sum = 0
        for values in data_dict.values():
            total_sum += sum(values)  # Sum each list of values
        return total_sum

    # Calculate the total sums
    total_sum_first = calculate_total_sum(first_dict_real)
    total_sum_second = calculate_total_sum(second_dict_real)

    # Print the results
    print(f"Total sum in first_dict_real: {total_sum_first}")
    print(f"Total sum in second_dict_real: {total_sum_second}")


if __name__ == "__main__":
    # ==============================================   RQ1.1 HAFix & Baseline and   ===========================================================
    print('-------------------------------pass@k for HAFix in Instruction Prompt-------------------------------')
    evaluation_path_instruct = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct"
    only_history_settings = ['2', '3', '4', '5', '6', '7', '8']
    # k_list_70 = [1] + list(range(5, 71, 5))
    k_list_70 = list(range(1, 71))
    hafix_pass_at_k_result_instruct, hafix_dict_instruct, hafix_dict_real_instruct = report_pass_at_k_hafix_70(
        evaluation_path_instruct,
        only_history_settings, k_list_70)

    print('-------------------------------pass@k for Baseline in Instruction Prompt-------------------------------')
    evaluation_path_baseline_instruct = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct_baseline_70"
    baseline_setting = '1'
    baseline_pass_at_k_result_instruct, baseline_dict_instruct, baseline_dict_real_instruct = report_pass_at_k_any_setting_70(
        evaluation_path_baseline_instruct, baseline_setting, k_list_70)

    print('-------------------------------pass@k for FLN-all in Instruction Prompt-------------------------------')
    evaluation_path_FLN_all_instruct = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct_FLN_all_70"
    FLN_all_setting = '6'
    FLN_all_pass_at_k_result_instruct, FLN_all_dict_instruct, FLN_all_dict_real_instruct = report_pass_at_k_any_setting_70(
        evaluation_path_FLN_all_instruct, FLN_all_setting, k_list_70)

    draw_pass_at_k_comparison_dynamic_groups(
        data_groups=[hafix_pass_at_k_result_instruct, baseline_pass_at_k_result_instruct,
                     FLN_all_pass_at_k_result_instruct],
        labels=["HAFix-Agg", "Baseline", "FLN_all"],
        save_filename="hafix_baseline_FLN_all_comparison.png"
    )

    # # verify_2_comparisons(hafix_dict, hafix_dict_real, baseline_dict, baseline_dict_real)

    print('-------------------------------pass@k for baseline and individuals in Instruction Prompt-------------------------------')
    baseline_history_settings = ['1', '2', '3', '4', '5', '6', '7', '8']
    k_list_10 = list(range(1, 11))
    pass_at_k_8_groups_instruct = report_pass_at_k_individual_and_baseline(evaluation_path_instruct, baseline_history_settings, k_list_10)
    print(f'pass_at_k_8_groups_instruct\n: {pass_at_k_8_groups_instruct}')
    draw_individual_heuristics(pass_at_k_8_groups_instruct, save_filename='individuals_baseline_comparison(n=10).png')


    # ============================================================================   RQ2   ============================================================================
    evaluation_path_infill = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_infill"
    print('-------------------------------pass@k for baseline and individuals in InstructionMask Prompt-------------------------------')
    pass_at_k_8_groups_infill = report_pass_at_k_individual_and_baseline(evaluation_path_infill, baseline_history_settings, k_list_10)
    print(f'pass_at_k_8_groups_infill\n: {pass_at_k_8_groups_infill}')
    print('-------------------------------pass@k for HAFix in InstructionMask Prompt-------------------------------')
    hafix_pass_at_k_result_infill, hafix_dict_infill, hafix_dict_real_infill = report_pass_at_k_hafix_70(
        evaluation_path_infill,
        only_history_settings, k_list_70)

    # verify_2_comparisons(hafix_dict_instruct, hafix_dict_real_instruct, hafix_dict_infill, hafix_dict_real_infill)

    evaluation_path_instruct_label = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_instruct_labelled"
    print('-------------------------------pass@k for baseline and individuals in InstructionLabel Prompt-------------------------------')
    pass_at_k_8_groups_label = report_pass_at_k_individual_and_baseline(evaluation_path_instruct_label, baseline_history_settings, k_list_10)
    print(f'pass_at_k_8_groups_label\n: {pass_at_k_8_groups_label}')

    draw_pass_at_k_comparison_dynamic_groups(
        data_groups=[pass_at_k_8_groups_instruct['1'], pass_at_k_8_groups_label['1'], pass_at_k_8_groups_infill['1']],
        labels=["Baseline_Instruction", "Baseline_InstructionLabel", "Baseline_InstructionMask"],
        save_filename="baseline_3_prompts_comparison.png"
    )

    draw_pass_at_k_comparison_dynamic_groups(
        data_groups=[pass_at_k_8_groups_instruct['6'], pass_at_k_8_groups_label['6'], pass_at_k_8_groups_infill['6']],
        labels=["FLN_all_Instruction", "FLN_all_InstructionLabel", "FLN_all_InstructionMask"],
        save_filename="FLN_all_3_prompts_comparison.png"
    )

    print('-------------------------------pass@k for HAFix in InstructionLabel Prompt-------------------------------')
    hafix_pass_at_k_result_label, hafix_dict_label, hafix_dict_real_label = report_pass_at_k_hafix_70(
        evaluation_path_instruct_label,
        only_history_settings, k_list_70)

    # verify_2_comparisons(hafix_dict_instruct, hafix_dict_real_instruct, hafix_dict_label, hafix_dict_real_label)

    draw_pass_at_k_comparison_dynamic_groups(
        data_groups=[hafix_pass_at_k_result_instruct, hafix_pass_at_k_result_label, hafix_pass_at_k_result_infill],
        labels=["HAFix-Agg_Instruction", "HAFix-Agg_InstructionLabel", "HAFix-Agg_InstructionMask"],
        save_filename="hafix_3_prompts_comparison.png"
    )

    print('-------------------------------pass@k for Baseline in InstructionLabel Prompt-------------------------------')
    evaluation_path_baseline_label = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_label_baseline_70"
    baseline_pass_at_k_result_label, baseline_dict_label, baseline_dict_real_label = report_pass_at_k_any_setting_70(
        evaluation_path_baseline_label, baseline_setting, k_list_70)
    # verify_2_comparisons(hafix_dict_instruct, hafix_dict_real_instruct, baseline_dict_label, baseline_dict_real_label)

    draw_pass_at_k_comparison_dynamic_groups(
        data_groups=[
            hafix_pass_at_k_result_instruct,
            baseline_pass_at_k_result_instruct,
            baseline_pass_at_k_result_label,
            FLN_all_pass_at_k_result_instruct
        ],
        labels=["HAFix-Agg_Instruction", "Baseline_Instruction", "Baseline_InstructionLabel", "FLN_all_Instruction"],
        save_filename="hafix_2_baselines_1_FLN_all_comparison.png"
    )

    draw_pass_at_k_comparison_dynamic_groups(
        data_groups=[
            hafix_pass_at_k_result_instruct,
            baseline_pass_at_k_result_instruct,
            FLN_all_pass_at_k_result_instruct
        ],
        labels=["HAFix_Instruction", "Baseline_Instruction", "FLN_all_Instruction"],
        save_filename="hafix_1_baseline_1_FLN_all_comparison.png"
    )


    ## model stability check
    print('-------------------------------model stability check: pass@k for baseline in Instruction Prompt-------------------------------')
    k_list_10 = list(range(1, 11))
    pass_at_k_instruct_baseline_7_groups = report_pass_at_k_7_runs_for_stability_check(evaluation_path_baseline_instruct, baseline_setting, k_list_10)
    print(f'pass_at_k_instruct_baseline_7_groups\n: {pass_at_k_instruct_baseline_7_groups}')
    draw_individual_heuristics(pass_at_k_instruct_baseline_7_groups, labels=list(range(1, 8)), save_filename="baseline_7_times_instruct.png")


    # print('-------------------------------pass@k for Baseline in InstructionMask Prompt-------------------------------')
    # evaluation_path_baseline_infill = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_infill_baseline_70"
    # baseline_pass_at_k_result_infill, baseline_dict_infill, baseline_dict_real_infill = report_pass_at_k_any_setting_70(
    #     evaluation_path_baseline_infill, baseline_setting, k_list_70)
    # # verify_2_comparisons(hafix_dict_instruct, hafix_dict_real_instruct, baseline_dict_infill, baseline_dict_real_infill)
    #
    # print('-------------------------------pass@k for FLN-all in InstructionLabel Prompt-------------------------------')
    # evaluation_path_FLN_all_label = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_label_FLN_all_70"
    # FLN_all_pass_at_k_result_label, FLN_all_dict_label, FLN_all_dict_real_label = report_pass_at_k_any_setting_70(
    #     evaluation_path_FLN_all_label, FLN_all_setting, k_list_70)
    # # verify_2_comparisons(hafix_dict_instruct, hafix_dict_real_instruct, FLN_all_dict_label, FLN_all_dict_real_label)
    #
    # print('-------------------------------pass@k for FLN-all in InstructionMask Prompt-------------------------------')
    # evaluation_path_FLN_all_infill = "/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_infill_FLN_all_70"
    # FLN_all_pass_at_k_result_infill, FLN_all_dict_infill, FLN_all_dict_real_infill = report_pass_at_k_any_setting_70(
    #     evaluation_path_FLN_all_infill, FLN_all_setting, k_list_70)
    # # verify_2_comparisons(hafix_dict_instruct, hafix_dict_real_instruct, FLN_all_dict_infill, FLN_all_dict_real_infill)
    #
    # draw_pass_at_k_comparison_dynamic_groups(
    #     data_groups=[
    #         hafix_pass_at_k_result_instruct,
    #         baseline_pass_at_k_result_instruct,
    #         baseline_pass_at_k_result_label,
    #         baseline_pass_at_k_result_infill,
    #         FLN_all_pass_at_k_result_instruct,
    #         FLN_all_pass_at_k_result_label,
    #         FLN_all_pass_at_k_result_infill
    #     ],
    #     labels=["HAFix_Instruction", "Baseline_Instruction", "Baseline_InstructionLabel", "Baseline_InstructionMask",
    #             "FLN_all_Instruction", "FLN_all_InstructionLabel", "FLN_all_InstructionMask"],
    #     save_filename="hafix_3_baselines_FLN_alls_comparison.png"
    # )
    #
    # draw_pass_at_k_comparison_dynamic_groups(
    #     data_groups=[
    #         hafix_pass_at_k_result_instruct,
    #         baseline_pass_at_k_result_instruct,
    #         baseline_pass_at_k_result_label,
    #         baseline_pass_at_k_result_infill
    #     ],
    #     labels=["HAFix_Instruction", "Baseline_Instruction", "Baseline_InstructionLabel", "Baseline_InstructionMask"],
    #     save_filename="hafix_3_baselines_comparison.png"
    # )
