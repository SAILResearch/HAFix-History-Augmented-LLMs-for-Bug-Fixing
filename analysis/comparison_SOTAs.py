import os
from venn import venn
import matplotlib.pyplot as plt
import pandas as pd
import json
from dataset.defects4j.src.data_mining_util import defects4j_project_name_repository_map

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
RQ_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, 'RQ1_2'))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../'))

chatgpt_fixes = """Lang-59
Lang-45
Closure-44
Lang-28
Math-69
Lang-16
Chart-9
Math-85
Chart-17
Closure-83
Chart-12
Math-94
Closure-70
Closure-73
Time-4
Lang-11
Closure-10
Closure-36
Mockito-34
Closure-5
Math-82
Math-27
Closure-97
Math-59
Time-16
Chart-11
Closure-124
Closure-92
Lang-21
Chart-7
Math-58
Chart-1
Chart-13
Math-56
Math-89
Closure-61
Lang-57
Lang-40
Chart-5
Lang-44
Closure-101
Lang-24
Math-91
Math-45
Lang-29
Math-3
Closure-57
Closure-119
Math-106
Closure-38
Closure-11
Closure-77
Closure-20
Math-41
Chart-10
Chart-26
Lang-55
Closure-67
Math-34
Math-11
Closure-52
Closure-19
Mockito-38
Lang-39
Chart-8
Math-95
Closure-33
Closure-102
Closure-65
Closure-128
Closure-62
Lang-43
Lang-52
Time-15
Math-73
Closure-125
Closure-2
Math-70
Mockito-12
Chart-6
Closure-56
Math-5
Math-57
Closure-13
Lang-26
Math-50
Math-96
Closure-78
Math-79
Lang-33
Math-33
Lang-38
Math-53
Lang-27
Closure-31
Chart-20
Mockito-29
Chart-24
Math-2
Math-30
Closure-126
Closure-104
Mockito-24
Closure-86
Math-10
Lang-51
Mockito-22
Lang-61
Closure-18
Math-105
Math-72
Math-80
Chart-4
Closure-15
Cli-11.java
Cli-17.java
Cli-28.java
Cli-40.java
Cli-8.java
Codec-10.java
Codec-17.java
Codec-18.java
Codec-2.java
Codec-3.java
Codec-4.java
Codec-7.java
Codec-9.java
Compress-19.java
Compress-23.java
Csv-11.java
Csv-1.java
Csv-4.java
Gson-11.java
Gson-13.java
Gson-15.java
JacksonCore-25.java
JacksonCore-5.java
JacksonCore-8.java
JacksonDatabind-16.java
JacksonDatabind-1.java
JacksonDatabind-27.java
JacksonDatabind-46.java
JacksonDatabind-57.java
JacksonDatabind-82.java
JacksonDatabind-96.java
JacksonDatabind-97.java
JacksonDatabind-99.java
JacksonXml-5.java
Jsoup-32.java
Jsoup-33.java
Jsoup-34.java
Jsoup-43.java
Jsoup-45.java
Jsoup-46.java
Jsoup-47.java
Jsoup-55.java
Jsoup-57.java
Jsoup-61.java
Jsoup-62.java
Jsoup-77.java
Jsoup-86.java
Jsoup-88.java"""
iterlist = """Chart 1
Chart 11
Chart 12
Chart 16
Chart 19
Chart 20
Chart 24
Chart 7
Chart 8
Chart 9
Cli 11
Cli 17
Cli 27
Cli 34
Cli 5
Cli 8
Closure 10
Closure 104
Closure 113
Closure 115
Closure 123
Closure 126
Closure 131
Closure 38
Closure 4
Closure 46
Closure 56
Closure 57
Closure 62
Closure 63
Closure 73
Closure 79
Closure 86
Closure 92
Codec 1
Codec 3
Codec 7
Compress 19
Compress 25
Compress 27
Compress 31
Csv 4
Csv 6
JacksonCore 12
JacksonCore 25
JacksonCore 6
Lang 26
Lang 34
Lang 43
Lang 47
Lang 51
Lang 55
Lang 57
Lang 59
Lang 6
Time 19
Time 4"""
iterlist = iterlist.split("\n")


def get_fixed_bugs_from_hafix_agg(csv_path, json_path):
    # Read the CSV
    df = pd.read_csv(csv_path)  # use appropriate separator if it's tab/space/comma

    # Filter bug_ids where hafix_agg == 1
    bug_ids = df[df["hafix_agg"] == '1']["bug_id"].tolist()

    # Load JSON
    with open(json_path, "r") as f:
        meta_data = json.load(f)

    # Generate project_name-defects4j_id output
    results = set()
    for bug_id in bug_ids:
        bug_id_str = str(bug_id)
        if bug_id_str in meta_data:
            # project_name = next((k for k, v in defects4j_project_name_repository_map.items() if v == meta_data[bug_id_str]["project_name"]), None)
            project_name = get_defects4j_name_by_project_name(meta_data[bug_id_str]["project_name"])
            defects4j_id = meta_data[bug_id_str]["defects4j_id"]
            results.add(f"{project_name}-{defects4j_id}")

    return results


