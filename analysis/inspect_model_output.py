import os
import json

from util import HistoryCategory

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))
MODEL_INFERENCE_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup', 'model_inference'))
MODEL_EVALUATION_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'backup', 'evaluation'))


def main():
    model_name_path = [
        'codellama_7b_instruct_hf',
        'codellama_7b_instruct_hf_infill',
        'codellama_13b_instruct_hf',
        'codellama_13b_instruct_hf_infill',
        'codellama_34b_instruct_hf'
    ]
    history_settings_ids = [1, 2, 3, 4, 5, 6, 7, 8]

    for bug_id in range(1, 69):
        bug_id_str = str(bug_id)
        _bug_id_inspect_path = f"{CURRENT_DIR_PATH}/inspect_model_output"
        os.makedirs(_bug_id_inspect_path, exist_ok=True)
        bug_id_inspect_path = f"{_bug_id_inspect_path}/model_output_bug_{bug_id}.txt"
        bug_id_inspect_result = open(bug_id_inspect_path, 'a')
        bug_id_inspect_result.write(f"####################inspect model-generated code for bug {bug_id}####################\n")
        for model_name in model_name_path:
            bug_id_inspect_result.write(
                f"####################inspect {model_name}-generated code####################\n")
            for history_flag in history_settings_ids:
                history_flag = str(history_flag)
                if model_name == 'codellama_7b_instruct_hf_infill' or model_name == 'codellama_13b_instruct_hf_infill':
                    inference_path = f"{MODEL_INFERENCE_BASE_PATH}/{model_name}/{model_name.replace('_infill', '')}_{HistoryCategory(history_flag).name}.json"
                    evaluate_path = f"{MODEL_EVALUATION_BASE_PATH}/{model_name}/unittest_result_{model_name.replace('_infill', '')}_{HistoryCategory(history_flag).name}.json"
                else:
                    inference_path = f"{MODEL_INFERENCE_BASE_PATH}/{model_name}/{model_name}_{HistoryCategory(history_flag).name}.json"
                    evaluate_path = f"{MODEL_EVALUATION_BASE_PATH}/{model_name}/unittest_result_{model_name}_{HistoryCategory(history_flag).name}.json"

                inference_json = json.load(open(inference_path, 'r'))
                evaluate_result: dict = json.load(open(evaluate_path, 'r'))

                if bug_id_str not in inference_json or bug_id_str not in evaluate_result:
                    continue
                if history_flag == '1':
                    buggy_code = inference_json[bug_id_str]['input']['buggy_code']
                    ground_fixed_code = inference_json[bug_id_str]['ground_fixed_code']
                    bug_id_inspect_result.write(f"#1. buggy code\n")
                    bug_id_inspect_result.write(f"{buggy_code}\n\n")
                    bug_id_inspect_result.write(f"#2. ground fixed code\n")
                    bug_id_inspect_result.write(f"{ground_fixed_code}\n\n")

                model_generated_code = inference_json[bug_id_str]['output']['greedy_search']
                result = evaluate_result[bug_id_str]['greedy_search_flag']
                bug_id_inspect_result.write(f"#setting_{history_flag}: {HistoryCategory(history_flag).name}\n")
                bug_id_inspect_result.write(f"{result}\n")
                bug_id_inspect_result.write(f"{model_generated_code}\n\n")

        bug_id_inspect_result.close()


if __name__ == '__main__':
    main()
