import csv
import json
import os.path
from pathlib import Path
from pydriller import Git, Commit, ModifiedFile
from argparse import ArgumentParser
from data_mining_util import (get_accurate_function_code, defects4j_project_name_repository_map,
                              defects4j_project_name_url_map, get_pydriller_method_by_long_name,
                              get_pydriller_method_by_changed_line)
from dataset.defects4j.src.defects4j_analysis import is_single_line_bug, is_single_hunk_bug

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../../../'))
SUBJECT_PROJECTS_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'subject_projects', 'defects4j'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--defects4j_analysis_file', type=str)
    parser.add_argument('--bugs_meta_data_file', type=str)
    return parser


args = get_parser().parse_args()


def main():
    # defects4j_analysis_file = args.defects4j_analysis_file
    # bugs_meta_data_file = args.bugs_meta_data_path
    bugs_meta_data_file = os.path.join(PROJECT_DIR_BASE, "dataset", "defects4j", "defects4j_bugs_meta_data.json")
    chart_csv_path = os.path.join(PROJECT_DIR_BASE, "dataset", "defects4j", "Chart_commit.csv")

    if os.path.exists(bugs_meta_data_file):
        os.remove(bugs_meta_data_file)
    base_path = Path(PROJECT_DIR_BASE).parent / "defects4j" / "framework" / "projects"
    single_line_bugs, _ = categorize_bugs(base_path, get_active_bugs(base_path))

    result = {}
    index = 0
    for project_name, repo_name in defects4j_project_name_repository_map.items():
        # if project_name != 'Chart':
        #     continue
        defects4j_analysis_file = os.path.join(base_path, project_name, 'active-bugs.csv')

        # bug description link
        defects4j_commit_db_file = os.path.join(base_path, project_name, 'commit-db')
        bug_to_report_link = {}
        with open(defects4j_commit_db_file, 'r') as f:
            for line in f:
                row = line.strip().split(',')
                if str(row[-1]).startswith("https://"):
                    id = row[0]
                    bug_to_report_link[int(id)] = row[-1]

        defects4j_modified_class_path = os.path.join(base_path, project_name, 'modified_classes')
        with open(defects4j_analysis_file) as f:
            data = []
            for row in csv.DictReader(f):
                data.append(row)
        for bug_id in single_line_bugs.get(project_name):

            bug_description_link = bug_to_report_link.get(bug_id) if bug_to_report_link.get(bug_id) is not None else ""
            # challenge1: get buggy_line_content and buggy_line_location from the patch file
            bug_patch_file = os.path.join(base_path, project_name, 'patches', f'{bug_id}.src.patch')
            buggy_line_content, fixed_line_content, fixed_line_location = extract_buggy_line_info(bug_patch_file)

            if fixed_line_location is None or buggy_line_content is None:
                print(f'Fail to parse the buggy_line_content for this bug: Project {project_name} bug_id {bug_id}')
                continue

            # handle some error cases due to the error from Defects4J
            if project_name == 'Chart' and str(bug_id) == '1':
                fixed_line_location = 1564
            if project_name == 'Closure' and str(bug_id) == '10':
                fixed_line_location, buggy_line_content = 1417, 'return valueCheck(n, MAY_BE_STRING_PREDICATE);'
            if project_name == 'Math' and str(bug_id) == '32':
                fixed_line_location, buggy_line_content = 135, 'if ((Boolean) getTree(false).getAttribute()) {'
            if project_name == 'JacksonDatabind' and str(bug_id) == '17':
                fixed_line_location, buggy_line_content = 178, '|| TreeNode.class.isAssignableFrom(t.getRawClass());'

            bug = get_item_from_list(data, 'bug.id', bug_id)
            fixed_commit_id = bug.get('revision.id.fixed')
            if project_name == 'Chart':
                fixed_commit_id = get_fixed_commit(chart_csv_path, 'Chart', bug_id)
            project_local_path = os.path.join(SUBJECT_PROJECTS_BASE_PATH, repo_name)
            git_repo = Git(project_local_path)
            # make sure reset to main branch
            git_repo.reset()
            commit = git_repo.get_commit(fixed_commit_id)
            modified_class_file_path = os.path.join(defects4j_modified_class_path, f'{bug_id}.src')
            modified_class_name = open(modified_class_file_path).readline().strip().split('.')[-1]
            modified_class_file_name = f'{modified_class_name}.java'

            # suppose there is only one file changed with same name
            modified_file = get_modified_file_by_name(modified_class_file_name, commit)
            if modified_file is None:
                print(f'Fail to find the modified_file in the fixed commit: Project {project_name} bug_id {bug_id}')
                continue

            project_url = defects4j_project_name_url_map.get(project_name)
            defects4j_id = bug_id
            file_path = modified_file.new_path
            # file_path_old = modified_file.old_path
            # if file_path != file_path_old:
            #     print(f'file_path != file_path_old')
            file_name = modified_file.filename

            diff = modified_file.diff
            in_function = True
            if len(modified_file.changed_methods) == 0:
                print(f'The bug is not inside a function: project_name {project_name} bug_id {bug_id}')
                continue

            # challenge2: get changed_method from git repo, and confirm the changed line is inside the function
            changed_method = get_pydriller_method_by_changed_line(fixed_line_location, modified_file)
            if changed_method is None:
                print(f'Error: the buggy line is not inside a function: project_name {project_name} bug_id {bug_id}')
                continue

            function_parent = changed_method.long_name
            function_name = changed_method.name.split("::")[-1]
            function_after_start_line = changed_method.start_line
            function_after_end_line = changed_method.end_line
            file_before = modified_file.source_code_before
            file_after = modified_file.source_code

            # challenge3: get fixed function-level code (function_code_after).
            # Using Class name, function signature (function name and paramter tyle) can precisely localized
            # the function-level code. Here I might need to use a python library for parsing Java code javalang.
            function_code_after = get_accurate_function_code(
                file_after,
                function_after_start_line,
                function_after_end_line
            )
            # have to confirm that the function_code_after code contains the fixed line
            if fixed_line_content.strip() not in function_code_after:
                print(
                    f'Error: the fixed line is not inside the fixed function: project_name {project_name} bug_id {bug_id}')
                continue

            fixed_line_location_verify = find_code_line_location(
                file_after,
                function_code_after,
                fixed_line_content,
                fixed_line_location
            )

            if fixed_line_location_verify == -1:
                print(f'Error: cannot find fixed line location: project_name {project_name} bug_id {bug_id}')
                continue

            changed_method_before = get_pydriller_method_by_long_name(modified_file.methods_before, changed_method.long_name)
            if changed_method_before is None:
                print(f'Error: cannot find the buggy function: project_name {project_name} bug_id {bug_id}')
                continue
            function_before_start_line = changed_method_before.start_line
            function_before_end_line = changed_method_before.end_line
            function_code_before = get_accurate_function_code(
                file_before,
                function_before_start_line,
                function_before_end_line
            )

            # have to confirm that the function_code_before code contains the buggy line
            skip_cases = {('Closure', '18'), ('JxPath', '10'), ('Math', '96')}
            if buggy_line_content.strip() not in function_code_before:
                if (project_name, str(bug_id)) not in skip_cases:
                    print(
                        f'Error: the buggy line is not inside the buggy function: project_name {project_name} bug_id {bug_id}')
                    continue

            # verify the buggy line location
            buggy_line_location_verify = find_code_line_location(
                file_before,
                function_code_before,
                buggy_line_content,
                fixed_line_location_verify
            )

            # if buggy_line_location_verify != fixed_line_location:
            #     print(f'buggy_line_location_verify != fixed_line_location\n{project_name}: {bug_id}: {buggy_line_location_verify}: {fixed_line_location}')
            # manually fix the buggy_line_location_verify
            if buggy_line_location_verify == -1:
                if project_name == 'Chart' and str(bug_id) == '10':
                    buggy_line_location_verify = 56
                if project_name == 'Closure' and str(bug_id) == '18':
                    buggy_line_location_verify = 1288
                if project_name == 'Closure' and str(bug_id) == '67':
                    buggy_line_location_verify = 316
                if project_name == 'JacksonDatabind' and str(bug_id) == '57':
                    buggy_line_location_verify = 1441
                if project_name == 'Jsoup' and str(bug_id) == '32':
                    buggy_line_location_verify = 1138
                if project_name == 'JxPath' and str(bug_id) == '10':
                    buggy_line_location_verify = 42
                if project_name == 'Math' and str(bug_id) == '96':
                    buggy_line_location_verify = 258

            function_code_after_token_count = changed_method.token_count
            function_code_before_token_count = changed_method_before.token_count

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
                "project_name": repo_name,
                "project_url": project_url,
                "defects4j_id": defects4j_id,
                "buggy_line_location": buggy_line_location_verify,
                "buggy_line_content": buggy_line_content.strip(),
                "fixed_line_location": fixed_line_location_verify,
                "fixed_line_content": fixed_line_content.strip(),
                "bug_description_link": bug_description_link,
                "in_function": in_function,  # True or False
                "commit": {
                    "commit_id": commit.hash,
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
                    "file_before": "",
                    "file_after": ""
                }
            }
            result[index] = bug_meta_data
            json.dump(result, open(bugs_meta_data_file, 'w'), indent=2)
            # print("Finish the bug-fix commit info mining!")