def get_defects4j_name_by_project_name(project_name):
    for k, v in defects4j_project_name_repository_map.items():
        if v == project_name:
            return k
    return None


def filter_existing_items(input_set, json_path):
    # Load the JSON file
    with open(json_path, 'r') as f:
        meta_data = json.load(f)

    # Delete entries with id 67 and 112
    for bug_id in ["67", "112"]:
        meta_data.pop(bug_id, None)

    # Build a set of valid keys in format: "Chart 1"
    valid_keys = {f"{get_defects4j_name_by_project_name(entry['project_name'])}-{entry['defects4j_id']}" for entry in meta_data.values()}

    # Filter and return as a set
    return {item for item in input_set if item in valid_keys}


if __name__ == "__main__":

    dataset = "defects4j"
    toolGroup1_original = {}
    toolGroup1 = {}
    codellama_7b_instruct_csv_path = f"{RQ_BASE}/{dataset}/codellama_7b_instruct_fp16_Instruction/hafix_bugs_fixed_number.csv"
    deepseek_coder_instruct_fp16_Instruction_csv_path = f"{RQ_BASE}/{dataset}/deepseek_coder_6.7b_instruct_fp16_Instruction/hafix_bugs_fixed_number.csv"
    deepseek_coder_v2_16b_lite_instruct_fp16_Instruction_csv_path = f"{RQ_BASE}/{dataset}/deepseek_coder_v2_16b_lite_instruct_fp16_Instruction/hafix_bugs_fixed_number.csv"

    json_path = f"{PROJECT_DIR_BASE}/dataset/{dataset}/defects4j_bugs_meta_data.json"
    toolGroup1["HAFix-Agg_CodeLlama_7B"] = get_fixed_bugs_from_hafix_agg(codellama_7b_instruct_csv_path, json_path)
    toolGroup1["HAFix-Agg_DeepSeek_Coder_instruct"] = get_fixed_bugs_from_hafix_agg(deepseek_coder_instruct_fp16_Instruction_csv_path, json_path)
    toolGroup1["HAFix-Agg_DeepSeek_Coder_V2_instruct"] = get_fixed_bugs_from_hafix_agg(deepseek_coder_v2_16b_lite_instruct_fp16_Instruction_csv_path, json_path)

    toolGroup1_original['ChatRepair'] = set([x.split(".")[0].strip() for x in chatgpt_fixes.splitlines()]) #162 ISSTA24
    toolGroup1['ChatRepair'] = filter_existing_items(toolGroup1_original['ChatRepair'], json_path) #90

    # Figure 1: compare with ChatRepair
    plt.figure(figsize=(10, 6))
    plt.subplots_adjust(top=0.95, bottom=0.15, right=0.9)  # Make room at bottom
    venn(toolGroup1, fontsize=18, legend_loc=None)
    # Create custom legend outside
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ['#9467bd', '#aec7e8', '#98df8a', '#ffff99']]
    labels = ['HAFix-Agg_CodeLlama_7B', 'HAFix-Agg_DeepSeek_Coder_6.7B', 'HAFix-Agg_DeepSeek_Coder_V2_16B',
              'ChatRepair (Using ChatGPT)']
    plt.legend(handles, labels, bbox_to_anchor=(0.5, 0.08), loc='upper center', fontsize=18, ncol=1)
    plt.savefig(f"{RQ_BASE}/{dataset}/rq1_venn_comparison_ChatRepair.png", bbox_inches='tight', dpi=300)

    # Figure 2: compare with ITER
    toolGroup1_original['ITER'] = set([c.replace(" ", "-") for c in iterlist]) # ICSE24 74, 57, Defects4J 2.0
    toolGroup1['ITER'] = filter_existing_items(toolGroup1_original['ITER'], json_path) # 27
    del toolGroup1['ChatRepair']
    plt.figure(figsize=(10, 6))
    plt.subplots_adjust(top=0.95, bottom=0.15, right=0.9)  # Make room at bottom
    venn(toolGroup1, fontsize=18, legend_loc=None)
    # Create custom legend outside
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in ['#9467bd', '#aec7e8', '#98df8a', '#ffff99']]
    labels = ['HAFix-Agg_CodeLlama_7B', 'HAFix-Agg_DeepSeek_Coder_6.7B', 'HAFix-Agg_DeepSeek_Coder_V2_16B',
              'ITER']
    plt.legend(handles, labels, bbox_to_anchor=(0.5, 0.08), loc='upper center', fontsize=18, ncol=1)
    plt.savefig(f"{RQ_BASE}/{dataset}/rq1_venn_comparison_ITER.png", bbox_inches='tight', dpi=300)
    plt.close()

