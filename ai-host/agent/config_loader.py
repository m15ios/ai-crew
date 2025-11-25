import os
import json
from dotenv import load_dotenv

def load_config():
    """Загрузка всей конфигурации из .env и JSON"""
    
    # Загружаем .env файл
    load_dotenv()
    
    # Базовые настройки из .env
    config = {
        'gitea': {
            'url': os.getenv('GITEA_URL'),
            'token': os.getenv('GITEA_TOKEN'),
            'repo_owner': os.getenv('GITEA_REPO_OWNER'),
            'repo_name': os.getenv('GITEA_REPO_NAME')
        },
        'jira': {
            'url': os.getenv('JIRA_URL'),
            'username': os.getenv('JIRA_USERNAME'),
            'password': os.getenv('JIRA_PASSWORD'),
            'project_key': os.getenv('JIRA_PROJECT'),
            'agent_username': os.getenv('JIRA_AGENT_USERNAME', os.getenv('JIRA_USERNAME'))
        },
        'ai': {
            'model_url': os.getenv('AI_MODEL_URL', 'http://localhost:11434'),
            'model_name': os.getenv('AI_MODEL_NAME', 'llama2'),
            'temperature': float(os.getenv('AI_TEMPERATURE', 0.7))
        },
        'agent': {
            'task_process_interval': int(os.getenv('TASK_PROCESS_INTERVAL', 120))
        }
    }
    
    # Загружаем JSON конфиг если существует
    config_path = '/app/config/agent_config.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                json_config = json.load(f)
                
            # Объединяем конфиги
            if 'gitea' in json_config:
                config['gitea'].update(json_config['gitea'])
            if 'jira' in json_config:
                config['jira'].update(json_config['jira'])
            if 'ai' in json_config:
                config['ai'].update(json_config['ai'])
            if 'agent' in json_config:
                config['agent'].update(json_config['agent'])
                
            print("✅ Loaded JSON configuration")
        except Exception as e:
            print(f"⚠️  Error loading JSON config: {e}")
    else:
        print("ℹ️  JSON config not found, using .env only")
    
    # Валидация обязательных полей
    required_fields = [
        ('GITEA_URL', config['gitea']['url']),
        ('GITEA_TOKEN', config['gitea']['token']),
        ('JIRA_URL', config['jira']['url']),
        ('JIRA_USERNAME', config['jira']['username']),
        ('JIRA_PASSWORD', config['jira']['password'])
    ]
    
    missing_fields = []
    for field_name, field_value in required_fields:
        if not field_value:
            missing_fields.append(field_name)
    
    if missing_fields:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")
    
    print(f"✅ Configuration loaded:")
    print(f"   Jira: {config['jira']['url']}")
    print(f"   Jira Project: {config['jira']['project_key']}")
    print(f"   Agent Username: {config['jira']['agent_username']}")
    print(f"   Gitea Repo: {config['gitea']['repo_owner']}/{config['gitea']['repo_name']}")
    print(f"   AI Model: {config['ai']['model_url']}")
    
    return config