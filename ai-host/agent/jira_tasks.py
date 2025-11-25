from jira_client import JiraClient

class JiraTasks:
    def __init__(self, jira_client):
        self.jira = jira_client
    
    def get_my_todo_tasks(self, username):
        """Получить задачи назначенные на меня со статусом To Do"""
        jql = f"assignee = '{username}' AND status = 'To Do'"
        success, result = self.jira.get_issues(jql=jql)
        
        if success:
            return True, result
        else:
            return False, result
    
    def get_my_in_progress_tasks(self, username):
        """Получить задачи назначенные на меня со статусом In Progress"""
        jql = f"assignee = '{username}' AND status = 'In Progress'"
        success, result = self.jira.get_issues(jql=jql)
        
        if success:
            return True, result
        else:
            return False, result
    
    def get_task_details(self, issue_key):
        """Получить детальную информацию о задаче"""
        try:
            url = f"{self.jira.url}/rest/api/2/issue/{issue_key}"
            response = self.jira.session.get(url)
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Error getting task details: {response.status_code}"
        except Exception as e:
            return False, f"Error fetching task details: {e}"
    
    def transition_task(self, issue_key, transition_name):
        """Изменить статус задачи"""
        try:
            # Сначала получаем доступные переходы
            transitions_url = f"{self.jira.url}/rest/api/2/issue/{issue_key}/transitions"
            response = self.jira.session.get(transitions_url)
            
            if response.status_code != 200:
                return False, f"Error getting transitions: {response.status_code}"
            
            transitions = response.json().get('transitions', [])
            target_transition = None
            
            # Ищем нужный переход
            for transition in transitions:
                if transition['name'].lower() == transition_name.lower():
                    target_transition = transition
                    break
            
            if not target_transition:
                available_transitions = [t['name'] for t in transitions]
                return False, f"Transition '{transition_name}' not found. Available: {available_transitions}"
            
            # Выполняем переход
            transition_data = {
                'transition': {
                    'id': target_transition['id']
                }
            }
            
            response = self.jira.session.post(transitions_url, json=transition_data)
            
            if response.status_code == 204:
                return True, f"Task {issue_key} moved to {transition_name}"
            else:
                return False, f"Error transitioning task: {response.text}"
                
        except Exception as e:
            return False, f"Error transitioning task: {e}"
    
    def add_comment(self, issue_key, comment):
        """Добавить комментарий к задаче"""
        try:
            url = f"{self.jira.url}/rest/api/2/issue/{issue_key}/comment"
            comment_data = {
                'body': comment
            }
            
            response = self.jira.session.post(url, json=comment_data)
            
            if response.status_code == 201:
                return True, "Comment added"
            else:
                return False, f"Error adding comment: {response.text}"
                
        except Exception as e:
            return False, f"Error adding comment: {e}"