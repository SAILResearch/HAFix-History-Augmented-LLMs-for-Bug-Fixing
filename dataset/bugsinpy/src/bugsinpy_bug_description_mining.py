import json
import os
import csv
from pathlib import Path
from ghapi.all import GhApi

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    github_issue_file = BASE_DIR / "issues.csv"
    bugs_meta_data_file = BASE_DIR / "bugs_meta_data.json"
    bugs_description_file = BASE_DIR / "github_issue" / "bugs_description.json"

    if os.path.exists(bugs_description_file):
        os.remove(bugs_description_file)
    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
    result = {}
    with open(github_issue_file) as f:
        data = []
        for row in csv.DictReader(f):
            data.append(row)
    for i, issue_info in enumerate(data):
        description = ""
        bug_id = issue_info['id']
        issue_link = issue_info['issue_link']
        if issue_link.strip() == 'no':
            description = bugs_meta_data[bug_id]['commit']['commit_message']
            desc_source = "commit_msg"
        else:
            issue_number = issue_link.split('/')[-1]
            project_url = bugs_meta_data[bug_id]['project_url']
            project_owner = project_url.split('/')[-2]
            project_name = project_url.split('/')[-1].split('.git')[0]
            api = GhApi(owner=project_owner, repo=project_name, token=GITHUB_TOKEN)
            project_issue = api.issues.get(issue_number)
            if project_issue is None:
                continue
            title = project_issue.title if project_issue.title else ""
            body = project_issue.body if project_issue.body else ""
            description += f"{title}\n{body}\n"
            desc_source = "github_issue"
        result[bug_id] = {'description': description, 'desc_source': desc_source}
        json.dump(result, open(bugs_description_file, 'w'), indent=2)


if __name__ == '__main__':
    main()
