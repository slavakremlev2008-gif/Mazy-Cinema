import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from subgram_client import subgram
from .common import check_access_and_continue, get_main_keyboard, get_admin_keyboard, get_cancel_keyboard
from .subgram_check import show_sponsors
from config import ADMIN_ID, SUBGRAM_DISABLED

logger = logging.getLogger(__name__)

# Состояния добавления (для админов)
ADD_STATES = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    is_admin = (user_id == ADMIN_ID)
    
    logger.info(f"Start command from user {user_id}, admin={is_admin}")
    
    # Админы пропускают проверку
    if is_admin:
        await show_main_menu(update, is_admin=True)
        return
    
    # Если проверка Subgram отключена
    if SUBGRAM_DISABLED:
        await show_main_menu(update, is_admin=False)
        return
    
    # Получаем статус подписки
    status = await subgram.get_sponsor_tasks(chat_id, user_id)
    
    if status.get("has_access", True):
        await show_main_menu(update, is_admin=False)
    else:
        await show_sponsors(update, user_id, chat_id, context, status)

async def show_main_menu(update: Update, is_admin: bool = False):
    """Показать главное меню"""
    stats = db.get_stats()
    
    welcome_text = (
        "🎬 *Добро пожаловать в Кино-Бот!*\n\n"
        f"📊 *Статистика:*\n"
        f"🎬 Фильмов: {stats['movies']}\n"
        f"📺 Сериалов: {stats['series']}\n"
        f"📦 Всего: {stats['total']}\n\n"
        "У вас есть код? Введите его, и я покажу название и год выпуска!\n\n"
        "Или используйте кнопки:\n"
        "🎲 *Рандом фильм* - случайный фильм\n"
        "📺 *Рандом сериал* - случайный сериал"
    )
    
    if is_admin:
        welcome_text += "\n\n👑 *Вы вошли как администратор*\nИспользуйте кнопки для управления контентом."
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_admin_keyboard())
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def show_main_menu_from_callback(update: Update, is_admin: bool = False):
    """Показать главное меню из callback-запроса"""
    stats = db.get_stats()
    
    welcome_text = (
        "🎬 *Добро пожаловать в Кино-Бот!*\n\n"
        f"📊 *Статистика:*\n"
        f"🎬 Фильмов: {stats['movies']}\n"
        f"📺 Сериалов: {stats['series']}\n"
        f"📦 Всего: {stats['total']}\n\n"
        "У вас есть код? Введите его, и я покажу название и год выпуска!\n\n"
        "Или используйте кнопки:\n"
        "🎲 *Рандом фильм* - случайный фильм\n"
        "📺 *Рандом сериал* - случайный сериал"
    )
    
    if is_admin:
        welcome_text += "\n\n👑 *Вы вошли как администратор*\nИспользуйте кнопки для управления контентом."
        await update.callback_query.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_admin_keyboard())
    else:
        await update.callback_query.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопки проверки подписки"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    logger.info(f"Checking subscription for user {user_id}")
    
    # Показываем сообщение о проверке
    await query.edit_message_text(
        "🔄 *Проверяем подписку...*\n\n"
        "Пожалуйста, подождите...",
        parse_mode='Markdown'
    )
    
    import asyncio
    await asyncio.sleep(1)
    
    # Получаем актуальный статус
    status = await subgram.get_sponsor_tasks(chat_id, user_id)
    
    if status.get("has_access", False):
        await query.edit_message_text(
            "✅ *Подписка подтверждена!*\n\n"
            "Добро пожаловать в бот! Используйте кнопки ниже.",
            parse_mode='Markdown'
        )
        await show_main_menu_from_callback(update, is_admin=False)
    else:
        await show_sponsors(update, user_id, chat_id, context, status)

# Действия пользователя с проверкой подписки

async def _show_random_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать случайный фильм"""
    random_movie = db.get_random_movie('movie')
    
    if random_movie:
        response = (
            f"🎬 *Случайный фильм!*\n\n"
            f"📽 *Название:* {random_movie['title']}\n"
            f"📅 *Год выпуска:* {random_movie['year']}\n"
            f"🔑 *Код:* `{random_movie['code']}`\n\n"
            f"Приятного просмотра! 🍿"
        )
    else:
        response = "❌ В базе пока нет фильмов. Добавьте их через админ-панель."
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def _show_random_series(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать случайный сериал"""
    random_series = db.get_random_movie('series')
    
    if random_series:
        response = (
            f"📺 *Случайный сериал!*\n\n"
            f"📺 *Название:* {random_series['title']}\n"
            f"📅 *Год выпуска:* {random_series['year']}\n"
            f"🔑 *Код:* `{random_series['code']}`\n\n"
            f"Приятного просмотра! 🍿"
        )
    else:
        response = "❌ В базе пока нет сериалов. Добавьте их через админ-панель."
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def _prompt_for_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запросить код у пользователя"""
    await update.message.reply_text(
        "🎬 Введите код фильма или сериала:",
        reply_markup=get_cancel_keyboard()
    )

async def _search_by_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    """Поиск фильма по коду"""
    movie = db.get_movie(code.upper())
    
    if movie:
        emoji = "🎬" if movie['type'] == 'movie' else "📺"
        type_name = "Фильм" if movie['type'] == 'movie' else "Сериал"
        
        response = (
            f"{emoji} *Найден {type_name}!*\n\n"
            f"📽 *Название:* {movie['title']}\n"
            f"📅 *Год выпуска:* {movie['year']}\n"
            f"🔑 *Код:* `{movie['code']}`\n\n"
            f"Приятного просмотра! 🍿"
        )
    else:
        response = (
            "❌ *Ничего не найдено*\n\n"
            "Проверьте правильность кода или попробуйте другой.\n\n"
            "Используйте кнопки 'Рандом фильм' или 'Рандом сериал' "
            "для случайного выбора."
        )
    
    await update.message.reply_text(response, parse_mode='Markdown')

async def _show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать статистику"""
    stats = db.get_stats()
    await update.message.reply_text(
        f"📊 *Статистика базы данных:*\n\n"
        f"🎬 Фильмов: {stats['movies']}\n"
        f"📺 Сериалов: {stats['series']}\n"
        f"📦 Всего записей: {stats['total']}",
        parse_mode='Markdown'
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений от пользователей"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Обработка отмены
    if text == "❌ Отмена":
        await update.message.reply_text("❌ Действие отменено", reply_markup=get_main_keyboard())
        return
    
    # Обработка кнопок
    if text == "🎬 Узнать по коду":
        await check_access_and_continue(update, context, _prompt_for_code)
        return
    
    if text == "🎲 Рандом фильм":
        await check_access_and_continue(update, context, _show_random_movie)
        return
    
    if text == "📺 Рандом сериал":
        await check_access_and_continue(update, context, _show_random_series)
        return
    
    if text == "📊 Статистика":
        await check_access_and_continue(update, context, _show_stats)
        return
    
    # Поиск по коду (если ввели не кнопку)
    if len(text) > 0:
        # Создаем фейковый объект для проверки
        class FakeUpdate:
            def __init__(self, user_id, chat_id, message):
                self.effective_user = type('obj', (object,), {'id': user_id})()
                self.effective_chat = type('obj', (object,), {'id': chat_id})()
                self.message = message
        
        fake_update = FakeUpdate(user_id, update.effective_chat.id, update.message)
        await check_access_and_continue(fake_update, context, _search_by_code, text)
        return