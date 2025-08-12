import json
import os
import csv
from argparse import ArgumentParser
from collections import defaultdict
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
    return parser


def main():
    args = get_parser().parse_args()
    sample_size = 10  # 1, 5, 10

    for dataset_name in args.datasets.split(','):
        for evaluation_dir in args.evaluation_dirs.split(','):
            # first parse the model name and prompt style
            model_name_enum, prompt_style_enum = get_model_and_prompt_enum(evaluation_dir)
            model_name, prompt_style = model_name_enum.value, prompt_style_enum.value
            if not model_name or not prompt_style:
                print(f"the evaluation_dir is not a valid path name: {evaluation_dir}")
                continue

            evaluation_result_path = f"{EVALUATION_BASE_PATH}/{dataset_name}/{evaluation_dir}"
            output_csv_hafix_file = f"{RQ_BASE}/{dataset_name}/{evaluation_dir}/hafix_bugs_fixed_number.csv"
            bug_setting_result = defaultdict(lambda: {f"setting_{i}": 0 for i in range(1, 9)})

            for file_name in os.listdir(evaluation_result_path):
                if file_name.endswith('.json'):
                    for setting in HistoryCategory:
                        if f'unittest_result_{setting.name}.json' == file_name:
                            name_suf_dict = json.load(open(os.path.join(evaluation_result_path, file_name), 'r'))
                            for bug_id, result in name_suf_dict.items():
                                # calculate all cases
                                flag = 1 if any(result == 'Pass' for result in list(result['nucleus_sampling_flags'])[:sample_size]) else 0
                                bug_setting_result[bug_id][f"setting_{setting.value}"] = flag

                                # save result as row csv file
                                # save_raw_result_as_csv(
                                #     output_csv_file, evaluation_dir, setting.value, setting.name, bug_id, flag
                                # )

            # Convert to DataFrame
            df = pd.DataFrame.from_dict(bug_setting_result, orient='index').reset_index()
            df = df.rename(columns={'index': 'bug_id'})

            # Sort columns
            setting_cols = [f"setting_{i}" for i in range(1, 9)]
            df = df[['bug_id'] + setting_cols]
            df['hafix_agg'] = df[[f"setting_{i}" for i in range(2, 9)]].max(axis=1)

            # Calculate summary rows
            total_bugs = len(df)
            sum_row = ['Sum'] + df[setting_cols + ['hafix_agg']].sum().tolist()
            percent_row = ['Percentage'] + [
                f"{val / total_bugs:.2%}" for val in df[setting_cols + ['hafix_agg']].sum()
            ]

            # Calculate uniquely fixed bugs compared to baseline (setting_1)
            unique_fix_counts = []
            not_fixed_baseline = df["setting_1"] == 0
            fixed_hafix_agg = df['hafix_agg'] == 1
            for i in range(2, 9):
                fixed_i = df[f"setting_{i}"] == 1
                unique_fix_counts.append((fixed_i & not_fixed_baseline).sum())
            unique_fix_counts.append((fixed_hafix_agg & not_fixed_baseline).sum())
            unique_row = ['Unique_fixed'] + [0] + unique_fix_counts

            # Append rows
            df_final = pd.concat([df, pd.DataFrame([sum_row, percent_row, unique_row], columns=df.columns)], ignore_index=True)

            # Save to CSV
            os.makedirs(os.path.dirname(output_csv_hafix_file), exist_ok=True)
            df_final.to_csv(output_csv_hafix_file, index=False)
            print(f"Saved: {output_csv_hafix_file}")


def save_raw_result_as_csv(output_csv_file, model_id, setting_id, setting_name, bug_id, test_result):
    if not os.path.exists(output_csv_file):
        with open(output_csv_file, 'w') as f:
            csv_write = csv.writer(f)
            csv_head = ["model_id", "setting_id", "setting_name", "bug_id", "test_result"]
            csv_write.writerow(csv_head)
    with open(output_csv_file, 'a+') as f:
        csv_write = csv.writer(f)
        csv_row = [model_id, setting_id, setting_name, bug_id, test_result]
        csv_write.writerow(csv_row)


if __name__ == "__main__":
    main()
