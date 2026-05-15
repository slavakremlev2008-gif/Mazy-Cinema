import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import db
from .common import get_admin_keyboard, get_cancel_keyboard
from .user import _show_stats, _show_random_movie, _show_random_series
from config import ADMIN_ID

logger = logging.getLogger(__name__)

# Состояния добавления
ADD_STATES = {}

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик сообщений от админа"""
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id != ADMIN_ID:
        return False
    
    # Обработка отмены
    if text == "❌ Отмена":
        if user_id in ADD_STATES:
            del ADD_STATES[user_id]
        await update.message.reply_text("❌ Действие отменено", reply_markup=get_admin_keyboard())
        return True
    
    # Обработка добавления фильма/сериала
    if text == "🎬 Добавить фильм":
        ADD_STATES[user_id] = {'step': 'code', 'type': 'movie'}
        await update.message.reply_text(
            "🎬 *Добавление нового фильма*\n\n"
            "Введите *код* для фильма (например: MATRIX2023):\n\n"
            "Код должен быть уникальным.\n"
            "Нажмите '❌ Отмена' для отмены",
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return True
    
    if text == "📺 Добавить сериал":
        ADD_STATES[user_id] = {'step': 'code', 'type': 'series'}
        await update.message.reply_text(
            "📺 *Добавление нового сериала*\n\n"
            "Введите *код* для сериала (например: BREAKINGBAD):\n\n"
            "Код должен быть уникальным.\n"
            "Нажмите '❌ Отмена' для отмены",
            parse_mode='Markdown',
            reply_markup=get_cancel_keyboard()
        )
        return True
    
    # Список фильмов
    if text == "📋 Список фильмов":
        movies = db.get_all_movies('movie')
        if not movies:
            await update.message.reply_text("📭 Список фильмов пуст.")
        else:
            response = "🎬 *Список всех фильмов:*\n\n"
            for movie in movies:
                response += f"📽 *{movie['title']}* ({movie['year']})\n"
                response += f"   Код: `{movie['code']}`\n\n"
                if len(response) > 3500:
                    await update.message.reply_text(response, parse_mode='Markdown')
                    response = ""
            if response:
                await update.message.reply_text(response, parse_mode='Markdown')
        return True
    
    # Список сериалов
    if text == "📋 Список сериалов":
        series = db.get_all_movies('series')
        if not series:
            await update.message.reply_text("📭 Список сериалов пуст.")
        else:
            response = "📺 *Список всех сериалов:*\n\n"
            for serie in series:
                response += f"📺 *{serie['title']}* ({serie['year']})\n"
                response += f"   Код: `{serie['code']}`\n\n"
                if len(response) > 3500:
                    await update.message.reply_text(response, parse_mode='Markdown')
                    response = ""
            if response:
                await update.message.reply_text(response, parse_mode='Markdown')
        return True
    
    # Статистика
    if text == "📊 Статистика":
        await _show_stats(update, context)
        return True
    
    # Рандом для админа
    if text == "🎲 Рандом фильм":
        await _show_random_movie(update, context)
        return True
    
    if text == "🎲 Рандом сериал":
        await _show_random_series(update, context)
        return True
    
    # Удаление
    if text == "❌ Удалить по коду":
        await update.message.reply_text(
            "ℹ️ Для удаления используйте команду:\n"
            "`/del код`\n\n"
            "Пример: `/del MATRIX2023`",
            parse_mode='Markdown'
        )
        return True
    
    # Обработка добавления
    if user_id in ADD_STATES:
        state = ADD_STATES[user_id]
        content_type = "фильма" if state['type'] == 'movie' else "сериала"
        
        if state['step'] == 'code':
            code = text.strip().upper()
            
            if ' ' in code:
                await update.message.reply_text("❌ Код не должен содержать пробелов. Попробуйте еще раз:")
                return True
            
            if db.code_exists(code):
                await update.message.reply_text(f"❌ Код `{code}` уже существует! Попробуйте другой код:", parse_mode='Markdown')
                return True
            
            ADD_STATES[user_id]['code'] = code
            ADD_STATES[user_id]['step'] = 'title'
            await update.message.reply_text(
                f"✅ Код `{code}` принят!\n\n"
                f"Теперь введите *название* {content_type}:",
                parse_mode='Markdown'
            )
            return True
        
        elif state['step'] == 'title':
            title = text.strip()
            ADD_STATES[user_id]['title'] = title
            ADD_STATES[user_id]['step'] = 'year'
            await update.message.reply_text(
                f"✅ Название `{title}` принято!\n\n"
                f"Теперь введите *год выпуска* {content_type} (например: 2023):",
                parse_mode='Markdown'
            )
            return True
        
        elif state['step'] == 'year':
            try:
                year = int(text.strip())
                
                if year < 1888 or year > 2030:
                    await update.message.reply_text("❌ Пожалуйста, введите корректный год (1888-2030):")
                    return True
                
                code = ADD_STATES[user_id]['code']
                title = ADD_STATES[user_id]['title']
                type_m = ADD_STATES[user_id]['type']
                
                success = db.add_movie(code, title, year, user_id, type_m)
                
                type_name = "Фильм" if type_m == 'movie' else "Сериал"
                emoji = "🎬" if type_m == 'movie' else "📺"
                
                if success:
                    await update.message.reply_text(
                        f"{emoji} *{type_name} успешно добавлен!*\n\n"
                        f"📽 Название: {title}\n"
                        f"📅 Год: {year}\n"
                        f"🔑 Код: `{code}`",
                        parse_mode='Markdown',
                        reply_markup=get_admin_keyboard()
                    )
                else:
                    await update.message.reply_text(f"❌ Ошибка при добавлении {type_name.lower()}", reply_markup=get_admin_keyboard())
                
                del ADD_STATES[user_id]
                
            except ValueError:
                await update.message.reply_text("❌ Пожалуйста, введите год цифрами (например: 2023):")
            return True
    
    return False

async def delete_movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /del - удаление фильма/сериала"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для этой команды.")
        return
    
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "❌ *Использование:* `/del код`\n\n"
            "Пример: `/del MATRIX2023`",
            parse_mode='Markdown'
        )
        return
    
    code = args[0].upper()
    movie = db.get_movie(code)
    
    if not movie:
        await update.message.reply_text(f"❌ Контент с кодом `{code}` не найден.", parse_mode='Markdown')
        return
    
    success = db.delete_movie(code)
    emoji = "🎬" if movie['type'] == 'movie' else "📺"
    type_name = "Фильм" if movie['type'] == 'movie' else "Сериал"
    
    if success:
        await update.message.reply_text(
            f"{emoji} ✅ *{type_name} удален!*\n\n"
            f"📽 Название: {movie['title']}\n"
            f"📅 Год: {movie['year']}\n"
            f"🔑 Код: `{code}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ Ошибка при удалении")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    user_id = update.effective_user.id
    is_admin = (user_id == ADMIN_ID)
    
    help_text = (
        "📖 *Как пользоваться ботом:*\n\n"
        "1️⃣ Получите код у администратора\n"
        "2️⃣ Нажмите 'Узнать по коду' и введите код\n"
        "3️⃣ Или используйте 'Рандом фильм'/'Рандом сериал'\n\n"
        "*Команды:*\n"
        "/start - Начать работу\n"
        "/help - Помощь\n"
        "/del код - Удалить контент (только админ)\n"
    )
    
    if is_admin:
        help_text += (
            "\n👑 *Админ-команды:*\n"
            "🎬 Добавить фильм - добавить фильм\n"
            "📺 Добавить сериал - добавить сериал\n"
            "📋 Список фильмов/сериалов - показать все\n"
            "📊 Статистика - показать статистику\n"
            "/del код - удалить по коду\n"
        )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')