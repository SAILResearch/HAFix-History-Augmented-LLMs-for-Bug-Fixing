import json
import os.path
import subprocess
from argparse import ArgumentParser

from pydriller import Git, Commit, ModifiedFile
from data_mining_util import get_accurate_function_code, get_pydriller_method_by_long_name

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../../../'))
SUBJECT_PROJECTS_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'subject_projects', 'defects4j'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--defects4j_analysis_file', type=str)
    # bugsinpy_analysis_file = "/home/project/fm-apr-replay/dataset/bugsinpy_analysis.csv"
    parser.add_argument('--bugs_meta_data_file', type=str)
    # bugs_meta_data_file = "/home/project/fm-apr-replay/dataset/bugs_meta_data.json"
    parser.add_argument('--history_base_path', type=str)
    # history_base_path = "/home/project/fm-apr-replay/dataset/history_blame/"
    return parser


args = get_parser().parse_args()


def main():
    # bugsinpy_analysis_file = args.bugsinpy_analysis_file
    # bugs_meta_data_file = args.bugs_meta_data_path
    # history_base_path = args.history_base_path
    bugs_meta_data_file = os.path.join(PROJECT_DIR_BASE, "dataset", "defects4j", "defects4j_bugs_meta_data.json")
    history_base_path = os.path.join(PROJECT_DIR_BASE, "dataset", "defects4j", "history_blame")
    if not os.path.exists(history_base_path):
        os.makedirs(history_base_path)

    # history mining
    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
    for bug_id, bug_value in bugs_meta_data.items():
        history_save_path = os.path.join(history_base_path, f'{bug_id}.json')
        if os.path.exists(history_save_path):
            os.remove(history_save_path)
        project_local_path = os.path.join(SUBJECT_PROJECTS_BASE_PATH, bug_value['project_name'])
        git_repo = Git(project_local_path)
        # make sure reset to main branch
        git_repo.reset()
        blame_commit_id = get_last_commit_touching_buggy_line_before_fix_commit(
            project_local_path,
            bug_value['file']['file_path'],
            bug_value['buggy_line_location'],
            bug_value['commit']['commit_id']
        )

        blame_commit = git_repo.get_commit(blame_commit_id)
        blame_commit_modified_file = get_modified_file_by_name(
            bug_value['file']['file_name'],
            blame_commit
        )
        if blame_commit_modified_file is None:
            print(f"Cannot find the corresponding modified file in blame commit: "
                  f"{bug_id} {project_local_path} {bug_value['commit']['commit_id']} {blame_commit_id}")
            continue

        blame_commit_data = mining_history_data_from_commit(
            bug_id,
            blame_commit,
            blame_commit_modified_file,
            bug_value['function']['function_parent']
        )

        # bug 67 and 112 don't have the blame commit, so totally 116 bugs validated
        # 7. get all commits which modifying the file before the bug-fix commit
        git_repo.checkout(bug_value['commit']['commit_id'])
        assert git_repo.get_head().hash == bug_value['commit']['commit_id']
        commits_modify_file_before_fix = git_repo.get_commits_modified_file(
            project_local_path + '/' + bug_value['file']['file_path']
        )
        git_repo.reset()
        # commits_modify_file_all = git_repo.get_commits_modified_file(
        #     project_local_path + '/' + bug_value['file']['file_path'], include_deleted_files=True
        # )
        assert git_repo.get_head().hash != bug_value['commit']['commit_id']
        history_data = {
            "id": bug_id,
            "blame_commit": blame_commit_data,
            "commits_modify_file_before_fix": {
                "size": len(commits_modify_file_before_fix),
                # "commit_ids": commits_modify_file_before_fix
            }
        }
        json.dump(history_data, open(history_save_path, 'w'), indent=2)


