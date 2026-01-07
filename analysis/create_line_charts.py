import json
import os
from collections import defaultdict
import numpy as np
import pandas as pd
from argparse import ArgumentParser
from util import HistoryCategory, initialize_result_dict, PromptCategory, get_model_and_prompt_enum
import matplotlib.pyplot as plt
from matplotlib import colormaps

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
RQ_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, 'RQ1_2'))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))
EVALUATION_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup/evaluation'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--datasets', type=str)
    parser.add_argument('--evaluation_dirs', type=str)
    return parser


name_map = {
    "bugsinpy": "bpy",
    "defects4j": "d4j",

    "codellama_7b": "cl",
    "deepseek_coder_6.7b": "dsc",
    "deepseek_coder_v2": "dsc2",

    "Instruction": "inst",
    "InstructionLabel": "instl",
    "InstructionMask": "instm"
}


def main():
    args = get_parser().parse_args()
    # debug
    # args.datasets = 'bugsinpy'
    # args.evaluation_dirs = 'codellama_7b_instruct_fp16_Instruction,codellama_7b_instruct_fp16_InstructionLabel,codellama_7b_instruct_fp16_InstructionMask'
    for dataset_name in args.datasets.split(','):
        output_path_dataset = os.path.join(RQ_BASE, dataset_name)
        os.makedirs(output_path_dataset, exist_ok=True)
        # RQ1
        baseline_hafix_compare_all_models = defaultdict(dict)
        # RQ2
        baseline_prompt_styles_compare = defaultdict(dict)
        hafix_prompt_styles_compare = defaultdict(dict)

        for evaluation_dir in args.evaluation_dirs.split(','):
            # first parse the model name and prompt style
            model_name_enum, prompt_style_enum = get_model_and_prompt_enum(evaluation_dir)
            model_name, prompt_style = model_name_enum.value, prompt_style_enum.value
            if not model_name or not prompt_style:
                print(f"the evaluation_dir is not a valid path name: {evaluation_dir}")
                continue

            output_path_model = os.path.join(output_path_dataset, evaluation_dir)
            os.makedirs(output_path_model, exist_ok=True)

            evaluation_path = f"{EVALUATION_BASE_PATH}/{dataset_name}/{evaluation_dir}"
            evaluation_path_repeat_60 = f"{EVALUATION_BASE_PATH}/{dataset_name}_repeat/{dataset_name}/{evaluation_dir}"
            only_history_settings = ['2', '3', '4', '5', '6', '7', '8']
            baseline_and_history_settings = ['1', '2', '3', '4', '5', '6', '7', '8']
            baseline_flag = '1'
            hafix_agg_flag = '0'
            k_list_70 = list(range(1, 71))
            k_list_10 = list(range(1, 11))

            # ====== RQ1: HAFix & Baseline and ======
            # RQ1.1 pass@k for baseline and history heuristics
            pass_at_k_baseline_and_heuristics = report_pass_at_k_baseline_and_heuristics(
                evaluation_path, baseline_and_history_settings, k_list_10, dataset_name)
            # save the result to csv
            save_pass_at_k_to_csv(pass_at_k_baseline_and_heuristics, save_file_path=os.path.join(
                output_path_model,
                f"hafix_pass_at_k.csv")
            )

            # First generate all figures, then set fixed_y_max_label=50 for unifying multiple figures based on observation of maximum y value
            draw_pass_at_k_comparison_dynamic_groups(
                data_groups=[pass_at_k_baseline_and_heuristics[history_flag] for history_flag in baseline_and_history_settings],
                labels=[HistoryCategory(history_flag).short_name for history_flag in baseline_and_history_settings],
                fixed_y_max_label=50,
                save_file_path=os.path.join(
                    output_path_model,
                    f'rq1_baseline_heuristics_comparison_{name_map.get(dataset_name)}_{name_map.get(model_name)}_{name_map.get(prompt_style)}.png'),
                has_separate_legend=True,
                font_size=22,
                legend_font_size=20,
                tick_font_size=20
            )

            # RQ1.2 pass@k for HAFix and baseline on 70 samples
            pass_at_k_hafix, _, _ = report_pass_at_k_hafix(evaluation_path, only_history_settings, k_list_70, dataset_name)

            # Only for Instruction prompt style, need to compare the baseline with HAFix when sample = 70
            if prompt_style == PromptCategory.instruction.value:
                pass_at_k_baseline_70, _, _ = report_pass_at_k_any_setting_70(
                    evaluation_path, evaluation_path_repeat_60, baseline_flag, k_list_70, dataset_name
                )
                # save the result to csv
                save_pass_at_k_to_csv(pass_at_k_result_dict={HistoryCategory.baseline.value: pass_at_k_baseline_70,
                                                             HistoryCategory.hafix_agg.value: pass_at_k_hafix},
                                      save_file_path=os.path.join(output_path_model, "hafix_pass_at_k_70.csv"))

                # discussion: run baseline multiple times check
                pass_at_k_7_groups = report_pass_at_k_7_runs_for_stability_check(
                    evaluation_path, evaluation_path_repeat_60, baseline_flag, k_list_10, dataset_name
                )
                save_pass_at_k_to_csv(pass_at_k_result_dict=pass_at_k_7_groups,
                                      save_file_path=os.path.join(output_path_model, "baseline_pass_at_k_10_7_groups.csv"))

                # First generate all figures, then set fixed_y_max_label=70 for unifying multiple figures based on observation of maximum y value
                # draw_pass_at_k_comparison_dynamic_groups(
                #     data_groups=[pass_at_k_hafix, pass_at_k_baseline_70],
                #     labels=[HistoryCategory(hafix_agg_flag).short_name, HistoryCategory(baseline_flag).short_name],
                #     fixed_y_max_label=70,
                #     save_file_path=os.path.join(
                #         output_path_model,
                #         f'rq1_baseline_hafix_comparison_{name_map.get(dataset_name)}_{name_map.get(model_name)}_{name_map.get(prompt_style)}.png')
                # )

                # RQ1.3_1 pass@k for HAFix and baseline on 70 samples for each dataset, first collect them 2 datasets * 3 models * 1 prompt style
                baseline_hafix_compare_all_models[f"{HistoryCategory(baseline_flag).short_name}_{model_name}"] = pass_at_k_baseline_70
                baseline_hafix_compare_all_models[f"{HistoryCategory(hafix_agg_flag).short_name}_{model_name}"] = pass_at_k_hafix

            # RQ2 Prompt style comparison for baseline, HAFix-Agg
            pass_at_k_baseline_10 = pass_at_k_baseline_and_heuristics[baseline_flag]

            if model_name and prompt_style:
                baseline_prompt_styles_compare[model_name][prompt_style] = pass_at_k_baseline_10
                hafix_prompt_styles_compare[model_name][prompt_style] = pass_at_k_hafix

        # RQ1.3_2 generate based on RQ1.3.1
        # save the result to csv
        save_pass_at_k_to_csv(pass_at_k_result_dict=baseline_hafix_compare_all_models,
                              save_file_path=os.path.join(output_path_dataset, "baseline_hafix_pass_at_k_70_all_models.csv"))
        # First generate all figures, then set fixed_y_max_label=70 for unifying multiple figures based on observation of maximum y value
        # Sort the dict, 3 baseline first then 3 HAFix-Agg
        baseline_hafix_compare_all_models_sort = dict(
            sorted(baseline_hafix_compare_all_models.items(), key=lambda x: (not x[0].startswith(HistoryCategory(baseline_flag).short_name), x[0])))
        # print(f"baseline_hafix_compare_all_models_sort.keys(): \n{baseline_hafix_compare_all_models_sort.keys()}")
        draw_pass_at_k_comparison_dynamic_groups(
            data_groups=list(baseline_hafix_compare_all_models_sort.values()),
            labels=list(baseline_hafix_compare_all_models_sort.keys()),
            fixed_y_max_label=70,
            save_file_path=os.path.join(
                output_path_dataset,
                f'rq1_baseline_hafix_agg_comparison_{name_map.get(dataset_name)}_{name_map.get(PromptCategory.instruction.value)}.png'),
            pairwise=True
        )

        # RQ2.1 baseline comparison for different prompt styles
        for model_name, prompt_style_result in baseline_prompt_styles_compare.items():
            baseline_prompt_styles = defaultdict(dict)
            for prompt_style, pass_at_k in prompt_style_result.items():
                baseline_prompt_styles[f"{HistoryCategory.baseline.short_name}_{prompt_style}"] = pass_at_k
            # save the result to csv
            save_pass_at_k_to_csv(pass_at_k_result_dict=baseline_prompt_styles,
                                  save_file_path=os.path.join(output_path_dataset, f"baseline_prompt_styles_pass_at_k_{model_name}.csv"))
            # First generate all figures, then set fixed_y_max_label=50 for unifying multiple figures based on observation of maximum y value
            draw_pass_at_k_comparison_dynamic_groups(
                data_groups=list(baseline_prompt_styles.values()),
                labels=list(baseline_prompt_styles.keys()),
                fixed_y_max_label=50,
                save_file_path=os.path.join(
                    output_path_dataset,
                    f'rq2_baseline_comparison_prompt_styles_{name_map.get(dataset_name)}_{name_map.get(model_name)}.png'),
                has_separate_legend=True,
                font_size=22,
                legend_font_size=20,
                tick_font_size=20,
                legend_save_file_path=os.path.join(
                    output_path_dataset,
                    "legend_separate_rq2_baseline_prompt_styles.png")
            )

        # RQ2.2 hafix-agg comparison for different prompt styles
        for model_name, prompt_style_result in hafix_prompt_styles_compare.items():
            hafix_prompt_styles = defaultdict(dict)
            for prompt_style, pass_at_k in prompt_style_result.items():
                hafix_prompt_styles[f"{HistoryCategory.hafix_agg.short_name}_{prompt_style}"] = pass_at_k
            # save the result to csv
            save_pass_at_k_to_csv(pass_at_k_result_dict=hafix_prompt_styles,
                                  save_file_path=os.path.join(output_path_dataset, f"hafix_prompt_styles_pass_at_k_{model_name}.csv"))
            # First generate all figures, then set fixed_y_max_label=70 for unifying multiple figures based on observation of maximum y value
            draw_pass_at_k_comparison_dynamic_groups(
                data_groups=list(hafix_prompt_styles.values()),
                labels=list(hafix_prompt_styles.keys()),
                fixed_y_max_label=70,
                save_file_path=os.path.join(
                    output_path_dataset,
                    f'rq2_hafix_agg_comparison_prompt_styles_{name_map.get(dataset_name)}_{name_map.get(model_name)}.png'),
                has_separate_legend=True,
                font_size=22,
                legend_font_size=20,
                tick_font_size=20,
                legend_save_file_path=os.path.join(
                    output_path_dataset,
                    "legend_separate_rq2_hafix_prompt_styles.png"),
                legend_marker_size=0
            )


