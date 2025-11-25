import requests

class JiraClient:
    def __init__(self, url, username, password, project_key):
        self.url = url
        self.project_key = project_key
        self.session = requests.Session()
        self.session.auth = (username, password)
    
    def health_check(self):
        """Проверка доступности Jira"""
        try:
            response = self.session.get(f"{self.url}/rest/api/2/serverInfo", timeout=10)
            if response.status_code == 200:
                info = response.json()
                return True, f"Jira OK (v{info.get('version')})"
            else:
                return False, f"Jira error: {response.status_code}"
        except Exception as e:
            return False, f"Jira connection failed: {e}"
    
    def get_issues(self, jql=None, max_results=10):
        """Получить задачи из Jira"""
        try:
            if not jql:
                jql = f"project = {self.project_key}"
            
            url = f"{self.url}/rest/api/2/search"
            params = {
                'jql': jql,
                'maxResults': max_results,
                'fields': 'key,summary,description,status,assignee,created'
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                issues = data.get('issues', [])
                return True, issues
            else:
                return False, f"Jira API error: {response.status_code}"
                
        except Exception as e:
            return False, f"Error fetching Jira issues: {e}"
    
    def get_projects(self):
        """Получить список проектов"""
        try:
            url = f"{self.url}/rest/api/2/project"
            response = self.session.get(url)
            
            if response.status_code == 200:
                projects = response.json()
                return True, projects
            else:
                return False, f"Error getting projects: {response.status_code}"
        except Exception as e:
            return False, f"Error fetching projects: {e}"