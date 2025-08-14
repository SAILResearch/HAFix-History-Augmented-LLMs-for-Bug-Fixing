import os
import pandas as pd
from argparse import ArgumentParser
from util import HistoryCategory, get_model_and_prompt_enum

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
RQ_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, 'RQ1_2'))


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
    # dataset_name = "defects4j"
    # args.evaluation_dirs = "deepseek_coder_6.7b_instruct_fp16_Instruction"
    for dataset_name in args.datasets.split(','):
        for evaluation_dir in args.evaluation_dirs.split(','):
            # first parse the model name and prompt style
            model_name_enum, prompt_style_enum = get_model_and_prompt_enum(evaluation_dir)
            model_name, prompt_style = model_name_enum.value, prompt_style_enum.value
            if not model_name or not prompt_style:
                print(f"the evaluation_dir is not a valid path name: {evaluation_dir}")
                continue

            csv_result_path = f"{RQ_BASE}/{dataset_name}/{evaluation_dir}"
            csv_file = f"{csv_result_path}/hafix_bugs_fixed_number.csv"
            if not os.path.exists(csv_file):
                print(f"error: file not exist! {csv_file}")
                return
            df = pd.read_csv(csv_file)
            # Keep only rows with numeric bug IDs (exclude 'Sum', 'Percentage')
            df = df[df['bug_id'].apply(lambda x: str(x).isdigit())]
            # Convert bug_id column to integer
            df['bug_id'] = df['bug_id'].astype(int)

            bug_ids_fixed_baseline = set(df[df['setting_1'] == str(1)]['bug_id'].astype(str))
            baseline_label = HistoryCategory.from_setting_key("setting_1").short_name

            bug_ids_fixed_hafix_agg = set(df[df['hafix_agg'] == str(1)]['bug_id'].astype(str))
            hafix_label = 'HAFix-Agg'

            create_2_set_venn_percentage(
                bug_ids_fixed_baseline,
                bug_ids_fixed_hafix_agg,
                baseline_label,
                hafix_label,
                os.path.join(csv_result_path, f"rq1_venn_baseline_vs_hafix_agg_{name_map.get(dataset_name)}_{name_map.get(model_name)}_{name_map.get(prompt_style)}.png")
            )

            for i in range(2, 9):  # setting_1 to setting_8
                setting_col = f'setting_{i}'
                if setting_col not in df.columns:
                    print(f"error: cannot find this setting column {setting_col}")
                    return

                bug_ids_fixed_setting = set(df[df[setting_col] == str(1)]['bug_id'].astype(str))
                setting_label = HistoryCategory.from_setting_key(setting_col).short_name
                picture_name = f"rq1_venn_baseline_vs_{setting_col}_{name_map.get(dataset_name)}_{name_map.get(model_name)}_{name_map.get(prompt_style)}.png"

                picture_path = os.path.join(csv_result_path, picture_name)

                create_2_set_venn_percentage(
                    bug_ids_fixed_baseline,
                    bug_ids_fixed_setting,
                    baseline_label,
                    setting_label,
                    picture_path
                )


def create_2_set_venn(set1, set2, set1_label, set2_label, picture_name):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2, venn2_circles

    def format_label_text(numbers):
        """Format the list of numbers into a multi-line string with a dynamic number of items per line."""
        sorted_numbers = sorted(numbers, key=int)
        lines = []
        line_length = 1
        i = 0

        while i < len(sorted_numbers):
            line = ", ".join(sorted_numbers[i:i + line_length])
            lines.append(line)
            i += line_length
            line_length += 1  # Gradually increase the number of items per line

        return "\n".join(lines)

    # Create the Venn diagram
    venn = venn2([set1, set2], (set1_label, set2_label))

    # Customize the labels inside the circles
    venn.get_label_by_id('10').set_text(format_label_text(set1 - set2))
    venn.get_label_by_id('01').set_text(format_label_text(set2 - set1))
    venn.get_label_by_id('11').set_text(format_label_text(set1 & set2))

    # Optionally set the font size for better readability
    for subset in ['10', '01', '11']:
        venn.get_label_by_id(subset).set_fontsize(8)

    plt.savefig(f'{picture_name}.png', bbox_inches='tight', dpi=600)
    plt.close()


def create_2_set_venn_percentage(set1, set2, set1_label, set2_label, save_file_path):
    import matplotlib.pyplot as plt
    from matplotlib_venn import venn2, venn2_circles

    def calculate_percentage(subset, total):
        """Calculate the percentage of the subset relative to the total."""
        return len(subset) / total * 100

    total_elements = len(set1 | set2)

    # Calculate percentages for each subset
    only_set1 = calculate_percentage(set1 - set2, total_elements)
    only_set2 = calculate_percentage(set2 - set1, total_elements)
    intersection = calculate_percentage(set1 & set2, total_elements)
    # Create the Venn diagram
    venn = venn2([set1, set2], (set1_label, set2_label))

    # Customize the labels inside the circles with percentages
    if len(set1 - set2) != 0:
        venn.get_label_by_id('10').set_text(f'{len(set1 - set2)}\n\n{only_set1:.2f}%')
    else:
        venn.get_label_by_id('10').set_text(f'')
    venn.get_label_by_id('01').set_text(f'{len(set2 - set1)}\n\n{only_set2:.2f}%')
    venn.get_label_by_id('11').set_text(f'{len(set1 & set2)}\n\n{intersection:.2f}%')

    # Optionally set the font size for better readability
    for subset in ['10', '01', '11']:
        venn.get_label_by_id(subset).set_fontsize(12)

    # Outer set labels
    for label in venn.set_labels:
        label.set_fontsize(14)

    # Change the colors of the circle areas if needed
    # venn_patches = venn.patches
    # venn_patches[0].set_facecolor('red')
    # venn_patches[1].set_facecolor('blue')
    # venn_patches[2].set_facecolor('purple')  # Overlapping area color if needed

    plt.savefig(save_file_path, bbox_inches='tight', dpi=600)
    print(f"Saved: {save_file_path}")
    plt.close()


if __name__ == '__main__':
    main()
