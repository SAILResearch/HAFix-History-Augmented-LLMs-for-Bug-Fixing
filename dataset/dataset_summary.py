from analysis.util import bugsinpy_bugs_all_51_ids, defects4j_bugs_all_116_ids
from dataset.defects4j.src.data_mining_util import defects4j_project_name_repository_map
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def summary_subject_dataset(bugs_meta_data_path, bug_ids):
    bugs_meta_data: dict = json.load(open(bugs_meta_data_path, 'r'))

    # Filter data based on BUG_IDs
    filtered_data = {k: v for k, v in bugs_meta_data.items() if str(v["id"]) in bug_ids}

    # Count projects in the filtered data
    project_counter_filtered = Counter((item["project_name"], item["project_url"]) for item in filtered_data.values())

    # Create a DataFrame to display results
    project_summary = pd.DataFrame([
        {
            "project name": next((k for k, v in defects4j_project_name_repository_map.items() if v == name), None) if "defects4j" in bugs_meta_data_path.name else name,
            "how many": count,
            "link": url
        }
        for (name, url), count in project_counter_filtered.items()
    ])
    pd.set_option('display.width', 0)  # or a large number
    return project_summary


if __name__ == "__main__":
    import json
    from collections import Counter
    import pandas as pd

    bugsinpy_bugs_meta_data = BASE_DIR/'bugsinpy/bugsinpy_bugs_meta_data.json'
    defects4j_bugs_meta_data = BASE_DIR/'defects4j/defects4j_bugs_meta_data.json'

    # Display the DataFrame
    print("================================= bugsinpy =================================")
    print(summary_subject_dataset(bugsinpy_bugs_meta_data, bugsinpy_bugs_all_51_ids))
    print("================================= defects4j =================================")
    print(summary_subject_dataset(defects4j_bugs_meta_data, defects4j_bugs_all_116_ids))
