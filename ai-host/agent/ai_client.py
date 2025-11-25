import requests
import json

class AIClient:
    def __init__(self, model_url):
        self.model_url = model_url
        self.headers = {
            'Content-Type': 'application/json'
        }
    
    def health_check(self):
        """Проверка доступности AI модели"""
        try:
            response = requests.get(f"{self.model_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                models = [model['name'] for model in models_data.get('models', [])]
                return True, f"AI accessible. Models: {', '.join(models)}"
            else:
                return False, f"AI model error: {response.status_code}"
        except Exception as e:
            return False, f"AI connection failed: {e}"
    
    def generate_response(self, prompt, model="llama3.1", temperature=0.7, max_tokens=500):
        """Генерация ответа на промпт для llama3.1"""
        try:
            url = f"{self.model_url}/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('response', 'No response generated')
            else:
                return False, f"AI API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Error generating AI response: {e}"
    
    def chat_completion(self, messages, model="llama3.1", temperature=0.7, max_tokens=500):
        """Чат-комpletion для llama3.1"""
        try:
            url = f"{self.model_url}/api/chat"
            
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return True, result.get('message', {}).get('content', 'No response generated')
            else:
                return False, f"AI chat API error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"Error in AI chat: {e}"
    
    def get_available_models(self):
        """Получить список доступных моделей"""
        try:
            response = requests.get(f"{self.model_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models_data = response.json()
                models = [model['name'] for model in models_data.get('models', [])]
                return True, models
            else:
                return False, f"Error getting models: {response.status_code}"
                
        except Exception as e:
            return False, f"Error fetching models: {e}"
    
    def analyze_task(self, task_description, task_summary):
        """Анализ задачи для ревью (специально для ревьювера)"""
        prompt = f"""Проанализируй задачу для код-ревью:

Название: {task_summary}
Описание: {task_description}

Ответь кратко (2-3 предложения) на русском:
1. Основная цель задачи
2. Потенциальные сложности
3. Рекомендации по ревью"""

        return self.generate_response(prompt)
    
    def generate_review_comment(self, task_key, task_summary, findings):
        """Генерация комментария для ревью"""
        prompt = f"""Сгенерируй профессиональный комментарий для код-ревью задачи:

Задача: {task_key} - {task_summary}
Находки: {findings}

Формат:
- Начни с позитивного отзыва
- Укажи основные замечания
- Предложи конкретные улучшения
- Закончи ободряюще

Язык: русский, профессиональный но дружелюбный"""

        return self.generate_response(prompt)