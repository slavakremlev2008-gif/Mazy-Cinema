from telegram import ReplyKeyboardMarkup

def get_admin_keyboard():
    """Клавиатура для администратора"""
    keyboard = [
        ["🎬 Добавить фильм", "📺 Добавить сериал"],
        ["🎲 Рандом фильм", "🎲 Рандом сериал"],
        ["📋 Список фильмов", "📋 Список сериалов"],
        ["📊 Статистика", "❌ Удалить по коду"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_main_keyboard():
    """Главная клавиатура пользователя"""
    keyboard = [
        ["🎬 Узнать по коду", "🎲 Рандом фильм"],
        ["📺 Рандом сериал", "📊 Статистика"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    """Клавиатура отмены"""
    keyboard = [["❌ Отмена"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)