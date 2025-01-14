import csv
import json
import os.path
from argparse import ArgumentParser
from pydriller import Repository
from data_mining_util import category_and_localize_single_line, filter_modified_python_files, \
    get_accurate_function_code, \
    get_superficial_function_code, get_method_by_name

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../../'))
SUBJECT_PROJECTS_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'subject_projects'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--bugsinpy_analysis_file', type=str)
    # bugsinpy_analysis_file = "/home/project/fm-apr-replay/dataset/bugsinpy_analysis.csv"
    parser.add_argument('--bugs_meta_data_file', type=str)
    # bugs_meta_data_file = "/home/project/fm-apr-replay/dataset/bugs_meta_data.json"
    return parser


args = get_parser().parse_args()


def main():
    # bugsinpy_analysis_file = args.bugsinpy_analysis_file
    # bugs_meta_data_file = args.bugs_meta_data_path
    bugsinpy_analysis_file = os.path.join(PROJECT_DIR_BASE, "dataset", "bugsinpy_analysis.csv")
    bugs_meta_data_file = os.path.join(PROJECT_DIR_BASE, "dataset", "bugs_meta_data.json")

    if os.path.exists(bugs_meta_data_file):
        os.remove(bugs_meta_data_file)
    with open(bugsinpy_analysis_file) as f:
        data = []
        for row in csv.DictReader(f):
            data.append(row)
    result = {}
    index = 0
    for i, row in enumerate(data):
        if row["is_single_line"] == '0':
            continue
        project_local_pwd = os.path.join(SUBJECT_PROJECTS_BASE_PATH, row["project_name"])
        commit_id = row["commit_id"]
        repository = Repository(
            path_to_repo=project_local_pwd,
            single=commit_id
        )
        commits = repository.traverse_commits()
        commit = next(commits)
        assert len(list(commits)) == 0
        modified_only_python_files = filter_modified_python_files(commit)
        assert len(modified_only_python_files) == 1
        modified_file = modified_only_python_files[0]
        project_name = row["project_name"]
        project_url = row["project_url"]
        bugsinpy_id = row["bugsinpy_id"]
        file_path = modified_file.new_path
        file_name = modified_file.filename
        is_single_hunk = True if row["is_single_hunk"] == '1' else False
        is_single_line = True if row["is_single_line"] == '1' else False
        diff = modified_file.diff
        in_function = True if row["is_in_function"] == '1' else False
        if len(modified_file.changed_methods) == 0:
            print(project_name, " ", commit_id, " ", "no methods")
            continue
        buggy_line_location, buggy_line_content = category_and_localize_single_line(modified_file.diff_parsed, "python")

        changed_method = modified_file.changed_methods[0]
        if (len(modified_file.changed_methods)) > 1:
            print("more than 1", len(modified_file.changed_methods))
            for method in modified_file.changed_methods:
                if '.' not in method.name:
                    changed_method = method
        function_name = changed_method.name
        function_after_start_line = changed_method.start_line
        function_after_end_line = changed_method.end_line
        file_before = modified_file.source_code_before
        file_after = modified_file.source_code
        # Accurately narrow and record the function's namespace here,
        # for future function localization when there are multiple functions using same name
        # is parent of changed method is class, record class name, else record Module's python file name
        function_parent, function_code_after = get_accurate_function_code(
            changed_method.filename,
            file_after,
            function_name,
            function_after_start_line,
            function_after_end_line
        )
        function_before_start_line, function_before_end_line, function_code_before = get_superficial_function_code(
            file_before,
            function_name,
            function_parent
        )
        # As if there is only one-line change, so start/end-line should be same between before and after
        # function_code_before = get_function_code(file_before, function_name, function_start_line, function_end_line)
        # function_code_after = get_function_code(file_after, function_name, function_start_line, function_end_line)

        method_after = get_method_by_name(
            function_name,
            function_after_start_line,
            function_after_end_line,
            modified_file.changed_methods
        )
        if method_after is not None:
            function_code_after_token_count = method_after.token_count
        else:
            function_code_after_token_count = 0

        method_before = get_method_by_name(
            function_name,
            function_before_start_line,
            function_before_end_line,
            modified_file.methods_before
        )
        if method_before is not None:
            function_code_before_token_count = method_before.token_count
        else:
            function_code_before_token_count = 0

        if function_code_before == "" or function_code_after == "":
            print("wrong", project_name, " ", commit_id)
            continue

        test = ""
        is_standalone = ""  # True or False
        level = ""  # self-contained, slib_runnable, plib_runnable,
        # class_runnable, file_runnable, # project_runnable
        dependency = {
            "in_class": [],  # location
            "in_file": [],
            "cross_file": []
        }
        commit_message = commit.msg
        commit_author = commit.author.name
        commit_parent = commit.parents[0]
        commit_date = commit.committer_date.strftime("%Y-%m-%d %H:%M:%S")
        file_nloc = modified_file.nloc
        file_complexity = modified_file.complexity
        file_token_count = modified_file.token_count

        index = index + 1
        bug_meta_data = {
            "id": index,
            "project_name": project_name,
            "project_url": project_url,
            "bugsinpy_id": bugsinpy_id,
            "is_single_hunk": is_single_hunk,  # True or False
            "is_single_line": is_single_line,  # True or False
            "buggy_line_location": buggy_line_location,
            "buggy_line_content": buggy_line_content,
            "in_function": in_function,  # True or False
            "commit": {
                "commit_id": commit_id,
                "commit_message": commit_message,
                "commit_author": commit_author,
                "commit_parent": commit_parent,
                "commit_date": commit_date,
                "commit_file_diff": diff
            },
            "function": {
                "function_name": function_name,
                "function_parent": function_parent,
                "function_before_start_line": function_before_start_line,
                "function_before_end_line": function_before_end_line,
                "function_after_start_line": function_after_start_line,
                "function_after_end_line": function_after_end_line,
                "function_before_token_count": function_code_before_token_count,
                "function_after_token_count": function_code_after_token_count,
                "function_before": function_code_before,
                "function_after": function_code_after
            },
            "file": {
                "file_name": file_name,
                "file_path": file_path,
                "file_nloc": file_nloc,
                "file_complexity": file_complexity,
                "file_token_count": file_token_count,
                "file_before": file_before,
                "file_after": file_after
            },
            "test": [""],
            "is_standalone": "",  # True or False
            "level": "",  # self-contained, slib_runnable, plib_runnable,
            # class_runnable, file_runnable, # project_runnable
            "dependency": {
                "in_class": [],  # location
                "in_file": [],
                "cross_file": []
            }
        }
        result[index] = bug_meta_data
        json.dump(result, open(bugs_meta_data_file, 'w'), indent=2)
    print("Finish the bug-fix commit info mining!")
