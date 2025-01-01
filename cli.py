import os
import json
import requests
from requests.auth import HTTPBasicAuth

API_ISSUE_ENDPOINT = "/rest/api/3/issue"

config_file = "jira_config.json"  # file will be created after the user inputs the Jira credentials

# load credentials from the config file
def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            return json.load(file)
    return None

# save credentials to the config file
def save_config(jira_url, username, api_token):
    config_data = {
        "jira_url": jira_url,
        "username": username,
        "api_token": api_token
    }
    with open(config_file, 'w') as file:
        json.dump(config_data, file, indent=4)
    print("Configuration saved successfully.")

# function to input and save Jira credentials
def setup_jira_credentials():
    print("Setup Jira Configuration")
    jira_url = input("Enter your Jira URL (e.g., https://your-domain.atlassian.net/): ").strip()
    username = input("Enter your Jira username (email): ").strip()
    api_token = input("Enter your Jira API token: ").strip()
    save_config(jira_url, username, api_token)

def fetch_issue(issue_key, auth, headers):
    api_endpoint_search = "/rest/api/3/search"
    jql_query = f"key = {issue_key}"

    response = requests.get(
        auth['jira_url'] + api_endpoint_search,
        auth=auth['auth'],
        headers=headers,
        params={
            "jql": jql_query,
            "maxResults": 1,
            "fields": "summary,status,description,issuetype"
        }
    )

    if response.status_code == 200:
        response_data = response.json()
        if "issues" in response_data:
            issues = response_data['issues']
            if issues:
                issue = issues[0]
                issue_key = issue['key']
                issue_summary = issue['fields']['summary']
                issue_status = issue['fields']['status']['name']
                description_field = issue['fields'].get('description', None)
                issue_type = issue['fields']['issuetype']['name']
                description_text = "No description available"
                if description_field:
                    description_text = ""
                    if isinstance(description_field, dict) and 'content' in description_field:
                        for content in description_field['content']:
                            if 'content' in content:
                                for text_item in content['content']:
                                    if text_item['type'] == 'text':
                                        description_text += text_item['text']
                description_text = description_text.strip()
                print(f"\nIssue Key: {issue_key}")
                print(f"Summary: {issue_summary}")
                print(f"Status: {issue_status}")
                print(f"Issue Type: {issue_type}")
                print(f"Description: {description_text}")
    else:
        print("Failed to fetch issue:", response.status_code, response.text)

def check_if_issue_exists(issue_key, auth, headers):
    api_endpoint_search = "/rest/api/3/search"
    jql_query = f"key = {issue_key}"

    response = requests.get(
        auth['jira_url'] + api_endpoint_search,
        auth=auth['auth'],
        headers=headers,
        params={
            "jql": jql_query,
            "maxResults": 1,
        }
    )

    if response.status_code == 200:
        response_data = response.json()
        if "issues" in response_data and response_data['issues']:
            return True
    return False

def create_issue(issue_summary, issue_status, issue_description, issue_type="Task", auth=None, headers=None):
    formatted_description = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": issue_description
                    }
                ]
            }
        ]
    }

    issue_data = {
        "fields": {
            "project": {
                "key": "SCRUM"
            },
            "summary": issue_summary,
            "description": formatted_description,
            "issuetype": {
                "name": issue_type
            }
        }
    }

    response = requests.post(
        auth['jira_url'] + API_ISSUE_ENDPOINT, 
        auth=auth['auth'],
        headers=headers,
        data=json.dumps(issue_data)
    )

    if response.status_code == 201:
        response_data = response.json()
        print(f"\nIssue created successfully!")
        print(f"Issue Key: {response_data['key']}")
        print(f"Summary: {response_data['fields']['summary']}")
        print(f"Status: {response_data['fields']['status']['name']}")
        print(f"Issue Type: {response_data['fields']['issuetype']['name']}")
        print(f"Description: {response_data['fields']['description']['content'][0]['content'][0]['text']}")
    else:
        print("Failed to create issue:", response.status_code, response.text)

def main():
    config = load_config()

    if not config:
        print("Configuration not found. Please set up your Jira credentials.")
        setup_jira_credentials()
        config = load_config()

    print("Welcome to the Jira CLI tool!")
    print("1. Fetch an issue")
    print("2. Create a new issue")

    auth = {
        "jira_url": config["jira_url"],
        "auth": HTTPBasicAuth(config["username"], config["api_token"])
    }
    headers = {"Content-Type": "application/json"}

    choice = input("Choose an option (1 or 2): ").strip()

    if choice == "1":
        issue_key = input("Enter the Jira issue key (e.g., SCRUM-2): ").strip()
        fetch_issue(issue_key, auth, headers)

    elif choice == "2":
        issue_key = input("Enter the Jira issue key (e.g., SCRUM-2): ").strip()

        if check_if_issue_exists(issue_key, auth, headers):
            print(f"\nIssue with key {issue_key} already exists.")
        else:
            issue_summary = input("Enter the summary for the new issue: ").strip()
            issue_status = input("Enter the status for the new issue (To Do/ In Progress/ Done): ").strip()
            issue_description = input("Enter the description for the new issue: ").strip()
            issue_type = input("Enter the issue type (Task/Bug): ").strip()

            create_issue(issue_summary, issue_status, issue_description, issue_type, auth, headers)

    else:
        print("Invalid choice. Please choose 1 or 2.")

if __name__ == "__main__":
    main()
