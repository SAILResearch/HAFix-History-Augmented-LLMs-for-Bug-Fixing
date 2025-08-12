import json
import os
import requests
from ghapi.all import GhApi
from bs4 import BeautifulSoup
from pathlib import Path

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
BASE_DIR = Path(__file__).resolve().parent.parent


def main():
    bugs_meta_data_file = BASE_DIR / "defects4j_bugs_meta_data.json"
    bugs_meta_data: dict = json.load(open(bugs_meta_data_file, 'r'))
    bugs_description_file = BASE_DIR / "defects4j_bugs_description.json"
    if os.path.exists(bugs_description_file):
        os.remove(bugs_description_file)

    result = {}
    for bug_id, bug_value in bugs_meta_data.items():
        bug_description_link = bug_value['bug_description_link']
        # if bug_value['bug_description_link'] != "" else bug_value['commit']['commit_message']

        description = ""
        desc_source = ""
        if 'https://github.com/' in bug_description_link:
            # github issue page: 8 projects
            description = mining_bug_desc_from_github_issue_page(
                bug_description_link,
                bugs_meta_data[bug_id]['project_url']
            )
            desc_source = "github_issue"

        elif 'https://issues.apache.org/jira/' in bug_description_link:
            # apache jira page: 7 projects
            description = mining_bug_desc_from_apache_jira(bug_description_link)
            desc_source = "jira"

        elif 'https://storage.googleapis.com/' in bug_description_link:
            # google json file
            description = mining_bug_desc_from_google_code_archive(bug_description_link)
            desc_source = "google"

        elif 'https://sourceforge.net' in bug_description_link:
            description = get_sourceforge_bug_details(bug_description_link)
            desc_source = "sourceforge"

        if bug_description_link == "" or description == "":
            description = bug_value['commit']['commit_message']
            desc_source = "commit_msg"

        result[bug_id] = {'description': description, 'desc_source': desc_source}
        json.dump(result, open(bugs_description_file, 'w'), indent=2)


def mining_bug_desc_from_github_issue_page(github_issue_link, project_url):
    issue_number = github_issue_link.split('/')[-1]
    project_owner = project_url.split('/')[-2]
    project_name = project_url.split('/')[-1].split('.git')[0]
    api = GhApi(owner=project_owner, repo=project_name, token=GITHUB_TOKEN)
    try:
        project_issue = api.issues.get(issue_number)
        title = project_issue.title if project_issue.title else ""
        body = project_issue.body if project_issue.body else ""
        description = f"{title}\n{body}\n"
    except:
        print(f"Failed to retrieve github_issue_link. {github_issue_link}")
        description = ""
    return description


def mining_bug_desc_from_apache_jira(jira_link):
    # Extract the issue key from the URL
    issue_key = jira_link.rstrip('/').split('/')[-1]
    api_url = f'https://issues.apache.org/jira/rest/api/2/issue/{issue_key}?fields=summary,description'
    response = requests.get(api_url, headers={'Accept': 'application/json'})

    if response.status_code == 200:
        data = response.json()
        description = f"{data['fields']['summary']}\n{data['fields']['description']}"
    else:
        description = ""
        print(f"Failed to retrieve jira_link. {jira_link}")
    return description


def mining_bug_desc_from_google_code_archive(google_link):
    response = requests.get(google_link)
    if response.status_code == 200:
        data = response.json()
        title = data.get('summary', "").strip()
        comments = data.get('comments', [])
        comment_first = comments[0].get('content', "").strip() if comments else ""
        if not title and not comment_first:
            return ""
        description = f"{title}\n{comment_first}"

    else:
        print(f"Failed to retrieve google_link. {google_link}")
        description = ""
    return description


def get_sourceforge_bug_details(sourceforge_link):
    # Example usage
    # sourceforge_link = 'https://sourceforge.net/p/jfreechart/bugs/983'
    response = requests.get(sourceforge_link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract the title
        issue_number_tag = soup.find('h2', class_='dark title')
        title = issue_number_tag.get_text().strip() if issue_number_tag else ''

        # Get the description from the <div id="ticket_content"> inside <div class="markdown_content">
        content_div = soup.find('div', {'id': 'ticket_content'})
        markdown_div = content_div.find('div', class_='markdown_content') if content_div else None
        content = markdown_div.get_text().strip() if markdown_div else ''

        if not title and not content:
            return ""
        description = f"{title}\n{content}"
    else:
        print(f"Failed to retrieve sourceforge_link. {sourceforge_link}")
        description = ""
    return description


if __name__ == '__main__':
    main()
