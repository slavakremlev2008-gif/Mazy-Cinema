import random
from database import db

def get_random_content(content_type: str):
    """Получение случайного контента"""
    return db.get_random_movie(content_type)