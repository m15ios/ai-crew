import os
import sys
import time
import schedule
from datetime import datetime
from config_loader import load_config
from jira_client import JiraClient
from gitea_git_client import GiteaGitClient
from jira_agent import JiraTaskAgent
from review_agent import ReviewAgent
from ai_client import AIClient

# Отключаем буферизацию вывода
sys.stdout = open(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), 'w', buffering=1)

print("🚀 Jira-Gitea Agents Starting...")

class JiraGiteaAgent:
    def __init__(self):
        print("🔧 Loading configuration and initializing clients...")
        
        # Загружаем конфигурацию
        self.config = load_config()
        
        # Инициализируем клиенты
        self.jira = JiraClient(
            url=self.config['jira']['url'],
            username=self.config['jira']['username'],
            password=self.config['jira']['password'],
            project_key=self.config['jira']['project_key']
        )
        
        # Инициализируем Git клиент
        self.git = GiteaGitClient(
            url=self.config['gitea']['url'],
            token=self.config['gitea']['token'],
            repo_owner=self.config['gitea']['repo_owner'],
            repo_name=self.config['gitea']['repo_name']
        )
        
        # Инициализируем AI клиент
        self.ai = AIClient(
            model_url=self.config['ai']['model_url']
        )
        
        
        # Инициализируем агента обработки задач
        self.task_agent = JiraTaskAgent(
            jira_client=self.jira,
            gitea_git_client=self.git,
            username=self.config['jira']['agent_username']
        )
        
        # Инициализируем агента ревью
        self.review_agent = ReviewAgent(
            jira_client=self.jira,
            ai_client=self.ai,  # ← Передаем AI клиент
            username=self.config['jira']['agent_username']
        )
        
        print("✅ All clients and agents initialized")

    def health_check(self):
        """Проверка доступности всех сервисов"""
        print("🏥 Health check...")
        
        # Проверяем Jira
        jira_ok, jira_msg = self.jira.health_check()
        print(f"   Jira: {'✅' if jira_ok else '❌'} {jira_msg}")
        
        # Проверяем Gitea Git
        git_ok, git_msg = self.git.health_check()
        print(f"   Gitea Git: {'✅' if git_ok else '❌'} {git_msg}")
        
        # Проверяем AI
        ai_ok, ai_msg = self.ai.health_check()
        print(f"   AI Model: {'✅' if ai_ok else '❌'} {ai_msg}")
        
        return jira_ok and git_ok and ai_ok

    def ensure_repository(self):
        """Обеспечиваем существование репозитория"""
        try:
            repo_ok, repo_msg = self.git.health_check()
            if repo_ok:
                print("✅ Repository is accessible")
                return True
            else:
                print(f"❌ Repository issue: {repo_msg}")
                return False
        except Exception as e:
            print(f"❌ Repository check error: {e}")
            return False

    def process_tasks(self):
        """Обработка In Progress задач в Jira (первый агент)"""
        print(f"\n🤖 Task processing started at {datetime.now().strftime('%H:%M:%S')}")
        
        if not self.health_check():
            print("❌ Services not available for task processing")
            return
        
        # Проверяем репозиторий
        if not self.ensure_repository():
            return
        
        self.task_agent.process_my_tasks()

    def review_tasks(self):
        """Проверка задач для ревью (второй агент)"""
        self.review_agent.check_review_tasks()

    def show_repository_status(self):
        """Показать статус репозитория"""
        moscow_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S MSK')
        print(f"\n🐙 Repository status at {moscow_time}")
        
        if not self.git.health_check()[0]:
            print("❌ Git client not available")
            return
        
        # Получаем список файлов в репозитории
        success, files = self.git.list_files()
        if success:
            task_files = [f for f in files if f['name'].endswith('.txt') and f['type'] == 'file']
            print(f"   📁 Task files in repository: {len(task_files)}")
            for file in task_files:
                print(f"      - {file['name']}")
    
        # Проверяем время последних коммитов
        success, commits = self.git.get_commits(limit=3)
        if success and commits:
            print(f"   ⏰ Last 3 commits:")
            for commit in commits:
                commit_time = commit['commit']['committer']['date']
                message = commit['commit']['message']
                print(f"      - {commit_time}: {message[:50]}...")

    def test_ai(self):
        """Тестирование AI клиента"""
        print(f"\n🧠 Testing AI connection...")
        
        ai_ok, ai_msg = self.ai.health_check()
        if not ai_ok:
            print(f"   ❌ AI not available: {ai_msg}")
            return
        
        # Получаем доступные модели
        models_ok, models = self.ai.get_available_models()
        if models_ok:
            print(f"   📚 Available models: {', '.join(models)}")
        else:
            print(f"   ⚠️  Could not get models: {models}")
        
        # Простой тест
        test_prompt = "Привет! Ответь коротко: как дела?"
        print(f"   💬 Testing with prompt: '{test_prompt}'")
        
        success, response = self.ai.generate_response(
            prompt=test_prompt,
            model=self.config['ai']['model_name'],
            temperature=self.config['ai']['temperature']
        )
        
        if success:
            print(f"   🤖 AI Response: {response}")
        else:
            print(f"   ❌ AI Error: {response}")

    def run(self):
        """Запуск всех агентов"""
        print("=" * 50)
        print("🎯 Multi-Agent System is RUNNING")
        print("🤖 Agent 1: Processes In Progress tasks")
        print("👀 Agent 2: Monitors In Review tasks") 
        print("🧠 AI Client: Ready for intelligent tasks")
        print("=" * 50)
        
        # Тестируем AI
        self.test_ai()
        
        # Первый запуск всех функций
        self.process_tasks()
        self.review_tasks()
        self.show_repository_status()
        
        # Планирование периодического выполнения
        schedule.every(self.config['agent']['task_process_interval']).seconds.do(self.process_tasks)
        schedule.every(self.review_agent.timeDelay).seconds.do(self.review_tasks)
        schedule.every(300).seconds.do(self.show_repository_status)
        
        print(f"⏰ Next task processing in {self.config['agent']['task_process_interval']} seconds")
        print(f"⏰ Next review check in {self.review_agent.timeDelay} seconds")
        print(f"⏰ Next repository status in 300 seconds")
        
        # Главный цикл
        counter = 0
        while True:
            schedule.run_pending()
            counter += 1
            
            # Каждый час очищаем кэш обработанных задач
            if counter % 3600 == 0:
                self.task_agent.clear_processed_cache()
            
            if counter % 30 == 0:
                print(f"⏰ All agents running... ({counter//60}m {counter%60}s)")
            
            time.sleep(1)

if __name__ == "__main__":
    try:
        agent = JiraGiteaAgent()
        agent.run()
    except KeyboardInterrupt:
        print("🛑 All agents stopped by user")
    except Exception as e:
        print(f"💥 CRITICAL ERROR: {e}")
        import traceback
        print(f"💥 Stack trace: {traceback.format_exc()}")