# output log:
# The bug is not inside a function: project_name Codec bug_id 16
# The bug is not inside a function: project_name Csv bug_id 12
# The bug is not inside a function: project_name Jsoup bug_id 17
# The bug is not inside a function: project_name Jsoup bug_id 25
# The bug is not inside a function: project_name Math bug_id 104
# The bug is not inside a function: project_name Mockito bug_id 26


def find_code_line_location(file_code: str,
                            function_code: str,
                            line_content: str,
                            refer_line_location: int) -> int:
    lines = file_code.splitlines()
    candidate_indices = [i for i, line in enumerate(lines, start=1)
                         if line.strip() == line_content.strip()]

    if not candidate_indices:
        print(f'Error: fixed_line_content not inside the code file')
        return -1  # not found

    # If only one match, return it
    if len(candidate_indices) == 1:
        return candidate_indices[0]

    # Filter to matches inside function_code_after
    function_lines = set(line.strip() for line in function_code.splitlines())

    candidates_in_function = [
        idx for idx in candidate_indices
        if lines[idx - 1].strip() in function_lines
    ]

    if not candidates_in_function:
        print(f'Error: fixed_line_content not inside the fixed function')
        return -1

    # Find the one closest to buggy_line_location
    return min(candidates_in_function, key=lambda x: abs(x - refer_line_location))


