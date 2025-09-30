from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню с основными командами"""
    keyboard = [
        [
            InlineKeyboardButton(text="📅 Расписание", callback_data="schedule"),
            InlineKeyboardButton(text="📚 Домашние задания", callback_data="homework")
        ],
        [
            InlineKeyboardButton(text="👥 О группе", callback_data="group_info"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_schedule_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора дня недели"""
    keyboard = [
        [
            InlineKeyboardButton(text="Понедельник", callback_data="schedule_monday"),
            InlineKeyboardButton(text="Вторник", callback_data="schedule_tuesday")
        ],
        [
            InlineKeyboardButton(text="Среда", callback_data="schedule_wednesday"),
            InlineKeyboardButton(text="Четверг", callback_data="schedule_thursday")
        ],
        [
            InlineKeyboardButton(text="Пятница", callback_data="schedule_friday"),
            InlineKeyboardButton(text="Суббота", callback_data="schedule_saturday")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_button() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    keyboard = [
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
