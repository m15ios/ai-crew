import requests
import base64
from datetime import datetime

class GiteaGitClient:
    def __init__(self, url, token, repo_owner, repo_name):
        self.url = url
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.headers = {
            'Authorization': f'token {token}',
            'Content-Type': 'application/json'
        }
    
    def get_file_content(self, file_path, branch="main"):
        """Получить содержимое файла из репозитория"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            params = {'ref': branch}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                content_data = response.json()
                # Декодируем base64 содержимое
                content = base64.b64decode(content_data['content']).decode('utf-8')
                return True, content, content_data['sha']  # sha нужен для обновления файла
            elif response.status_code == 404:
                return False, "File not found", None
            else:
                return False, f"Error getting file: {response.text}", None
                
        except Exception as e:
            return False, f"Error reading file: {e}", None
    
    def create_or_update_file(self, file_path, content, commit_message, branch="main"):
        """Создать или обновить файл в репозитории"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            
            print(f"   🔍 Checking file {file_path}...")
            
            # Сначала пытаемся получить текущий файл чтобы получить sha (для обновления)
            file_exists, existing_content, sha = self.get_file_content(file_path, branch)
            
            if file_exists:
                print(f"   📝 File exists, SHA: {sha}")
            else:
                print(f"   📄 File not found, creating new")
            
            # Подготавливаем данные для коммита
            file_data = {
                'message': commit_message,
                'content': base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                'branch': branch,
            }
            
            # Если файл существует, добавляем sha для обновления
            if file_exists:
                file_data['sha'] = sha
                print(f"   🔧 Adding SHA to update: {sha[:8]}...")
            
            print(f"   🚀 Sending request to Gitea...")
            response = requests.post(url, headers=self.headers, json=file_data)
            
            if response.status_code == 201:
                action = "updated" if file_exists else "created"
                return True, f"File {file_path} {action} successfully"
            else:
                error_text = response.text
                print(f"   ❌ Gitea API error: {error_text}")
                
                # Если файл уже существует, но SHA не подошел, пробуем получить актуальный SHA
                if "already exists" in error_text and file_exists:
                    print(f"   🔄 SHA might be outdated, refreshing...")
                    # Получаем актуальный SHA
                    file_exists, existing_content, new_sha = self.get_file_content(file_path, branch)
                    if file_exists and new_sha != sha:
                        print(f"   🔄 Using new SHA: {new_sha[:8]}...")
                        file_data['sha'] = new_sha
                        response = requests.post(url, headers=self.headers, json=file_data)
                        
                        if response.status_code == 201:
                            return True, f"File {file_path} updated successfully with new SHA"
                        else:
                            return False, f"Error even with new SHA: {response.text}"
                
                return False, f"Error creating/updating file: {error_text}"
                
        except Exception as e:
            return False, f"Error with file operation: {e}"
    
    def force_update_file(self, file_path, content, commit_message, branch="main"):
        """Принудительное обновление файла (удалить и создать заново)"""
        try:
            print(f"   💥 Force updating file {file_path}...")
            
            # Сначала удаляем файл
            delete_success = self.delete_file(file_path, commit_message + " [delete old]", branch)
            
            if delete_success:
                # Затем создаем заново
                return self.create_or_update_file(file_path, content, commit_message + " [recreate]", branch)
            else:
                return False, "Failed to delete file for force update"
                
        except Exception as e:
            return False, f"Error force updating file: {e}"
    
    def delete_file(self, file_path, commit_message, branch="main"):
        """Удалить файл из репозитория"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/contents/{file_path}"
            
            # Получаем текущий файл чтобы получить sha
            file_exists, existing_content, sha = self.get_file_content(file_path, branch)
            
            if not file_exists:
                return True  # Файл уже не существует
                
            delete_data = {
                'message': commit_message,
                'sha': sha,
                'branch': branch,
            }
            
            response = requests.delete(url, headers=self.headers, json=delete_data)
            
            if response.status_code == 200:
                print(f"   🗑️  File {file_path} deleted")
                return True
            else:
                print(f"   ❌ Error deleting file: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error deleting file: {e}")
            return False
    
    def create_file(self, file_path, content, commit_message, branch="main"):
        """Создать новый файл (только если не существует)"""
        try:
            # Проверяем существует ли файл
            file_exists, _, _ = self.get_file_content(file_path, branch)
            
            if file_exists:
                return False, f"File {file_path} already exists"
            
            return self.create_or_update_file(file_path, content, commit_message, branch)
            
        except Exception as e:
            return False, f"Error creating file: {e}"
    
    def update_file(self, file_path, content, commit_message, branch="main"):
        """Обновить существующий файл"""
        try:
            # Проверяем существует ли файл
            file_exists, _, sha = self.get_file_content(file_path, branch)
            
            if not file_exists:
                return False, f"File {file_path} not found"
            
            return self.create_or_update_file(file_path, content, commit_message, branch)
            
        except Exception as e:
            return False, f"Error updating file: {e}"
    
    def list_files(self, path="", branch="main"):
        """Получить список файлов в директории"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/contents/{path}"
            params = {'ref': branch}
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                files = response.json()
                file_list = []
                for file_info in files:
                    file_list.append({
                        'name': file_info['name'],
                        'path': file_info['path'],
                        'type': file_info['type'],  # 'file' или 'dir'
                        'size': file_info.get('size', 0)
                    })
                return True, file_list
            else:
                return False, f"Error listing files: {response.text}"
                
        except Exception as e:
            return False, f"Error listing files: {e}"
    
    def get_branches(self):
        """Получить список веток репозитория"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/branches"
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                branches = response.json()
                return True, branches
            else:
                return False, f"Error getting branches: {response.text}"
                
        except Exception as e:
            return False, f"Error getting branches: {e}"
    
    def get_commits(self, branch="main", limit=5):
        """Получить последние коммиты для проверки времени"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}/commits"
            params = {
                'sha': branch,
                'limit': limit
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                commits = response.json()
                return True, commits
            else:
                return False, f"Error getting commits: {response.text}"
                
        except Exception as e:
            return False, f"Error getting commits: {e}"
    
    def health_check(self):
        """Проверка доступности репозитория"""
        try:
            url = f"{self.url}/api/v1/repos/{self.repo_owner}/{self.repo_name}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                repo_info = response.json()
                return True, f"Repository accessible: {repo_info['full_name']}"
            else:
                return False, f"Repository not accessible: {response.status_code}"
                
        except Exception as e:
            return False, f"Repository health check failed: {e}"