def report_pass_at_k_baseline_and_heuristics(evaluation_path, history_setting_list, k_list, dataset):
    n = 10
    pass_at_k_8_groups = {}

    for history_flag in history_setting_list:
        nucleus_passed, nucleus_passed_array = initialize_result_dict(dataset)

        evaluate_file = f"{evaluation_path}/unittest_result_{HistoryCategory(history_flag).name}.json"
        eval_result_json: dict = json.load(open(evaluate_file, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    nucleus_passed[bug_id] += 1
                    nucleus_passed_array[bug_id].append(1)
                else:
                    nucleus_passed_array[bug_id].append(0)

        # Final sanity check: each bug_id should have 70 entries
        for bug_id, arr in nucleus_passed_array.items():
            if len(arr) != n:
                raise ValueError(f"Bug {bug_id} has {len(arr)} samples in total, expected {n}.")

        # print(f'history_flag={history_flag} k value')
        pass_at_k_result = {}
        for k in k_list:
            pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in nucleus_passed.items()])
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
            # print(f'{k} {pass_at_k_result[f"pass@{k}"]}')
        pass_at_k_8_groups[history_flag] = pass_at_k_result
    return pass_at_k_8_groups


def report_pass_at_k_hafix(evaluation_path, history_setting_list, k_list, dataset):
    n = 70
    pass_at_k_result = {}
    nucleus_passed, nucleus_passed_array = initialize_result_dict(dataset)

    for history_flag in history_setting_list:
        evaluate_file = f"{evaluation_path}/unittest_result_{HistoryCategory(history_flag).name}.json"
        eval_result_json: dict = json.load(open(evaluate_file, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    nucleus_passed[bug_id] += 1
                    nucleus_passed_array[bug_id].append(1)
                else:
                    nucleus_passed_array[bug_id].append(0)

        # Get the keys from eval_result_json
        eval_result_keys = set(eval_result_json.keys())

        # Check for missing keys
        missing_keys = [bug_id for bug_id in nucleus_passed.keys() if bug_id not in eval_result_keys]

        # Create a new dictionary for missing keys with an array of seventy 0s
        # for bug_id in missing_keys:
        #     nucleus_passed_array[bug_id].extend([0] * 70)
        if len(missing_keys) > 0:
            print(f"error: there is missing keys in {evaluation_path}, {dataset}, {history_flag}")
            return None, None, None

    # Final sanity check: each bug_id should have 70 entries
    for bug_id, arr in nucleus_passed_array.items():
        if len(arr) != n:
            raise ValueError(f"Bug {bug_id} has {len(arr)} samples in total, expected {n}.")

    # print(f'k value(hafix)')
    for k in k_list:
        pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in nucleus_passed.items()])
        pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
        # print(f'{k} {pass_at_k_result[f"pass@{k}"]}')

    return pass_at_k_result, dict(sorted(nucleus_passed.items(), key=lambda item: int(item[0]))), dict(
        sorted(nucleus_passed_array.items(), key=lambda item: int(item[0])))


