import sqlite3
from typing import Optional, Dict, List
import random

class Database:
    def __init__(self, db_name="movies.db"):
        self.db_name = db_name
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Таблица фильмов и сериалов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                code TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                year INTEGER NOT NULL,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER
            )
        ''')
        
        # Добавляем колонку type если ее нет (для старых БД)
        try:
            cursor.execute("ALTER TABLE movies ADD COLUMN type TEXT DEFAULT 'movie'")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()
    
    def add_movie(self, code: str, title: str, year: int, admin_id: int, type_m: str = 'movie') -> bool:
        """Добавление фильма или сериала"""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO movies (code, title, year, type, created_by) VALUES (?, ?, ?, ?, ?)",
                (code.lower(), title, year, type_m, admin_id)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_movie(self, code: str) -> Optional[Dict]:
        """Получение фильма/сериала по коду"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT code, title, year, type FROM movies WHERE code = ?",
            (code.lower(),)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {"code": result[0], "title": result[1], "year": result[2], "type": result[3]}
        return None
    
    def delete_movie(self, code: str) -> bool:
        """Удаление фильма/сериала"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM movies WHERE code = ?", (code.lower(),))
        affected = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def get_all_movies(self, type_m: str = None) -> List[Dict]:
        """Получение всех фильмов или сериалов"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        if type_m:
            cursor.execute(
                "SELECT code, title, year, type FROM movies WHERE type = ? ORDER BY created_at DESC",
                (type_m,)
            )
        else:
            cursor.execute("SELECT code, title, year, type FROM movies ORDER BY created_at DESC")
        
        results = cursor.fetchall()
        conn.close()
        
        return [{"code": r[0], "title": r[1], "year": r[2], "type": r[3]} for r in results]
    
    def get_random_movie(self, type_m: str = 'movie') -> Optional[Dict]:
        """Получение случайного фильма или сериала"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT code, title, year, type FROM movies WHERE type = ?", (type_m,))
        results = cursor.fetchall()
        conn.close()
        
        if results:
            random_movie = random.choice(results)
            return {"code": random_movie[0], "title": random_movie[1], "year": random_movie[2], "type": random_movie[3]}
        return None
    
    def code_exists(self, code: str) -> bool:
        """Проверка существования кода"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM movies WHERE code = ?", (code.lower(),))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def get_stats(self) -> Dict:
        """Получение статистики"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM movies WHERE type = 'movie'")
        movies_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM movies WHERE type = 'series'")
        series_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM movies")
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "movies": movies_count,
            "series": series_count,
            "total": total_count
        }

# Создаем глобальный экземпляр БД
db = Database()