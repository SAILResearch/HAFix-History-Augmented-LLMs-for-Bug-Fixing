import os
import csv
import pandas as pd
from pydriller import Repository
from data_mining_util import is_single_hunk_change, is_single_line, filter_modified_python_files


def main():
    # git_clone_url = "https://github.com/ansible/ansible.git"
    # git_clone_url = "/home/project/fm-apr-replay/subject_projects/ansible"
    # git_clone_url = "/home/project/fm-apr-replay/subject_projects/black"
    # commit_id = "c0a7582e3d4cc8bec3b7f5a6c52b36880dcb57d7"
    # return mining_data_by_project_and_commit(git_clone_url, commit_id)
    bugsinpy_path = "/home/project/BugsInPy"
    subject_projects_base_path = "/home/project/fm-apr-replay/subject_projects/"
    save_file = "/home/project/fm-apr-replay/dataset/bugsinpy_analysis.csv"

    if os.path.exists(save_file):
        os.remove(save_file)
    result = get_bugs_info_from_bugsinpy(bugsinpy_path)
    for git_clone_url, commit_id in result.items():
        for commit, bugsinpy_id in commit_id.items():
            temp = git_clone_url.split("/")
            project_name = temp[len(temp) - 1].split(".git")[0]
            write_project_id_and_commit_id(project_name, git_clone_url, commit, bugsinpy_id, save_file)
    print("Analyze BugsInPy to get basic project and commit information")
    print(f"Save information file to {save_file}")
    label_single_hunk_and_single_line_bug(subject_projects_base_path, save_file)
    print("Label single-hunk and single-line bugs done!")
    data_pd = pd.read_csv(save_file)
    print(f"single-hunk bugs: {data_pd['is_single_hunk'].sum()}")
    print(f"single-line bugs: {data_pd['is_single_line'].sum()}")
    print(f"single-line bugs is inside function: {data_pd['is_in_function'].sum()}")


def label_single_hunk_and_single_line_bug(subject_projects_root_path, csv_file):
    with open(csv_file) as f:
        data = []
        for row in csv.DictReader(f):
            data.append(row)
    header = data[0].keys()
    for row in data:
        git_clone_url = row['project_url']
        temp = git_clone_url.split("/")
        project_dir_relative = temp[len(temp) - 1].split(".git")[0]
        project_local_pwd = subject_projects_root_path + project_dir_relative
        commit_id = row["commit_id"]
        try:
            repository = Repository(
                path_to_repo=project_local_pwd,
                single=commit_id
            )
            commits = repository.traverse_commits()
            commit = next(commits)
        except:
            print(f"cannot have repository: {git_clone_url} {project_local_pwd} {commit_id}")
            continue
        assert len(list(commits)) == 0
        modified_only_python_files = filter_modified_python_files(commit)
        row["num_changed_py_files"] = len(modified_only_python_files)
        row["is_single_hunk"] = 0
        row["is_single_line"] = 0
        if (len(modified_only_python_files) == 1
                and is_single_hunk_change(modified_only_python_files[0].diff_parsed)):
            row["is_single_hunk"] = 1
            if is_single_line(modified_only_python_files[0].diff_parsed, "python"):
                row["is_single_line"] = 1
                row["is_in_function"] = 1 if is_infunction(modified_only_python_files[0]) else 0

    with open(csv_file, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)


def get_bugs_info_from_bugsinpy(bugsinpy_path):
    result = {}
    bugsinpy_project = bugsinpy_path + "/projects"
    bugsinpy_files = os.listdir(bugsinpy_project)
    count = 0
    for bugsinpy_file in bugsinpy_files:
        # project name
        project_dir = os.path.join(bugsinpy_project, bugsinpy_file)
        if not os.path.isdir(project_dir):
            continue
        protect_info = os.path.join(project_dir, 'project.info')
        with open(protect_info, 'rb') as f:
            first_line = f.readlines()[0]
            project_url = first_line.__str__()[14:-4] + ".git"
            if project_url == "https://github.com/jakubroztocil/httpie/.git":
                project_url = "https://github.com/httpie/cli.git"
        bugs_dir = os.path.join(project_dir, 'bugs')
        bug_files = os.listdir(bugs_dir)
        bug_list = {}
        for bug_file in bug_files:
            if not os.path.isdir(os.path.join(bugs_dir, bug_file)):
                continue
            bugsinpy_bug_id = bug_file
            bug_info = os.path.join(bugs_dir, bug_file, 'bug.info')
            with open(bug_info, 'rb') as f:
                for line in f.readlines():
                    if line.startswith(b"fixed_commit_id=") or line.startswith(b"fixed_commit_id ="):
                        commit_id = line.split(b"\"")[1].decode()
                        bug_list[commit_id] = bugsinpy_bug_id
        sorted_list = sorted(bug_list.items(), key=lambda x: int(x[1]))
        result[project_url] = dict(sorted_list)
        for i in range(1, len(dict(sorted_list).values())):
            if int(list(dict(sorted_list).values())[i]) - int(list(dict(sorted_list).values())[i - 1]) != 1:
                print(f"duplicated commit_id in {bugsinpy_file} is : {i + 1}")
        print(f'{bugsinpy_file}: {len(sorted_list)}')
        count += len(sorted_list)
    print("total: " + count.__str__())
    return result


