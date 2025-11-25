import requests

class GiteaClient:
    def __init__(self, url, token, repo_owner, repo_name):
        self.url = url
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
    
    def health_check(self):
        """Проверка доступности Gitea"""
        try:
            response = requests.get(f"{self.url}/api/v1/user", headers=self.headers, timeout=10)
            if response.status_code == 200:
                user_info = response.json()
                return True, f"Gitea OK (user: {user_info.get('login')})"
            else:
                return False, f"Gitea error: {response.status_code}"
        except Exception as e:
            return False, f"Gitea connection failed: {e}"
    
    def ensure_repository(self):
        """Создать репозиторий если не существует"""
        try:
            check_url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}"
            response = requests.get(check_url, headers=self.headers)
            
            if response.status_code == 200:
                return True, "Repository exists"
            elif response.status_code == 404:
                create_url = f"{self.url}/api/v1/user/repos"
                repo_data = {
                    'name': self.repo_name,
                    'description': 'Jira issues synchronization',
                    'private': False,
                    'auto_init': True
                }
                
                response = requests.post(create_url, headers=self.headers, json=repo_data)
                if response.status_code == 201:
                    return True, "Repository created"
                else:
                    return False, f"Error creating repository: {response.text}"
            else:
                return False, f"Error checking repository: {response.text}"
                
        except Exception as e:
            return False, f"Repository error: {e}"
    
    def create_issue(self, jira_issue):
        """Создать issue в Gitea на основе Jira задачи"""
        try:
            issue_key = jira_issue['key']
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/issues"
            
            fields = jira_issue['fields']
            title = f"[{issue_key}] {fields.get('summary', 'No title')}"
            
            body = f"""
## Jira Issue: {issue_key}

**Summary:** {fields.get('summary', 'No summary')}

**Description:**
{fields.get('description', 'No description provided')}

**Status:** {fields.get('status', {}).get('name', 'Unknown')}

**Assignee:** {fields.get('assignee', {}).get('displayName', 'Unassigned')}

---

*Automatically synced from Jira*
"""
            issue_data = {
                'title': title,
                'body': body.strip()
            }
            
            response = requests.post(url, headers=self.headers, json=issue_data)
            
            if response.status_code == 201:
                return True, f"Issue {issue_key} created"
            elif response.status_code == 409:
                return True, f"Issue {issue_key} already exists"
            else:
                return False, f"Failed to create {issue_key}: {response.text}"
                
        except Exception as e:
            return False, f"Error creating issue: {e}"
    
    def get_existing_issues(self):
        """Получить существующие issues"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/issues"
            params = {'state': 'all'}
            
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                issues = response.json()
                return True, issues
            else:
                return False, f"Error fetching issues: {response.text}"
        except Exception as e:
            return False, f"Error getting issues: {e}"