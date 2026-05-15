import logging
import aiohttp
from config import SUBGRAM_API_KEY, SUBGRAM_DISABLED, ADMIN_ID

logger = logging.getLogger(__name__)

SUBGRAM_URL = "https://api.subgram.org/get-sponsors"

class SubgramClient:
    def __init__(self):
        self.api_key = SUBGRAM_API_KEY
    
    async def get_sponsor_tasks(self, chat_id: int, user_id: int) -> dict:
        """
        Получает задания от SubGram API.
        Возвращает {
            "tasks": [...],
            "has_access": bool,  # True - доступ есть, False - нужно подписаться
            "status": "ok/warning/error"
        }
        """
        # Админ всегда имеет доступ
        if user_id == ADMIN_ID:
            return {"tasks": [], "has_access": True, "status": "ok"}
        
        if SUBGRAM_DISABLED:
            return {"tasks": [], "has_access": True, "status": "ok"}
        
        headers = {
            "Content-Type": "application/json",
            "Auth": self.api_key
        }
        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
            "get_links": 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(SUBGRAM_URL, json=payload, headers=headers) as resp:
                    data = await resp.json()
                    logger.info(f"SubGram ответ для user {user_id}: status={data.get('status')}, code={data.get('code')}")
                    
                    status = data.get("status", "error")
                    
                    # Если статус "ok" - пользователь выполнил все задания
                    if status == "ok":
                        return {"tasks": [], "has_access": True, "status": "ok"}
                    
                    # Если статус "warning" - есть невыполненные задания
                    elif status == "warning":
                        tasks = []
                        unique_links = set()  # Для уникальных ссылок
                        
                        # Получаем ссылки из поля 'links'
                        links = data.get("links", [])
                        for link in links:
                            if link and link not in unique_links:
                                unique_links.add(link)
                                tasks.append({
                                    "link": link,
                                    "name": "Канал",
                                    "id": None
                                })
                        
                        # Получаем спонсоров из 'additional.sponsors'
                        sponsors = data.get("additional", {}).get("sponsors", [])
                        for sponsor in sponsors:
                            link = sponsor.get("link")
                            name = sponsor.get("resource_name") or sponsor.get("name", "Канал")
                            if link and link not in unique_links:
                                if sponsor.get("available_now") and sponsor.get("status") == "unsubscribed":
                                    unique_links.add(link)
                                    # Очищаем ссылку от параметров
                                    if link and '?startapp=' in link:
                                        link = link.split('?')[0]
                                    tasks.append({
                                        "link": link,
                                        "name": name,
                                        "id": sponsor.get("ads_id")
                                    })
                        
                        # Доступ закрыт, так как есть невыполненные задания
                        return {
                            "tasks": tasks, 
                            "has_access": False, 
                            "status": "warning"
                        }
                    
                    else:
                        # При ошибке даем доступ (чтобы не блокировать пользователей)
                        return {"tasks": [], "has_access": True, "status": "error"}
        
        except Exception as e:
            logger.error(f"SubGram request failed: {e}")
            return {"tasks": [], "has_access": True, "status": "error"}

# Создаем глобальный экземпляр
subgram = SubgramClient()