def write_project_id_and_commit_id(project_name: str,
                                   project_url: str,
                                   commit_id: str,
                                   bugsinpy_id: str,
                                   to_file_path: str):
    if not os.path.exists(to_file_path):
        with open(to_file_path, 'w') as f:
            csv_write = csv.writer(f)
            csv_head = ['project_name', 'project_url', 'commit_id', 'bugsinpy_id',
                        'num_changed_py_files', 'is_single_hunk', 'is_single_line', 'is_in_function']
            csv_write.writerow(csv_head)
    with open(to_file_path, 'a+') as f:
        csv_write = csv.writer(f)
        csv_row = [project_name, project_url, commit_id, bugsinpy_id]
        csv_write.writerow(csv_row)


# def main():
#     # parser = argparse.ArgumentParser()
#     # parser.add_argument("project_path")
#     # parser.add_argument("output_path")
#     # parser.add_argument("--lang", default="python")
#     # args = parser.parse_args()
#
#     project_git_url = "https://github.com/django/django.git"
#     project_path = "/home/project/fm-apr-replay/subject_projects/django"
#     output_path = "/home/project/fm-apr-replay/dataset/single_line_fix_commit.jsonl"
#     lang = "python"
#     # 1. only_modifications_with_file_types will pick at least have one file changes related to .py
#     repository = Repository(
#         path_to_repo=project_path,
#         since=datetime.datetime(2017, 1, 1),
#         to=datetime.datetime(2024, 1, 1),
#         only_modifications_with_file_types=['.py'],
#         order="reverse"
#     )
#     commits = repository.traverse_commits()
#     commits_with_single_line_change = []
#     single_line_bug_list = []
#     for commit in tqdm(commits):
#         modified_files = commit.modified_files
#         # 2. one commit only has 1 python file change
#         if len(modified_files) != 1:
#             continue
#         modified_python_file = modified_files[0]
#         # 3. only have MODIFY type, no ADD, DELETE, RENAME or others
#         if modified_python_file.change_type != ModificationType.MODIFY:
#             continue
#         # 4. single-line change
#         if not is_single_line(modified_python_file.diff_parsed, lang):
#             continue
#         if not is_likely_bug(commit.msg):
#             continue
#         print(modified_python_file)
#
#         # parse the diff
#         diff_git = modified_python_file.diff
#         # check what if there are multi-hunk code
#         diff_hunks = parse_hunks(diff_git)
#         # there is only one hunk
#         diff_hunk = diff_hunks[0]
#         diff_hunk_clean = clean_hunk(diff_hunk)
#
#         # compute diff
#         try:
#             diff = code_diff.difference(diff_hunk_clean.before, diff_hunk_clean.after, lang=lang)
#         except Exception:
#             diff = None
#         if diff is not None:
#             sstub_pattern = diff.sstub_pattern()
#
#             # compute edit script
#             edit_script = compute_edit_script_it(diff)
#
#             try:
#                 stmt_diff = diff.statement_diff()
#                 before_diff = stmt_diff.source_text
#                 after_diff = stmt_diff.target_text
#             except ValueError:
#                 before_diff = diff.source_text
#                 after_diff = diff.target_text
#             sstub_pattern_name = sstub_pattern.name
#
#         single_line_bug_object = {
#             "project": commit.project_name,
#             "project_git_url": project_git_url,
#             "commit_sha": commit.hash,
#             "parent_sha": commit.parents[0],
#             "file_path": modified_python_file.old_path,
#             "change_type": modified_python_file.change_type.name,
#             "file_code_before": modified_python_file.source_code_before,
#             "file_code_after": modified_python_file.source_code,
#             "file_complexity": modified_python_file.complexity,
#             "file_LOC": modified_python_file.nloc,
#             "file_token_count": modified_python_file.token_count,
#             "in_function": is_infunction(modified_python_file),
#             "single_token_mod": single_token_mod(modified_python_file.diff, lang),
#             # Diff used to update the code
#             "diff": modified_python_file.diff,
#             "before": diff_hunk_clean.before,
#             "after": diff_hunk_clean.after,
#             "sstub_pattern": "sstub_pattern_name",
#             "edit_script": "edit_script",
#             "author": commit.author.name,
#             "author_email": commit.author.email,
#             # "commit_time": commit.committer_date.date(),
#             "commit_message": commit.msg
#         }
#         single_line_bug_list.append(single_line_bug_object)
#
#     with open(output_path, "w") as output_file:
#         for single_line_bug_object in single_line_bug_list:
#             output_file.write(json.dumps(single_line_bug_object) + "\n")


def is_likely_bug(commit_msg):
    return any(t in commit_msg.lower() for t in ["error", "bug", "fix", "issue", "mistake",
                                                 "incorrect", "fault", "defect", "flaw", "type"])


def is_infunction(modfile):
    return len(modfile.changed_methods) > 0


if __name__ == "__main__":
    main()