def mining_history_data_from_commit(bug_id, commit: Commit, blame_commit_modified_file: ModifiedFile, function_path_name: str):
    # 2. check on this point: function-level difference and file-level difference
    # what is the changed line number?
    # what is the line-surrounded function?
    # Here don't use path, using name instead as the path might be changed
    modified_file_patch = blame_commit_modified_file.diff

    # start_line_before, end_line_before, function_code_before \
    #     = extract_function_code_by_changed_line(modified_file_after, buggy_line_location)
    # challenge2: get changed_method from git repo, and confirm the changed line is inside the function
    changed_method = get_pydriller_method_by_long_name(blame_commit_modified_file.methods, function_path_name)
    if changed_method is None:
        print(f'Warning: the buggy line is not inside a function of blame commit, bug_id: {bug_id}')
        function_before_start_line = ""
        function_before_end_line = ""
        function_code_before = ""
        function_code_before_token_count = 0
        function_after_start_line = ""
        function_after_end_line = ""
        function_code_after = ""
        function_code_after_token_count = 0
        function_name = ""
    else:
        # function_parent = changed_method.long_name
        function_name = get_function_name(changed_method.name)
        function_after_start_line = changed_method.start_line
        function_after_end_line = changed_method.end_line
        function_code_after_token_count = changed_method.token_count

        file_before = blame_commit_modified_file.source_code_before
        file_after = blame_commit_modified_file.source_code

        function_code_after = get_accurate_function_code(
            file_after,
            function_after_start_line,
            function_after_end_line
        )

        changed_method_before = get_pydriller_method_by_long_name(blame_commit_modified_file.methods_before, changed_method.long_name)
        if changed_method_before is not None:
            function_before_start_line = changed_method_before.start_line
            function_before_end_line = changed_method_before.end_line
            function_code_before_token_count = changed_method_before.token_count
            function_code_before = get_accurate_function_code(
                file_before,
                function_before_start_line,
                function_before_end_line
            )
        else:
            print(f'Warning: cannot find the function code before in blame commit, bug_id: {bug_id}')
            function_before_start_line = ""
            function_before_end_line = ""
            function_code_before = ""
            function_code_before_token_count = 0

    commit_message = commit.msg
    commit_author = commit.author.name
    commit_date = commit.committer_date.strftime("%Y-%m-%d %H:%M:%S")
    file_nloc = blame_commit_modified_file.nloc
    file_complexity = blame_commit_modified_file.complexity
    file_token_count = blame_commit_modified_file.token_count

    # 3.1 all functions' name only in the modified file of blame commit.
    functions_name_modified_file_in_commit = []
    for method in blame_commit_modified_file.methods:
        if '.' not in method.name:
            functions_name_modified_file_in_commit.append(get_function_name(method.name))
    # 3.2 all functions' name in all files of blame commit
    functions_name_all_files_in_commit = []
    for m_file in commit.modified_files:
        for method in m_file.methods:
            if '.' not in method.name:
                functions_name_all_files_in_commit.append(get_function_name(method.name))

    # 4.1 co-evolved functions' name in the modified file of blame commit.
    functions_name_co_evolved_modified_file = []
    for method_ in blame_commit_modified_file.changed_methods:
        if '.' not in method_.name and method_.name != function_name:
            functions_name_co_evolved_modified_file.append(get_function_name(method_.name))

    # 4.2 co-evolved functions' name in all files of blame commit.
    functions_name_co_evolved_all_files = []
    for m_file_ in commit.modified_files:
        for method__ in m_file_.changed_methods:
            if '.' not in method__.name and method__.name != function_name:
                functions_name_co_evolved_all_files.append(get_function_name(method__.name))

    # print(f"{bug_id}: size functions_name_co_evolved_modified_file: {len(set(
    # functions_name_co_evolved_modified_file))} || size functions_name_co_evolved_all_files: {len(set(
    # functions_name_co_evolved_all_files))}")

    # 5. find all files' name in that commit
    files_name_in_blame_commit = []
    for m_file in commit.modified_files:
        if '.java' in m_file.filename:
            files_name_in_blame_commit.append(m_file.filename)

    commit_data_info = {
        "commit": {
            "commit_id": commit.hash,
            "commit_message": commit_message,
            "commit_author": commit_author,
            "commit_date": commit_date,
            "commit_parent": commit.parents[0] if bool(commit.parents) else ""
        },
        "function": {
            "function_name": function_name,
            "function_code_before": function_code_before,
            "function_code_after": function_code_after,
            "function_before_start_line": function_before_start_line,
            "function_before_end_line": function_before_end_line,
            "function_after_start_line": function_after_start_line,
            "function_after_end_line": function_after_end_line,
            "function_before_token_count": function_code_before_token_count,
            "function_after_token_count": function_code_after_token_count,
            "functions_name_modified_file": list(set(functions_name_modified_file_in_commit)),
            "functions_name_all_files": list(set(functions_name_all_files_in_commit)),
            "functions_name_co_evolved_modified_file": list(set(functions_name_co_evolved_modified_file)),
            "functions_name_co_evolved_all_files": list(set(functions_name_co_evolved_all_files))
        },
        "file": {
            "file_name": blame_commit_modified_file.filename,
            "file_nloc": file_nloc,
            "file_complexity": file_complexity,
            "file_token_count": file_token_count,
            "file_before": "",
            "file_after": "",
            "file_patch": modified_file_patch,
            "files_name_in_blame_commit": list(set(files_name_in_blame_commit))
        }
    }
    return commit_data_info


def get_function_name(long_name):
    return long_name.split("::")[-1]


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


def get_last_commit_touching_buggy_line_before_fix_commit(repo_path, file_path, buggy_line_number, fixed_commit_id):
    parent_commit = f"{fixed_commit_id}^"  # Parent of the fixed commit

    cmd = [
        "git", "blame", "-l", parent_commit,
        "-L", f"{buggy_line_number},{buggy_line_number}",
        "--", file_path
    ]
    result = subprocess.run(
        cmd,
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"Git blame failed: {result.stderr.strip()}")

    blame_id = result.stdout.strip().split(' ')[0]
    return blame_id.lstrip('^')  # handle ^merge case


if __name__ == "__main__":
    main()
