import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from database import db
from subgram_client import subgram
from config import ADMIN_ID, SUBGRAM_DISABLED

logger = logging.getLogger(__name__)

async def check_access_and_continue(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_func, *args, **kwargs):
    """
    Универсальная функция проверки доступа перед выполнением действия
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_admin = (user_id == ADMIN_ID)
    
    # Админы пропускают проверку
    if is_admin:
        await callback_func(update, context, *args, **kwargs)
        return True
    
    # Если проверка Subgram отключена
    if SUBGRAM_DISABLED:
        await callback_func(update, context, *args, **kwargs)
        return True
    
    # Получаем статус подписки
    status = await subgram.get_sponsor_tasks(chat_id, user_id)
    
    # Если есть незавершенные задания - доступ закрыт
    if status.get("has_access") is False:
        from .subgram_check import show_sponsors
        await show_sponsors(update, user_id, chat_id, context, status)
        return False
    
    await callback_func(update, context, *args, **kwargs)
    return True

def get_main_keyboard():
    """Главная клавиатура пользователя"""
    keyboard = [
        ["🎬 Узнать по коду", "🎲 Рандом фильм"],
        ["📺 Рандом сериал", "📊 Статистика"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard():
    """Клавиатура администратора"""
    keyboard = [
        ["🎬 Добавить фильм", "📺 Добавить сериал"],
        ["🎲 Рандом фильм", "🎲 Рандом сериал"],
        ["📋 Список фильмов", "📋 Список сериалов"],
        ["📊 Статистика", "❌ Удалить по коду"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура отмены"""
    keyboard = [["❌ Отмена"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)