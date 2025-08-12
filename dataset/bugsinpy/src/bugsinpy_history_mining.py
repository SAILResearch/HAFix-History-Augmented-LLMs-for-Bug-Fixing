import json
import os.path
from argparse import ArgumentParser
from pydriller import Git, Commit, ModifiedFile
from data_mining_util import filter_modified_python_files, get_method_by_name, get_superficial_function_code, \
    get_blame_line_commits

CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_DIR_BASE = os.path.abspath(os.path.join(CURRENT_DIR_PATH, '../../../'))
SUBJECT_PROJECTS_BASE_PATH = os.path.abspath(os.path.join(PROJECT_DIR_BASE, 'subject_projects'))


def get_parser():
    parser = ArgumentParser()
    parser.add_argument('--bugsinpy_analysis_file', type=str)
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
    bugs_meta_data_file = os.path.join(PROJECT_DIR_BASE, "dataset", "bugsinpy", "bugs_meta_data.json")
    history_base_path = os.path.join(PROJECT_DIR_BASE, "dataset", "bugsinpy", "history_blame")
    if not os.path.exists(history_base_path):
        os.makedirs(history_base_path)
    is_mine_recursive_blame_commits = True

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
        commit = git_repo.get_commit(bug_value['commit']['commit_id'])

        modified_only_python_files = filter_modified_python_files(commit)
        assert len(modified_only_python_files) == 1
        modified_file = modified_only_python_files[0]

        # 1. get the line-level buggy-line blame commit
        blame_commit_ids = git_repo.get_commits_last_modified_lines(commit, modified_file)
        # after testing, all 68 bugs only have one bug-introducing commit
        assert len(blame_commit_ids.values()) == 1
        assert len(blame_commit_ids.get(bug_value['file']['file_path'])) == 1

        blame_commit_id = blame_commit_ids.get(bug_value['file']['file_path']).pop()
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
            blame_commit,
            blame_commit_modified_file,
            bug_value['function']['function_name'],
            bug_value['function']['function_parent']
        )

        # 6. recursive-blame
        recursive_blame_commits = {}
        if is_mine_recursive_blame_commits:
            recursive_blame_function_lines = {}
            recursive_blame_commits_data = {}
            function_before_start_line = blame_commit_data["function"]["function_before_start_line"]
            function_before_end_line = blame_commit_data["function"]["function_before_end_line"]
            if function_before_start_line != "" and function_before_end_line != "":
                recursive_blame_function_lines = get_blame_line_commits(
                    git_repo, blame_commit, blame_commit_modified_file,
                    function_before_start_line, function_before_end_line
                )
                commit_ids_set = set()
                for line_num, commit_code_dict in recursive_blame_function_lines.items():
                    if commit_code_dict['valid'] == 1:
                        commit_ids_set.add(commit_code_dict["commit_id"])

                for line_blame_commit_id in commit_ids_set:
                    if line_blame_commit_id in recursive_blame_commits_data:
                        continue
                    recursive_line_blame_commit = git_repo.get_commit(line_blame_commit_id)
                    recursive_blame_commit_modified_file = get_modified_file_by_name(
                        bug_value['file']['file_name'],
                        recursive_line_blame_commit
                    )
                    if recursive_blame_commit_modified_file is None:
                        print(f"Cannot find the corresponding modified file in recursive blame commit: "
                              f"{bug_id} {project_local_path} {bug_value['commit']['commit_id']} {blame_commit_id} {line_blame_commit_id}")
                        continue

                    recursive_blame_commit_data = mining_history_data_from_commit(
                        recursive_line_blame_commit,
                        recursive_blame_commit_modified_file,
                        bug_value['function']['function_name'],
                        bug_value['function']['function_parent']
                    )
                    recursive_blame_commits_data[line_blame_commit_id] = recursive_blame_commit_data

                # Sort commits by date, latest commit first show
                sorted_list = sorted(recursive_blame_commits_data.items(), key=lambda x: x[1]['commit']['commit_date'], reverse=True)
                recursive_blame_commits_data = dict(sorted_list)

                recursive_blame_commits["recursive_blame_function_lines"] = recursive_blame_function_lines
                recursive_blame_commits["commits"] = recursive_blame_commits_data

            if not bool(recursive_blame_function_lines) or not bool(recursive_blame_commits_data):
                print(f"bug_id: {bug_id} has no recursive blame commits information")

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
        if is_mine_recursive_blame_commits:
            history_data["recursive_blame_commits"] = recursive_blame_commits
        json.dump(history_data, open(history_save_path, 'w'), indent=2)