def report_pass_at_k_any_setting_70(evaluation_path_10, evaluation_path_60, history_setting_flag, k_list, dataset):
    n = 70
    pass_at_k_result = {}
    nucleus_passed, nucleus_passed_array = initialize_result_dict(dataset)

    for evaluation_path in [evaluation_path_10, evaluation_path_60]:
        evaluate_file = f"{evaluation_path}/unittest_result_{HistoryCategory(history_setting_flag).name}.json"
        eval_result_json: dict = json.load(open(evaluate_file, 'r'))

        for bug_id, eval_result in eval_result_json.items():
            for value in eval_result['nucleus_sampling_flags']:
                if value == 'Pass':
                    nucleus_passed[bug_id] += 1
                    nucleus_passed_array[bug_id].append(1)
                else:
                    nucleus_passed_array[bug_id].append(0)

    # Final sanity check: each bug_id should have 70 entries
    for bug_id, arr in nucleus_passed_array.items():
        if len(arr) != n:
            raise ValueError(f"Bug {bug_id} has {len(arr)} samples in total, expected {n}.")

    # print(f'k value')
    for k in k_list:
        pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in nucleus_passed.items()])
        pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
        # print(f'{k} {pass_at_k_result[f"pass@{k}"]}')

    # print(f'Evaluating baseline pass_at_k result: {pass_at_k_result}\n')
    return pass_at_k_result, dict(sorted(nucleus_passed.items(), key=lambda item: int(item[0]))), dict(
        sorted(nucleus_passed_array.items(), key=lambda item: int(item[0])))


