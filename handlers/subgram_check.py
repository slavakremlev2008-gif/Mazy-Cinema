import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from subgram_client import subgram
from config import ADMIN_ID

logger = logging.getLogger(__name__)

async def show_sponsors(update: Update, user_id: int, chat_id: int, context: ContextTypes.DEFAULT_TYPE, status: dict = None):
    """Показать спонсоров для подписки"""
    logger.info(f"Showing sponsors for user {user_id}")
    
    if status is None:
        status = await subgram.get_sponsor_tasks(chat_id, user_id)
    
    sponsors = status.get("tasks", [])
    logger.info(f"Got {len(sponsors)} sponsors for user {user_id}")
    
    if sponsors and len(sponsors) > 0:
        keyboard = []
        sponsor_list = []
        
        # СОЗДАЕМ 1 КНОПКУ НА 1 СПОНСОРА
        for i, sponsor in enumerate(sponsors, 1):
            link = sponsor.get('link')
            name = sponsor.get('name', f'Спонсор {i}')
            
            if link:
                # Одна кнопка на одного спонсора
                button_text = f"📢 {name[:25]}" if len(name) > 25 else f"📢 {name}"
                keyboard.append([InlineKeyboardButton(button_text, url=link)])
                sponsor_list.append(f"{i}. {name}")
        
        # Кнопка проверки подписки
        keyboard.append([InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")])
        
        sponsors_text = "\n".join(sponsor_list)
        
        message_text = (
            f"🔒 *Доступ ограничен!* 🔒\n\n"
            f"Чтобы получить доступ к фильмам и сериалам, "
            f"необходимо подписаться на ВСЕХ спонсоров:\n\n"
            f"📢 *Список спонсоров:*\n{sponsors_text}\n\n"
            f"⚠️ *Важно:* подпишитесь на КАЖДЫЙ канал!\n\n"
            f"После подписки нажмите кнопку *«Я подписался»*"
        )
        
        # Отправляем сообщение
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                message_text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    else:
        logger.warning(f"No sponsors found for user {user_id}")
        from .user import show_main_menu
        if hasattr(update, 'callback_query') and update.callback_query:
            from .user import show_main_menu_from_callback
            await show_main_menu_from_callback(update, is_admin=(user_id == ADMIN_ID))
        else:
            await show_main_menu(update, is_admin=(user_id == ADMIN_ID))