def mining_history_data_from_commit(commit: Commit, commit_modified_file: ModifiedFile,
                                    function_name: str, function_parent: str):
    # 2. check on this point: function-level difference and file-level difference
    # what is the changed line number?
    # what is the line-surrounded function?
    # Here don't use path, using name instead as the path might be changed

    commit_modified_file_before = commit_modified_file.source_code_before
    commit_modified_file_after = commit_modified_file.source_code

    commit_modified_file_patch = commit_modified_file.diff

    if function_parent != "":
        superficial_start_line_before, superficial_end_line_before, commit_function_code_before = get_superficial_function_code(
            commit_modified_file_before,
            function_name,
            function_parent
        )
        superficial_start_line_after, superficial_end_line_after, commit_function_code_after = (
            get_superficial_function_code(
                commit_modified_file_after,
                function_name,
                function_parent
            )
        )

        blame_commit_method_before = get_method_by_name(
            function_name,
            superficial_start_line_before,
            superficial_end_line_before,
            commit_modified_file.methods_before
        )
        if blame_commit_method_before is not None:
            commit_function_code_before_token_count = blame_commit_method_before.token_count
        else:
            commit_function_code_before_token_count = 0

        method_after = get_method_by_name(
            function_name,
            superficial_start_line_after,
            superficial_end_line_after,
            commit_modified_file.changed_methods
        )
        if method_after is not None:
            commit_function_code_after_token_count = method_after.token_count
        else:
            commit_function_code_after_token_count = 0
    else:
        commit_function_code_before = ""
        commit_function_code_after = ""
        superficial_start_line_before = ""
        superficial_end_line_before = ""
        superficial_start_line_after = ""
        superficial_end_line_after = ""
        commit_function_code_before_token_count = 0
        commit_function_code_after_token_count = 0

    commit_message = commit.msg
    commit_author = commit.author.name
    commit_date = commit.committer_date.strftime("%Y-%m-%d %H:%M:%S")
    file_nloc = commit_modified_file.nloc
    file_complexity = commit_modified_file.complexity
    file_token_count = commit_modified_file.token_count

    # 3.1 all functions' name only in the modified file of blame commit.
    functions_name_modified_file_in_commit = []
    for method in commit_modified_file.methods:
        if '.' not in method.name:
            functions_name_modified_file_in_commit.append(method.name)
    # 3.2 all functions' name in all files of blame commit
    functions_name_all_files_in_commit = []
    for m_file in commit.modified_files:
        for method in m_file.methods:
            if '.' not in method.name:
                functions_name_all_files_in_commit.append(method.name)

    # 4.1 co-evolved functions' name in the modified file of blame commit.
    functions_name_co_evolved_modified_file = []
    for method_ in commit_modified_file.changed_methods:
        if '.' not in method_.name and method_.name != function_name:
            functions_name_co_evolved_modified_file.append(method_.name)

    # 4.2 co-evolved functions' name in all files of blame commit.
    functions_name_co_evolved_all_files = []
    for m_file_ in commit.modified_files:
        for method__ in m_file_.changed_methods:
            if '.' not in method__.name and method__.name != function_name:
                functions_name_co_evolved_all_files.append(method__.name)

    # print(f"{bug_id}: size functions_name_co_evolved_modified_file: {len(set(
    # functions_name_co_evolved_modified_file))} || size functions_name_co_evolved_all_files: {len(set(
    # functions_name_co_evolved_all_files))}")

    # 5. find all files' name in that commit
    files_name_in_blame_commit = []
    for m_file in commit.modified_files:
        if '.py' in m_file.filename:
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
            "function_code_before": commit_function_code_before,
            "function_code_after": commit_function_code_after,
            "function_before_start_line": superficial_start_line_before,
            "function_before_end_line": superficial_end_line_before,
            "function_after_start_line": superficial_start_line_after,
            "function_after_end_line": superficial_end_line_after,
            "function_before_token_count": commit_function_code_before_token_count,
            "function_after_token_count": commit_function_code_after_token_count,
            "functions_name_modified_file": list(set(functions_name_modified_file_in_commit)),
            "functions_name_all_files": list(set(functions_name_all_files_in_commit)),
            "functions_name_co_evolved_modified_file": list(set(functions_name_co_evolved_modified_file)),
            "functions_name_co_evolved_all_files": list(set(functions_name_co_evolved_all_files))
        },
        "file": {
            "file_name": commit_modified_file.filename,
            "file_nloc": file_nloc,
            "file_complexity": file_complexity,
            "file_token_count": file_token_count,
            "file_before": commit_modified_file_before,
            "file_after": commit_modified_file_after,
            "file_patch": commit_modified_file_patch,
            "files_name_in_blame_commit": list(set(files_name_in_blame_commit))
        }
    }
    return commit_data_info


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


if __name__ == "__main__":
    main()