def report_pass_at_k_7_runs_for_stability_check(evaluation_path_10, evaluation_path_60, history_setting_flag, k_list, dataset):
    n = 10
    pass_at_k_7_groups = {}
    _, neucleus_passed_array_70 = initialize_result_dict(dataset)

    # Process both evaluation paths
    for evaluation_path in [evaluation_path_10, evaluation_path_60]:
        evaluate_file = f"{evaluation_path}/unittest_result_{HistoryCategory(history_setting_flag).name}.json"
        eval_result_json: dict = json.load(open(evaluate_file, 'r'))
        for bug_id, eval_result in eval_result_json.items():
            nucleus_flags = eval_result['nucleus_sampling_flags']
            neucleus_passed_array_70[bug_id].extend(nucleus_flags)

    # Verify each bug has exactly 70 samples
    for bug_id, samples in neucleus_passed_array_70.items():
        assert len(samples) == 70, f"Bug {bug_id} has {len(samples)} samples, expected 70"

    # Split into 7 groups of 10 samples each
    for group_idx in range(7):
        start_idx = group_idx * 10
        end_idx = start_idx + 10
        # Initialize result dict for this group
        neucleus_passed, _ = initialize_result_dict(dataset)

        # Count passes for each bug in this group
        for bug_id in neucleus_passed.keys():
            group_samples = neucleus_passed_array_70[bug_id][start_idx:end_idx]
            neucleus_passed[bug_id] = sum(1 for flag in group_samples if flag == 'Pass')

        pass_at_k_result = {}
        # Calculate pass@k for each k value
        for k in k_list:
            pass_at_k = np.mean([_compute_pass_at_k(n, pass_num, k) for _, pass_num in neucleus_passed.items()])
            pass_at_k_result[f"pass@{k}"] = "{:.2%}".format(round(pass_at_k, 4))
        pass_at_k_7_groups[f"run_{group_idx+1}"] = pass_at_k_result
    return pass_at_k_7_groups


