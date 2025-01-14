import json
import os
import csv
from util import HistoryCategory


def main():
    model_size = '7b'  # 34b 13b 7b
    # prompt_style = 'instruct'

    k = 5  # 1, 5, 10

    save_csv_file = f"/home/22ys22/project/fm-apr-replay/analysis/infill@5.csv"
    source_path = f"/home/22ys22/project/fm-apr-replay/backup/evaluation/codellama_7b_instruct_hf_infill/"
    if os.path.exists(save_csv_file):
        os.remove(save_csv_file)

    # settings = []
    # for setting in HistoryCategory:
    #     settings.append(setting.value)
    for file_name in os.listdir(source_path):
        if file_name.endswith('.json'):
            for setting in HistoryCategory:
                if f'unittest_result_{setting.name}.json' == file_name:
                    name_suf_dict = json.load(open(os.path.join(source_path, file_name), 'r'))
                    if k == 1:
                        for bug_id, result in name_suf_dict.items():
                            flag = 1 if result['greedy_search_flag'] == 'Pass' else 0
                            save_result(save_csv_file, f"codellama_{model_size}_instruct", setting.value,
                                        setting.name, bug_id, flag)

                    else:
                        for bug_id, result in name_suf_dict.items():
                            # calculate all cases
                            flag = 1 if any(
                                result == 'Pass' for result in list(result['nucleus_sampling_flags'])[:k]) else 0
                            # flag = 1 if result['greedy_search_flag'] == 'Pass' else 0
                            save_result(save_csv_file, f"codellama_{model_size}_instruct", setting.value, setting.name,
                                        bug_id, flag)


def save_result(save_csv_file, model_id, setting_id, setting_name, bug_id, test_result):
    if not os.path.exists(save_csv_file):
        with open(save_csv_file, 'w') as f:
            csv_write = csv.writer(f)
            csv_head = ["model_id", "setting_id", "setting_name", "bug_id", "test_result"]
            csv_write.writerow(csv_head)
    with open(save_csv_file, 'a+') as f:
        csv_write = csv.writer(f)
        csv_row = [model_id, setting_id, setting_name, bug_id, test_result]
        csv_write.writerow(csv_row)


if __name__ == "__main__":
    main()
