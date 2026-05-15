#!/usr/bin/env python3
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from config import BOT_TOKEN
from handlers import (
    start_command,
    handle_user_message,
    handle_admin_message,
    delete_movie_command,
    help_command,
    check_subscription_callback
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("del", delete_movie_command))
    
    # Callback для проверки подписки
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="check_subscription"))
    
    # Обработчик сообщений (сначала проверяем админа, потом пользователя)
    async def message_handler(update: Update, context):
        if await handle_admin_message(update, context):
            return
        await handle_user_message(update, context)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    logger.info("Бот запущен...")
    print("🤖 Бот успешно запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()