def get_modified_file_by_name(file_name: str, commit: Commit) -> ModifiedFile | None:
    candidate_list = list(filter(lambda modified_file: file_name == modified_file.filename, commit.modified_files))
    if len(candidate_list) == 0:
        candidate_list_ = list(filter(
            lambda modified_file: (modified_file.new_path is not None and file_name in modified_file.new_path) or (
                    modified_file.old_path is not None and file_name in modified_file.old_path),
            commit.modified_files))
        if len(candidate_list_) == 0:
            return None
        else:
            return candidate_list_[0]
    else:
        return candidate_list[0]


def get_fixed_commit(csv_path, project_name, bug_id):
    with open(csv_path, mode='r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row['project'] == project_name and int(row['bug_id']) == bug_id:
                return row['fixed']

    # If no matching record is found:
    return None


def get_item_from_list(list, field_name, keyword):
    for dict_item in list:
        if dict_item.get(field_name) == str(keyword):
            return dict_item
    return None


def categorize_bugs(base_path, active_bugs):
    single_line_bugs = {}
    single_hunk_bugs = {}

    for project_name, bug_ids in active_bugs.items():
        for bug_id in bug_ids:
            patch_file_path = os.path.join(base_path, project_name, 'patches', f'{bug_id}.src.patch')

            if os.path.exists(patch_file_path):
                if is_single_line_bug(patch_file_path):
                    single_line_bugs.setdefault(project_name, []).append(bug_id)

                if is_single_hunk_bug(patch_file_path):
                    single_hunk_bugs.setdefault(project_name, []).append(bug_id)

    return single_line_bugs, single_hunk_bugs


def get_active_bugs(base_path):
    projects_bugs = {}

    # Iterate over each project directory in the given directory
    for project_name in os.listdir(base_path):
        project_path = os.path.join(base_path, project_name)
        if os.path.isdir(project_path):
            csv_file_path = os.path.join(project_path, 'active-bugs.csv')
            if os.path.exists(csv_file_path):
                with open(csv_file_path, mode='r', newline='') as file:
                    reader = csv.DictReader(file)
                    bug_ids = [int(row['bug.id']) for row in reader]
                    projects_bugs[project_name] = bug_ids

    return projects_bugs


def extract_buggy_line_info(patch_file_path):
    # There is a bug in Defects4J patch file, the - line is actually fixed line and the + line is the buggy line
    with open(patch_file_path, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith('@@'):
            # Example: @@ -1794,7 +1794,7 @@
            hunk_info = line.split(' ')[1]  # e.g., '-1794,7'
            start_line = int(hunk_info.split(',')[0][1:])
            current_line_number = start_line
            j = i + 1

            while j < len(lines):
                l = lines[j]
                if l.startswith('@@') or l.startswith('diff'):
                    break  # end of hunk

                if l.startswith('-') and not l.startswith('---'):
                    # Replace the first '-' with a space to preserve indentation
                    fixed_line_content = l.replace('-', ' ', 1)
                    buggy_line_ = lines[j + 1]
                    buggy_line_content = buggy_line_.replace('+', ' ', 1)
                    fixed_line_number = current_line_number
                    return buggy_line_content, fixed_line_content, fixed_line_number

                if not l.startswith('+'):
                    current_line_number += 1

                j += 1

    return None, None, None


if __name__ == '__main__':
    main()
