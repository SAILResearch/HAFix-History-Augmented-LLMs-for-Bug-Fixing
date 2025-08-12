import json
import os
from collections import Counter, defaultdict
import pandas as pd
from util import HistoryCategory


def get_evaluation_test_result(evaluation_result_path):
    sample_size = 10
    bug_setting_result = defaultdict(lambda: {f"{i}": 0 for i in range(1, 9)})
    for file_name in os.listdir(evaluation_result_path):
        if file_name.endswith('.json'):
            for setting in HistoryCategory:
                if f'unittest_result_{setting.name}.json' == file_name:
                    name_suf_dict = json.load(open(os.path.join(evaluation_result_path, file_name), 'r'))
                    for bug_id, result in name_suf_dict.items():
                        # calculate all cases
                        flag = 1 if any(result == 'Pass' for result in list(result['nucleus_sampling_flags'])[:sample_size]) else 0
                        bug_setting_result[bug_id][setting.value] = flag
    return bug_setting_result


def process_early_stop_custom_settings_order(exhaustive_csv_file, output_csv_file, setting_order):
    # If file exist, remove it first
    if os.path.exists(output_csv_file):
        os.remove(output_csv_file)
    # Read the original CSV file
    df = pd.read_csv(exhaustive_csv_file)
    # Sort by bug_id and setting_id to ensure proper order
    df = df.sort_values(['bug_id', 'setting_id'])
    # Create a list to store the filtered rows
    filtered_rows = []
    # Group by bug_id to process each bug separately
    for bug_id, bug_group in df.groupby('bug_id'):
        # Sort by setting_id to ensure we process in order from 1 to 8
        for setting_id in setting_order:
            matching_rows = bug_group[bug_group['setting_id'] == int(setting_id)]
            assert not matching_rows.empty, f"setting {setting_id} data missing for {exhaustive_csv_file}"
            assert len(matching_rows) == 1, f"Expected exactly 1 row for bug_id={bug_id}, setting_id={setting_id}, but found {len(matching_rows)}"
            # Get the row for this setting
            row = matching_rows.iloc[0]

            # Always keep the current row
            filtered_rows.append(row)
            # If test_result is 1, stop processing further settings for this bug
            if row['test_result'] == 1:
                break
    # Create new dataframe from filtered rows
    filtered_df = pd.DataFrame(filtered_rows)
    # Save to new CSV file
    filtered_df.to_csv(output_csv_file, index=False)
    print(f"Saved: {output_csv_file}")


def get_setting_order_es_accsorted(bug_setting_result_dict):
    """
    Get setting order based on number of bugs being fixed (test_result=1) for each setting,
    sorted in descending order.

    Args:
        bug_setting_result_dict: Dictionary with bug_id as keys and setting results as values
                                Format: {bug_id: {'1': 0/1, '2': 0/1, ..., '8': 0/1}}

    Returns:
        List of setting_ids ordered by number of bugs fixed (descending)
    """
    setting_fix_counts = {}

    # Count how many bugs each setting fixes
    for setting_id in ['1', '2', '3', '4', '5', '6', '7', '8']:
        fix_count = sum(1 for bug_results in bug_setting_result_dict.values()
                        if bug_results[setting_id] == 1)
        setting_fix_counts[setting_id] = fix_count

    # Sort settings by fix count in descending order
    sorted_settings = sorted(setting_fix_counts.items(), key=lambda x: x[1], reverse=True)

    return [setting_id for setting_id, _ in sorted_settings]


def get_setting_order_es_unisorted(bug_setting_result_dict):
    """
    Get setting order based on number of bugs uniquely solved compared with baseline (setting_1).
    Setting_1 is placed first, then other settings are ordered by unique bug fixes.

    Args:
        bug_setting_result_dict: Dictionary with bug_id as keys and setting results as values
                                Format: {bug_id: {'1': 0/1, '2': 0/1, ..., '8': 0/1}}

    Returns:
        List of setting_ids with setting_1 first, then ordered by unique fixes
    """
    # Get bugs fixed by baseline (setting_1)
    baseline_fixed_bugs = set()
    for bug_id, bug_results in bug_setting_result_dict.items():
        if bug_results['1'] == 1:
            baseline_fixed_bugs.add(bug_id)

    setting_unique_counts = {}

    # Count unique bugs fixed by each setting (excluding setting_1)
    for setting_id in ['2', '3', '4', '5', '6', '7', '8']:
        unique_count = 0
        for bug_id, bug_results in bug_setting_result_dict.items():
            # Bug is uniquely fixed if this setting fixes it but baseline doesn't
            if bug_results[setting_id] == 1 and bug_id not in baseline_fixed_bugs:
                unique_count += 1
        setting_unique_counts[setting_id] = unique_count

    # Sort settings by unique fix count in descending order
    sorted_settings = sorted(setting_unique_counts.items(), key=lambda x: x[1], reverse=True)

    # Return with setting_1 first, then the sorted order
    return ['1'] + [setting_id for setting_id, _ in sorted_settings]


