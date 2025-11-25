import time
import schedule
from datetime import datetime
from jira_client import JiraClient
from ai_client import AIClient

class ReviewAgent:
    def __init__(self, jira_client, ai_client, username):
        self.jira = jira_client
        self.ai = ai_client
        self.username = username
        self.timeDelay = 60  # 60 секунд между проверками
        
    def get_in_review_tasks(self):
        """Получить задачи в статусе In Review"""
        try:
            jql = 'status = "In Review"'
            success, result = self.jira.get_issues(jql=jql)
            
            if success:
                return True, result
            else:
                return False, result
        except Exception as e:
            return False, f"Error getting In Review tasks: {e}"
    
    def get_task_comments(self, issue_key):
        """Получить комментарии к задаче"""
        try:
            url = f"{self.jira.url}/rest/api/2/issue/{issue_key}/comment"
            response = self.jira.session.get(url)
            
            if response.status_code == 200:
                comments_data = response.json()
                return True, comments_data.get('comments', [])
            else:
                return False, f"Error getting comments: {response.status_code}"
        except Exception as e:
            return False, f"Error fetching comments: {e}"
    
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
    
    def ai_analyze_task_understanding(self, task_summary, task_description):
        """AI анализ понимания задания"""
        prompt = f"""
Проанализируй задачу из Jira и объясни, что нужно сделать:

Название задачи: {task_summary}
Описание задачи: {task_description}

Ответь кратко на русском (2-3 предложения):
1. В чем суть задачи?
2. Что конкретно нужно сделать?
3. Какой ожидается результат?
"""
        
        success, response = self.ai.generate_response(prompt)
        if success:
            return f"🤖 AI понимание задания:\n{response}"
        else:
            return f"❌ AI не смог проанализировать задание: {response}"
    
    def ai_analyze_work_completion(self, task_summary, task_description, comments):
        """AI анализ выполненной работы на основе комментариев"""
        comments_text = "\n".join([
            f"Комментарий {i+1} ({c.get('author', {}).get('displayName', 'Unknown')}): {c.get('body', '')}"
            for i, c in enumerate(comments)
        ])
        
        prompt = f"""
Проанализируй, выполнена ли задача на основе комментариев:

Задача: {task_summary}
Описание: {task_description}

Комментарии к задаче:
{comments_text}

Ответь на русском кратко (3-4 предложения):
1. Есть ли в комментариях указания на выполненную работу?
2. Соответствует ли описание работы исходной задаче?
3. Твоя оценка выполнения (выполнена/частично выполнена/не выполнена)?
"""
        
        success, response = self.ai.generate_response(prompt)
        if success:
            return f"🤖 AI анализ выполненной работы:\n{response}"
        else:
            return f"❌ AI не смог проанализировать работу: {response}"
    
    def ai_generate_detailed_opinion(self, task_summary, task_description, work_descriptions):
        """AI генерация детального мнения о работе"""
        work_info = "\n".join([
            f"- {work['author']}: {work['text']}"
            for work in work_descriptions
        ]) if work_descriptions else "Описания работы не найдены"
        
        prompt = f"""
Сформулируй профессиональное мнение о выполненной работе:

Задача: {task_summary}
Исходное описание: {task_description}

Найденные описания работы:
{work_info}

Ответь на русском в формате:
- Общая оценка выполнения
- Соответствие работы заданию  
- Рекомендации (если нужны)
- Итоговый вердикт
"""
        
        success, response = self.ai.generate_response(prompt)
        if success:
            return f"🤖 AI вердикт по задаче:\n{response}"
        else:
            return f"❌ AI не смог сформировать мнение: {response}"
    
    def analyze_comments_for_work_done(self, comments):
        """Анализ комментариев на предмет выполненной работы"""
        work_descriptions = []
        
        for comment in comments:
            comment_text = comment.get('body', '')
            author = comment.get('author', {}).get('displayName', 'Unknown')
            
            # Ищем ключевые слова, указывающие на выполненную работу
            work_indicators = [
                'создан', 'сделал', 'выполнил', 'реализовал', 'добавил', 
                'обновил', 'исправил', 'завершил', 'готово', 'done',
                'автоматически', 'файл', 'код', 'изменен', 'настроил',
                'установил', 'написал', 'скоммитил', 'пуш', 'merge'
            ]
            
            if any(indicator in comment_text.lower() for indicator in work_indicators):
                work_descriptions.append({
                    'author': author,
                    'text': comment_text,
                    'created': comment.get('created', '')
                })
        
        return work_descriptions
    
    def review_single_task(self, task):
        """Провести ревью одной задачи по полному алгоритму с AI"""
        task_key = task['key']
        task_summary = task['fields']['summary']
        task_description = task['fields'].get('description', 'Описание отсутствует')
        
        print(f"\n🎯 Ревью задачи: {task_key}")
        print(f"   📝 Задание: {task_summary}")
        print(f"   📋 Описание: {task_description[:200]}...")
        
        # Шаг 3: AI понимание задания
        ai_understanding = self.ai_analyze_task_understanding(task_summary, task_description)
        print(f"   {ai_understanding}")
        
        # Шаг 4-5: Анализ комментариев
        comments_success, comments = self.get_task_comments(task_key)
        if comments_success:
            print(f"   💬 Найдено комментариев: {len(comments)}")
            
            # Базовый анализ комментариев
            work_descriptions = self.analyze_comments_for_work_done(comments)
            print(f"   🔍 Найдено описаний работы: {len(work_descriptions)}")
            
            # AI анализ выполненной работы
            if comments:
                ai_work_analysis = self.ai_analyze_work_completion(task_summary, task_description, comments)
                print(f"   {ai_work_analysis}")
            
            # Шаг 6: Детальное AI мнение о работе
            if work_descriptions:
                ai_opinion = self.ai_generate_detailed_opinion(task_summary, task_description, work_descriptions)
                print(f"   {ai_opinion}")
            else:
                print(f"   📊 Мнение: Не найдено описаний выполненной работы в комментариях")
                
        else:
            print(f"   ❌ Ошибка получения комментариев: {comments}")
        
        print(f"   ✅ AI-ревью задачи {task_key} завершено")
    
    def check_review_tasks(self):
        """Проверить задачи для ревью по полному алгоритму с AI"""
        print(f"\n🔍 ReviewAgent: AI-поиск задач In Review в {datetime.now().strftime('%H:%M:%S')}")
        
        success, result = self.get_in_review_tasks()
        
        if not success:
            print(f"   ❌ ReviewAgent: Ошибка - {result}")
            return
        
        tasks = result
        print(f"   📋 ReviewAgent: Найдено {len(tasks)} задач в In Review")
        
        if not tasks:
            print("   😴 Нет задач для ревью")
            return
        
        # Полный AI-алгоритм ревью для каждой задачи
        for task in tasks:
            task_key = task['key']
            print(f"\n   🔄 Начинаем AI-ревью задачи {task_key}")
            self.review_single_task(task)
            print(f"   ⏭️  Переходим к следующей задаче...")
        
        print(f"\n   ✅ Все задачи отревьючены с помощью AI. Ожидание {self.timeDelay} сек...")
    
    def run(self):
        """Запуск AI-агента ревью"""
        print("=" * 50)
        print("🧠 AI Review Agent is RUNNING")
        print(f"⏰ Check interval: {self.timeDelay} seconds")
        print("🤖 Algorithm: Full AI-powered task review")
        print("=" * 50)
        
        # Первая проверка
        self.check_review_tasks()
        
        # Планирование периодического выполнения
        schedule.every(self.timeDelay).seconds.do(self.check_review_tasks)
        
        print(f"⏰ Next AI review check in {self.timeDelay} seconds")
        
        # Главный цикл
        counter = 0
        while True:
            schedule.run_pending()
            counter += 1
            
            if counter % 30 == 0:
                print(f"⏰ AI ReviewAgent running... ({counter//60}m {counter%60}s)")
            
            time.sleep(1)