def save_pass_at_k_to_csv(pass_at_k_result_dict, save_file_path):
    """
    Save the result from report_pass_at_k_baseline_and_heuristics to a CSV file.

    Args:
        pass_at_k_result_dict (dict): The dictionary returned from report_pass_at_k_baseline_and_heuristics.
        save_file_path (str or Path): The file path where the CSV should be saved.
    """
    # Convert the nested dict to a pandas DataFrame
    df = pd.DataFrame.from_dict(pass_at_k_result_dict, orient='index')
    # Transpose: rows become pass@k, columns become setting_ids
    df_reshaped = df.transpose()
    df_reshaped.columns = [f"setting_{col}" for col in df_reshaped.columns]
    # # Optionally, sort the index if desired
    df_reshaped.index.name = "pass@k"
    # Save to CSV
    df_reshaped.to_csv(save_file_path)
    print(f"Saved: {save_file_path}")


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


def draw_pass_at_k_comparison_dynamic_groups(data_groups, labels, x_label='K values', y_label='Pass@k (%)', fixed_y_max_label=None,
                                             save_file_path='comparison.png', dpi=300, pairwise=False, has_separate_legend=False,
                                             font_size=None, legend_font_size=None, tick_font_size=None,
                                             legend_save_file_path=None, legend_marker_size=None):
    """
    Draws a comparison plot for Pass@k results for multiple data groups.

    Parameters:
    - data_groups: List of dictionaries where keys are 'pass@k' and values are percentages (e.g., {"pass@1": "90%", ...}).
    - labels: List of labels for the data groups (e.g., ["HAFix-Agg", "Baseline"]).
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

    # plt.figure(figsize=(10, 6))
    fig, ax = plt.subplots(figsize=(10, 6))

    marker_size = 5 if len(k_values) <= 10 else 0
    # Plot each data group
    if not pairwise:
        for data, label, marker in zip(data_groups, labels, markers):
            values = [float(v.strip('%')) for v in data.values()]
            ax.plot(k_ticks, values, label=f'{label}', marker=marker, markersize=marker_size)
    else:
        num_models = len(data_groups) // 2
        baseline_groups = data_groups[:num_models]
        hafix_groups = data_groups[num_models:]
        baseline_labels = labels[:num_models]
        hafix_labels = labels[num_models:]
        colors = colormaps['tab10'].colors
        for i in range(num_models):
            baseline_values = [float(v.strip('%')) for v in baseline_groups[i].values()]
            # Plot baseline (no marker)
            ax.plot(k_ticks, baseline_values, label=baseline_labels[i], color=colors[i], marker='P', markersize=0)
        for i in range(num_models):
            hafix_values = [float(v.strip('%')) for v in hafix_groups[i].values()]
            # Plot HAFix (with marker)
            ax.plot(k_ticks, hafix_values, label=hafix_labels[i], color=colors[i], marker='P', markersize=5)

    # # Set x-ticks
    ax.set_xticks(k_ticks)
    if len(data_groups[0].keys()) == 70:
        ax.set_xticks([1] + list(range(5, max(k_ticks) + 1, 5)))

    # Add a subtle grid
    ax.grid(visible=True, which='both', linestyle='-', linewidth=0.5, alpha=0.7)

    # Add labels and legend
    ax.set_xlabel(x_label, fontweight='bold', fontsize=font_size)
    ax.set_ylabel(y_label, fontweight='bold', fontsize=font_size)

    if tick_font_size is None:
        tick_font_size = font_size
    if tick_font_size is not None:
        ax.tick_params(axis='both', labelsize=tick_font_size)

    # when what to merge line charts together with one separate legend
    handles, legend_labels = ax.get_legend_handles_labels()
    ncol = 3 if len(legend_labels) <= 3 else 2

    if legend_font_size is None:
        legend_font_size = font_size
    if not has_separate_legend:
        fig.legend(handles, legend_labels,
                   loc='upper center', bbox_to_anchor=(0.52, 0.05), ncol=ncol, fontsize=legend_font_size)
    # plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=ncol)

    # Adjust y maximum value labeled in y axis
    if fixed_y_max_label is not None:
        ax.set_ylim(0, fixed_y_max_label)
    else:
        ax.set_ylim(0, None)

    # Adjust layout to avoid clipping and set y-axis starting from 0
    plt.tight_layout()
    fig.subplots_adjust(bottom=0.15)
    fig.savefig(save_file_path, bbox_inches='tight', dpi=dpi)
    plt.close(fig)
    print(f"Saved figure: {save_file_path}")

    if has_separate_legend:
        if legend_save_file_path is None:
            dataset_dir = os.path.dirname(os.path.dirname(save_file_path))
            legend_path = os.path.join(dataset_dir, "legend_separate.png")
        else:
            legend_path = legend_save_file_path
            legend_dir = os.path.dirname(legend_path)
            if legend_dir:
                os.makedirs(legend_dir, exist_ok=True)
        if legend_marker_size is None:
            legend_marker_size = 6
        legend_fig = plt.figure(figsize=(2 * ncol, 1.0))
        legend_ax = legend_fig.add_subplot(111)
        for h, lbl in zip(handles, legend_labels):
            legend_ax.plot([], [], label=lbl,
                           marker=h.get_marker(),
                           color=h.get_color(),
                           linestyle='-',
                           markersize=legend_marker_size)
        legend_ax.axis('off')
        legend_fig.legend(loc='center', ncol=ncol, frameon=True, fontsize=legend_font_size)
        legend_fig.savefig(legend_path, bbox_inches='tight', dpi=dpi)
        plt.close(legend_fig)
        print(f"Saved legend image: {legend_path}")


if __name__ == "__main__":
    main()