def generate_all_scenarios_summary_csv(all_scenarios_csv_file_dict, output_csv_file, value_field):
    """
    Generate a summary CSV showing the sum of total_length for each setting across different CSV files.
    Rows are settings 1-8, columns are scenarios.

    Args:
        all_scenarios_csv_file_dict: Dictionary with scenario_name as key and csv_file_path as value
        output_csv_file: Path for the output summary CSV file
        value_field: column title of the value
    """
    # If file exist, remove it first
    if os.path.exists(output_csv_file):
        os.remove(output_csv_file)
    settings = ['1', '2', '3', '4', '5', '6', '7', '8']

    # Initialize summary data with setting column
    summary_data = {setting_id: {'setting_id': setting_id} for setting_id in settings}

    # Process each CSV file
    for scenario_name, csv_file_path in all_scenarios_csv_file_dict.items():
        assert os.path.exists(csv_file_path), f"CSV file does not exist: {csv_file_path}"

        # Read CSV and group by setting_id to sum total_length
        df = pd.read_csv(csv_file_path)
        setting_sums = df.groupby('setting_id')[value_field].sum()

        # Add sums for each setting
        for setting_id in settings:
            summary_data[setting_id][scenario_name] = setting_sums.get(int(setting_id))

    # Create DataFrame from summary data
    summary_df = pd.DataFrame([summary_data[setting_id] for setting_id in settings])

    # Ensure column order: setting first, then scenarios in dict order
    column_order = ['setting_id'] + list(all_scenarios_csv_file_dict.keys())
    summary_df = summary_df[column_order]

    # Save to CSV
    summary_df.to_csv(output_csv_file, index=False)
    print(f"Saved: {output_csv_file}")


def all_scenarios_symmetry_summary_csv(all_scenarios_csv_file_dict, all_scenarios_setting_order_dict, output_csv_file, value_field):
    """
    Generate a summary CSV showing the sum of total_length for each setting across different CSV files,
    split into token_fixed (test_result == 1) and token_not_fixed (test_result == 0).

    Args:
        all_scenarios_csv_file_dict: Dictionary with scenario_name as key and csv_file_path as value
        all_scenarios_setting_order_dict: dict of {scenario_name: list of setting_id strings in order}
        output_csv_file: Path for the output summary CSV file
        value_field: column title of the value
    """
    # If file exist, remove it first
    if os.path.exists(output_csv_file):
        os.remove(output_csv_file)
    summary_rows = []

    for scenario_name, csv_file_path in all_scenarios_csv_file_dict.items():
        assert os.path.exists(csv_file_path), f"CSV file does not exist: {csv_file_path}"
        setting_order = all_scenarios_setting_order_dict[scenario_name]

        df = pd.read_csv(csv_file_path)
        df["setting_id"] = df["setting_id"].astype(str)
        df["bug_id"] = df["bug_id"].astype(str)

        # Assign setting order index for correct per-bug evaluation sequence
        df["setting_order"] = df["setting_id"].apply(setting_order.index)
        df = df.sort_values(by=["bug_id", "setting_order"])

        # Determine first setting that solves each bug
        bug_to_solved_setting = {}
        for bug_id, group in df.groupby("bug_id"):
            for _, row in group.iterrows():
                if row["test_result"] == 1:
                    bug_to_solved_setting[bug_id] = row["setting_id"]
                    break

        # Count how many bugs were solved by each setting
        bug_solved_counter = Counter(bug_to_solved_setting.values())

        # Split into fixed and not_fixed
        df_fixed = df[df['test_result'] == 1]
        df_not_fixed = df[df['test_result'] == 0]

        # Group by setting and sum
        fixed_sums = df_fixed.groupby("setting_id")[value_field].sum()
        not_fixed_sums = df_not_fixed.groupby("setting_id")[value_field].sum()

        for setting in setting_order:
            row = {
                "type": scenario_name,
                "setting_id": f"{setting}",
                f"{value_field}_fixed": fixed_sums.get(setting, 0),
                f"{value_field}_not_fixed": not_fixed_sums.get(setting, 0),
                "num_bugs_solved_newly": bug_solved_counter.get(setting, 0)
            }
            summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_csv_file, index=False)
    print(f"Saved: {output_csv_file}")


def generate_setting_acc_scatter_csv(bug_setting_result_dict, exhaustive_csv_file, output_csv_file, value_field):
    # If file exist, remove it first
    if os.path.exists(output_csv_file):
        os.remove(output_csv_file)
    total_bugs = len(bug_setting_result_dict)
    setting_ids = [str(i) for i in range(1, 9)]

    # Count number of bugs solved per setting
    setting_solved_counts = {setting: 0 for setting in setting_ids}
    for bug_result in bug_setting_result_dict.values():
        for setting_id in setting_ids:
            if bug_result.get(setting_id, 0) == 1:
                setting_solved_counts[setting_id] += 1

    # Read total tokens per setting from the exhaustive CSV
    df = pd.read_csv(exhaustive_csv_file)
    df["setting_id"] = df["setting_id"].astype(str)
    token_sums = df.groupby("setting_id")[value_field].sum().to_dict()

    # Combine into summary rows
    summary_rows = []
    for setting in setting_ids:
        percentage = round(setting_solved_counts[setting] / total_bugs, 4)
        total_tokens = int(token_sums.get(setting, 0))
        summary_rows.append({
            "setting_id": setting,
            "percentage_solved": percentage,
            f"total_{value_field}": total_tokens
        })

    # Save to CSV
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(output_csv_file, index=False)
    print(f"Saved: {output_csv_file}")
