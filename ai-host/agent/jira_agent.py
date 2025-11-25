import time
import os
from datetime import datetime
from jira_tasks import JiraTasks

class JiraTaskAgent:
    def __init__(self, jira_client, gitea_git_client, username):
        self.tasks = JiraTasks(jira_client)
        self.git = gitea_git_client
        self.username = username
        self.processed_tasks = set()
    
    def process_my_tasks(self):
        """Обработать задачи назначенные на меня в статусе In Progress"""
        print(f"\n🔍 Checking In Progress tasks for {self.username}...")
        
        # Получаем задачи в статусе In Progress
        success, result = self.tasks.get_my_in_progress_tasks(self.username)
        
        if not success:
            print(f"❌ Error getting tasks: {result}")
            return
        
        tasks = result
        print(f"📋 Found {len(tasks)} tasks in In Progress")
        
        if not tasks:
            print("😴 No In Progress tasks to process")
            return
        
        # Обрабатываем каждую задачу
        for task in tasks:
            task_key = task['key']
            
            # Пропускаем уже обработанные задачи в этой сессии
            if task_key in self.processed_tasks:
                print(f"⏭️  Already processed in this session: {task_key}")
                continue
            
            print(f"\n🎯 Processing In Progress task: {task_key}")
            print(f"   Summary: {task['fields']['summary']}")
            
            # Создаем или обновляем файл в репозитории
            file_processed = self._create_task_file(task)
            
            if file_processed:
                # Добавляем комментарий о проделанной работе
                self._add_work_comment(task_key)
                
                # Переводим задачу в статус In Review
                self._move_to_in_review(task_key)
            
            # Помечаем как обработанную в этой сессии
            self.processed_tasks.add(task_key)
        
        print(f"✅ Processed {len(tasks)} In Progress tasks")
    
    def _create_task_file(self, task):
        """Создать или обновить файл задачи в репозитории"""
        task_key = task['key']
        task_summary = task['fields']['summary']
        task_description = task['fields'].get('description', 'No description provided')
        
        try:
            # Формируем имя файла - точно как ключ задачи (AL-2 -> al-2.txt)
            filename = f"{task_key.lower()}.txt"
            
            # Формируем содержимое файла
            file_content = f"""# Задача: {task_key}

## Название: {task_summary}

## Описание:
{task_description}

## Статус: In Progress
## Исполнитель: {self.username}
## Дата обновления: {datetime.now().strftime('%Y-%m-%d %H:%M:%S MSK')}

---
*Автоматически создано/обновлено агентом Jira-Gitea Sync*
"""
            # Создаем или обновляем файл в репозитории
            commit_message = f"🤖 Update task file for {task_key}: {task_summary}"
            
            # Пробуем обычное обновление
            success, message = self.git.create_or_update_file(
                file_path=filename,
                content=file_content.strip(),
                commit_message=commit_message,
                branch="main"
            )
            
            if success:
                print(f"   ✅ {message}")
                return True
            else:
                # Если не получилось, пробуем принудительное обновление
                print(f"   ⚠️  Regular update failed, trying force update...")
                success, message = self.git.force_update_file(
                    file_path=filename,
                    content=file_content.strip(),
                    commit_message=commit_message,
                    branch="main"
                )
                
                if success:
                    print(f"   ✅ {message}")
                    return True
                else:
                    print(f"   ❌ {message}")
                    return False
                
        except Exception as e:
            print(f"   ❌ Error processing file for task {task_key}: {e}")
            return False
    
    def _add_work_comment(self, task_key):
        """Добавить комментарий о проделанной работе"""
        try:
            comment = f"""✅ Автоматически обработано агентом:

🤖 Создан/обновлен файл задачи в репозитории: `{task_key.lower()}.txt`
📝 Файл содержит описание задачи и метаданные
🔄 Задача переведена в статус "In Review" для дальнейшей проверки

*Обработано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S MSK')}*"""
            
            success, message = self.tasks.add_comment(task_key, comment)
            
            if success:
                print(f"   💬 Added work completion comment")
            else:
                print(f"   ⚠️  Failed to add comment: {message}")
                
        except Exception as e:
            print(f"   ❌ Error adding comment: {e}")
    
    def _move_to_in_review(self, task_key):
        """Перевести задачу в статус In Review"""
        try:
            success, message = self.tasks.transition_task(task_key, "In Review")
            
            if success:
                print(f"   🔄 {message}")
            else:
                # Если статус "In Review" не найден, пробуем "Review"
                if "not found" in message.lower():
                    success, message = self.tasks.transition_task(task_key, "Review")
                    if success:
                        print(f"   🔄 {message}")
                    else:
                        print(f"   ⚠️  {message}")
                else:
                    print(f"   ⚠️  {message}")
                    
        except Exception as e:
            print(f"   ❌ Error moving task to In Review: {e}")
    
    def clear_processed_cache(self):
        """Очистить кэш обработанных задач"""
        self.processed_tasks.clear()
        print("🧹 Cleared processed tasks cache")