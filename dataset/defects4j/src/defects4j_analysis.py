import os
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
base_path = BASE_DIR / "defects4j" / "framework" / "projects"


def is_single_line_bug(patch_file):
    with open(patch_file, 'r', encoding='utf-8', errors='replace') as file:
        lines = file.readlines()

    added_lines = 0
    removed_lines = 0
    diff_started = False
    changes = []

    for index, line in enumerate(lines):
        if line.startswith('@@'):
            diff_started = True
        elif diff_started:
            if line.startswith('+') and not line.startswith('+++'):
                added_lines += 1
                changes.append(index)
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines += 1
                changes.append(index)

    total_changes = added_lines + removed_lines

    # No, actually if it is add a new line or deleting a line, there will be no blame commit
    # if (added_lines == 1 and removed_lines == 0) or (removed_lines == 1 and added_lines == 0):
    #     return True
    if added_lines == 1 and removed_lines == 1:
        # Check if the added and removed lines are consecutive
        if abs(changes[0] - changes[1]) == 1:
            return True
    return False


def is_single_hunk_bug(patch_file):
    with open(patch_file, 'r', encoding='utf-8', errors='replace') as file:
        lines = file.readlines()

    hunk_started = False
    changes = []

    for index, line in enumerate(lines):
        if line.startswith('@@'):
            if hunk_started and changes:  # Found a second hunk
                return False  # More than one hunk detected
            hunk_started = True
            changes = []  # Reset changes for a new hunk
            continue

        if hunk_started:
            if line.startswith('+') and not line.startswith('+++'):
                changes.append(index)
            elif line.startswith('-') and not line.startswith('---'):
                changes.append(index)

    # Check if changes form a single contiguous block
    if changes and max(changes) - min(changes) + 1 == len(changes):
        return True  # All changed lines are consecutive
    return False


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


if __name__ == '__main__':

    active_bugs = get_active_bugs(base_path)
    single_line_bugs, single_hunk_bugs = categorize_bugs(base_path, active_bugs)

    total_single_line_bugs = sum(len(bugs) for bugs in single_line_bugs.values())
    total_single_hunk_bugs = sum(len(bugs) for bugs in single_hunk_bugs.values())

    print(f'Total single-line bugs: {total_single_line_bugs}')
    print(f'Total single-hunk bugs: {total_single_hunk_bugs}\n')

    i = 0
    for project in sorted(set(single_line_bugs.keys()) | set(single_hunk_bugs.keys())):
        i += 1
        print(f'Project {i}: {project} | total single-line bugs: {len(single_line_bugs[project])} | total single-hunk '
              f'bugs: {len(single_hunk_bugs[project])}')

        if project in single_line_bugs:
            print(f'  Single-line Bugs: {", ".join(map(str, sorted(single_line_bugs[project], key=int)))}')
        if project in single_hunk_bugs:
            print(f'  Single-hunk Bugs: {", ".join(map(str, sorted(single_hunk_bugs[project], key=int)))}\n\n')
