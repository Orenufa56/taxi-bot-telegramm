import os
import re
import asyncio
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from database import (
    init_db, add_user, update_user_name, update_user_phone,
    get_user_bonus, add_bonus, use_bonus, add_order,
    get_user_history, get_user_stats, get_user_name,
    get_user_total_orders, get_user_last_order,
    get_user_orders_by_status
)

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DISPATCHER_CHAT_ID = "-1003980266463"
CLIENT_GROUP_IDS = [
    "-1003898088390",
    "-1003599431974",
    "-1002402286738",
]
ADMIN_IDS = [799527569]
# =================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

init_db()

# ========== СПИСОК ГОРОДОВ ==========
CITIES = [
    "Оренбург", "Уфа", "Толбазы", "Стерлитамак",
    "Салават", "Мелеуз", "Кумертау", "Мурапталово", "Октябрьское"
]

AVAILABLE_TIMES = ["6:00", "9:00", "12:00", "15:00", "18:00", "21:00-23:00"]

# ========== ЦЕНЫ ПО МАРШРУТАМ ==========
PRICES = {
    ("Оренбург", "Уфа"): 2300,
    ("Оренбург", "Стерлитамак"): 2000,
    ("Оренбург", "Салават"): 2000,
    ("Оренбург", "Мелеуз"): 1500,
    ("Оренбург", "Кумертау"): 1500,
    ("Оренбург", "Толбазы"): 2300,
    ("Оренбург", "Мурапталово"): 1500,
    ("Оренбург", "Октябрьское"): 1500,
    ("Уфа", "Оренбург"): 2300,
    ("Уфа", "Стерлитамак"): 1500,
    ("Уфа", "Салават"): 2000,
    ("Уфа", "Мелеуз"): 2000,
    ("Уфа", "Кумертау"): 2000,
    ("Уфа", "Толбазы"): 1500,
    ("Уфа", "Мурапталово"): 2300,
    ("Уфа", "Октябрьское"): 2300,
    ("Стерлитамак", "Оренбург"): 2000,
    ("Стерлитамак", "Уфа"): 1500,
    ("Стерлитамак", "Салават"): 1500,
    ("Стерлитамак", "Мелеуз"): 1500,
    ("Стерлитамак", "Кумертау"): 1500,
    ("Стерлитамак", "Толбазы"): 1500,
    ("Стерлитамак", "Мурапталово"): 2000,
    ("Стерлитамак", "Октябрьское"): 2000,
    ("Салават", "Оренбург"): 2000,
    ("Салават", "Уфа"): 2000,
    ("Салават", "Стерлитамак"): 1500,
    ("Салават", "Мелеуз"): 1500,
    ("Салават", "Кумертау"): 1500,
    ("Салават", "Толбазы"): 1500,
    ("Салават", "Мурапталово"): 2000,
    ("Салават", "Октябрьское"): 2000,
    ("Мелеуз", "Оренбург"): 1500,
    ("Мелеуз", "Уфа"): 2000,
    ("Мелеуз", "Стерлитамак"): 1500,
    ("Мелеуз", "Салават"): 1500,
    ("Мелеуз", "Кумертау"): 1500,
    ("Мелеуз", "Толбазы"): 1500,
    ("Мелеуз", "Мурапталово"): 1500,
    ("Мелеуз", "Октябрьское"): 1500,
    ("Кумертау", "Оренбург"): 1500,
    ("Кумертау", "Уфа"): 2000,
    ("Кумертау", "Стерлитамак"): 1500,
    ("Кумертау", "Салават"): 1500,
    ("Кумертау", "Мелеуз"): 1500,
    ("Кумертау", "Толбазы"): 2000,
    ("Кумертау", "Мурапталово"): 1200,
    ("Кумертау", "Октябрьское"): 1200,
    ("Толбазы", "Оренбург"): 2300,
    ("Толбазы", "Уфа"): 1500,
    ("Толбазы", "Стерлитамак"): 1500,
    ("Толбазы", "Салават"): 2000,
    ("Толбазы", "Мелеуз"): 2000,
    ("Толбазы", "Кумертау"): 2000,
    ("Толбазы", "Мурапталово"): 2000,
    ("Толбазы", "Октябрьское"): 2300,
    ("Мурапталово", "Оренбург"): 1500,
    ("Мурапталово", "Уфа"): 2300,
    ("Мурапталово", "Стерлитамак"): 2000,
    ("Мурапталово", "Салават"): 2000,
    ("Мурапталово", "Мелеуз"): 1500,
    ("Мурапталово", "Кумертау"): 1200,
    ("Мурапталово", "Толбазы"): 2000,
    ("Мурапталово", "Октябрьское"): 1200,
    ("Октябрьское", "Оренбург"): 1500,
    ("Октябрьское", "Уфа"): 2300,
    ("Октябрьское", "Стерлитамак"): 2000,
    ("Октябрьское", "Салават"): 2000,
    ("Октябрьское", "Мелеуз"): 1500,
    ("Октябрьское", "Кумертау"): 1200,
    ("Октябрьское", "Толбазы"): 2300,
    ("Октябрьское", "Мурапталово"): 1200,
}

# ========== БОНУСНАЯ СИСТЕМА ==========
MIN_BONUS_FOR_USE = 50
MAX_BONUS_FOR_USE = 200
BONUS_STEP = 10

def get_price_per_seat(from_city: str, to_city: str) -> int:
    return PRICES.get((from_city, to_city), 0)

def format_price(price: int) -> str:
    return f"{price:,}".replace(",", " ")

def calculate_bonus(price: int, total_orders: int) -> int:
    if total_orders >= 20:
        percent = 0.10
    elif total_orders >= 10:
        percent = 0.05
    elif total_orders >= 5:
        percent = 0.03
    else:
        percent = 0.01
    return int(price * percent)

def get_user_level(total_orders: int) -> tuple:
    if total_orders >= 20:
        return "VIP клиент", "🏆", "10%"
    elif total_orders >= 10:
        return "Активный клиент", "⭐", "5%"
    elif total_orders >= 5:
        return "Регулярный клиент", "🔄", "3%"
    else:
        return "Новый клиент", "🆕", "1%"

def calculate_final_price(price: int, bonus_used: int) -> int:
    return max(0, price - bonus_used)

def get_available_bonus_options(available_bonus: int) -> list:
    options = []
    max_allowed = min(MAX_BONUS_FOR_USE, available_bonus)
    max_allowed = (max_allowed // BONUS_STEP) * BONUS_STEP
    for amount in range(MIN_BONUS_FOR_USE, max_allowed + 1, BONUS_STEP):
        options.append(amount)
    return options

def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r'[\s\+\(\)\-]', '', phone)
    return cleaned.isdigit() and 10 <= len(cleaned) <= 12

def is_date_past(date_str: str) -> bool:
    try:
        order_date = datetime.strptime(date_str, "%d.%m.%y")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return order_date < today
    except:
        return True

def format_date_ru(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%d.%m.%y")
        months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                  'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        return f"{dt.day} {months[dt.month-1]} {dt.year}"
    except:
        return date_str

# ========== КЛАВИАТУРЫ ==========

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚕 Начать")],
            [KeyboardButton(text="🎁 Бонусы"), KeyboardButton(text="❓ Частые вопросы")],
            [KeyboardButton(text="📜 История"), KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="❌ Отмена"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def get_cities_keyboard():
    buttons = []
    row = []
    for city in CITIES:
        row.append(KeyboardButton(text=city))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton(text="🔙 Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_time_keyboard():
    buttons = []
    row = []
    for time in AVAILABLE_TIMES:
        row.append(KeyboardButton(text=time))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_calendar_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Сегодня"), KeyboardButton(text="📅 Завтра")],
            [KeyboardButton(text="📅 Послезавтра"), KeyboardButton(text="✏️ Ввести вручную")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_seats_keyboard(from_city: str, to_city: str):
    price_per_seat = get_price_per_seat(from_city, to_city)
    buttons = []
    row = []
    for seats in [1, 2, 3, 4, 5, 6]:
        total_price = price_per_seat * seats
        row.append(KeyboardButton(text=f"{seats} мест ({format_price(total_price)}₽)"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton(text="🔙 Назад")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_bonus_keyboard(available_options: list):
    buttons = []
    row = []
    for amount in available_options:
        row.append(KeyboardButton(text=f"💳 {amount} баллов"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([KeyboardButton(text="🔙 Пропустить")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def get_skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏩ Пропустить")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )

def get_faq_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Стоимость проезда")],
            [KeyboardButton(text="⏰ Время выезда"), KeyboardButton(text="🕐 Время в пути")],
            [KeyboardButton(text="📦 Посылки"), KeyboardButton(text="🚕 Забрать до адреса")],
            [KeyboardButton(text="📍 Точки отправления")],
            [KeyboardButton(text="🐕 Животные"), KeyboardButton(text="🧳 Багаж")],
            [KeyboardButton(text="🚭 Курить в машине")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

# ========== ОБРАБОТЧИКИ КОМАНД ==========

class OrderForm(StatesGroup):
    waiting_name = State()
    waiting_from_city = State()
    waiting_to_city = State()
    waiting_date = State()
    waiting_time = State()
    waiting_seats = State()
    waiting_bonus = State()
    waiting_phone = State()
    waiting_comment = State()

async def send_and_pin_button():
    """Отправляет кнопку во все группы клиентов и закрепляет её"""
    for group_id in CLIENT_GROUP_IDS:
        try:
            try:
                chat_info = await bot.get_chat(chat_id=group_id)
                if chat_info.pinned_message:
                    await bot.unpin_chat_message(chat_id=group_id)
            except:
                pass
            
            msg = await bot.send_message(
                chat_id=group_id,
                text="🚕 **Бот для заказа такси Оренбург - Уфа**\n\n"
                     "📋 **Как оформить заказ:**\n\n"
                     "1️⃣ Нажмите на кнопку ниже\n"
                     "2️⃣ В личном чате с ботом нажмите /start\n"
                     "3️⃣ Выберите '🚕 Начать' и следуйте инструкциям\n\n"
                     "💰 **Стоимость:**\n"
                     "• Место: от 1200 руб.\n"
                     "• Цена зависит от маршрута\n\n"
                     "🎁 **Бонусная система:**\n"
                     "• За каждый заказ начисляются бонусы (от 1% до 10%)\n"
                     "• Бонусы можно использовать для оплаты\n\n"
                     "⏰ **Время выезда:** 6:00, 9:00, 12:00, 15:00, 18:00, 21:00-23:00\n\n"
                     "📍 **Точки отправления:**\n"
                     "• Оренбург: ТЦ Север\n"
                     "• Уфа: Универмаг 'Уфа'\n\n"
                     "📞 **Контакты диспетчера:** +7 9292 80 7979\n\n"
                     "👇 **Нажмите на кнопку ниже, чтобы оформить заказ**",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🚕 Заказать такси", url="https://t.me/Taxi56OrenUfabot")]
                    ]
                ),
                parse_mode="Markdown"
            )
            await bot.pin_chat_message(chat_id=group_id, message_id=msg.message_id)
            logging.info(f"✅ Кнопка отправлена и закреплена в группе {group_id}!")
        except Exception as e:
            logging.error(f"❌ Ошибка при отправке в группу {group_id}: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    if chat_id != user_id:
        await message.answer("🚕 **Бот для заказа такси**\n\nНажмите на кнопку ниже, чтобы начать", reply_markup=get_main_keyboard())
        return
    
    saved_name = get_user_name(user_id)
    bonus_points, used_bonus = get_user_bonus(user_id)
    total_orders = get_user_total_orders(user_id)
    level, level_emoji, level_percent = get_user_level(total_orders)
    
    if saved_name:
        welcome_text = (
            f"🚕 **С возвращением, {saved_name}!**\n\n"
            f"🎁 **Бонусный счёт:** {bonus_points} баллов\n"
            f"👤 **Статус:** {level_emoji} {level}\n\n"
            "👇 **Выберите действие:**"
        )
    else:
        welcome_text = (
            "🚕 **Добро пожаловать в бот заказа такси!**\n\n"
            "Я помогу вам быстро и комфортно добраться между городами.\n\n"
            "🎁 **Бонусная система:**\n"
            "• За каждый заказ начисляются бонусы (от 1% до 10%)\n"
            "• Чем больше заказов, тем выше процент бонусов!\n"
            "• Бонусы можно использовать для оплаты следующих поездок!\n\n"
            "👇 **Выберите действие:**"
        )
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(F.text == "🚕 Начать")
async def start_order(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    saved_name = get_user_name(user_id)
    
    if saved_name:
        await state.set_state(OrderForm.waiting_from_city)
        await state.update_data(username=saved_name)
        await message.answer(
            f"🚕 **Начинаем оформление заказа!**\n\n"
            f"👋 **С возвращением, {saved_name}!**\n\n"
            f"📍 **Выберите город отправления:**",
            reply_markup=get_cities_keyboard()
        )
    else:
        await state.set_state(OrderForm.waiting_name)
        await message.answer(
            "🚕 **Начинаем оформление заказа!**\n\n"
            "👤 **Как к вам обращаться?**\n"
            "(Напишите ваше имя)",
            reply_markup=get_back_keyboard()
        )

@dp.message(F.text == "🎁 Бонусы")
async def show_bonus_info(message: types.Message):
    user_id = message.from_user.id
    bonus_points, used_bonus = get_user_bonus(user_id)
    total_orders = get_user_total_orders(user_id)
    level, level_emoji, level_percent = get_user_level(total_orders)
    
    await message.answer(
        f"🎁 **Ваш бонусный счёт**\n\n"
        f"💰 **Доступно баллов:** {bonus_points}\n"
        f"💳 **Использовано баллов:** {used_bonus}\n"
        f"👤 **Ваш статус:** {level_emoji} {level}\n"
        f"📊 **Всего заказов:** {total_orders}\n\n"
        f"📋 **Правила бонусной системы:**\n"
        f"• За каждый заказ начисляются бонусы\n"
        f"• 1 балл = 1 рубль скидки\n"
        f"• Минимальное списание: {MIN_BONUS_FOR_USE} баллов\n"
        f"• Максимальное списание: {MAX_BONUS_FOR_USE} баллов\n"
        f"• Списание кратно 10 баллам\n"
        f"• Бонусы не сгорают\n\n"
        f"🎯 **Ваш уровень:**\n"
        f"🆕 Новый клиент: до 5 заказов (+1% бонусов)\n"
        f"🔄 Регулярный клиент: 5-9 заказов (+3% бонусов)\n"
        f"⭐ Активный клиент: 10-19 заказов (+5% бонусов)\n"
        f"🏆 VIP клиент: 20+ заказов (+10% бонусов)",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "📜 История")
async def show_history(message: types.Message):
    user_id = message.from_user.id
    orders = get_user_history(user_id)
    stats = get_user_stats(user_id)
    
    if not orders:
        await message.answer(
            "📜 **История поездок**\n\nУ вас пока нет ни одной поездки.\n\nНажмите '🚕 Начать' для первого заказа!",
            reply_markup=get_back_keyboard()
        )
        return
    
    history_text = "📜 **История ваших поездок**\n\n"
    for i, order in enumerate(orders, 1):
        from_city, to_city, order_date, order_time, seats, price, bonus_earned, bonus_used, final_price, status = order
        status_emoji = "🆕" if status == "новый" else "✅" if status == "выполнен" else "⏳"
        date_formatted = format_date_ru(order_date)
        history_text += (
            f"{i}. 📍 {from_city} → {to_city}\n"
            f"   📅 {date_formatted} в {order_time}\n"
            f"   👥 {seats} мест | {format_price(price)}₽\n"
            f"   🎁 +{bonus_earned} бонусов"
        )
        if bonus_used > 0:
            history_text += f" | 💳 -{bonus_used} бонусов"
        history_text += f"\n   💰 Итого: {format_price(final_price)}₽\n"
        history_text += f"   🏷 Статус: {status_emoji} {status}\n\n"
    
    if stats:
        total_orders, phone, first_name, username, bonus_points, used_bonus = stats
        history_text += f"📊 **Всего поездок:** {total_orders}\n"
        history_text += f"🎁 **Бонусов на счету:** {bonus_points}\n"
        if phone:
            history_text += f"📞 **Ваш телефон:** {phone}"
    
    await message.answer(history_text, reply_markup=get_back_keyboard())

@dp.message(F.text == "📞 Контакты")
async def show_contacts(message: types.Message):
    await message.answer(
        "📞 **Контакты для связи**\n\n"
        "📱 Диспетчерская служба: +79058907979\n"
        "📱 Телефон диспетчера: +7 9292 80 7979\n\n"
        "🕐 Время работы: Круглосуточно\n\n"
        "📧 Email: orenufa56@gmail.com\n\n"
        "💬 ВКонтакте: vk.com/ufaoren\n\n"
        "📍 Мы в Telegram: t.me/orenufa56",
        reply_markup=get_back_keyboard()
    )

@dp.message(F.text == "❌ Отмена")
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ **Заказ отменен**\n\nНажмите '🚕 Начать' для нового заказа.", reply_markup=get_main_keyboard())

@dp.message(F.text == "ℹ️ Помощь")
async def show_help(message: types.Message):
    await message.answer(
        "ℹ️ **Помощь**\n\n"
        "📌 Команды:\n"
        "• 🚕 Начать - начать оформление заказа\n"
        "• 🎁 Бонусы - бонусный счёт\n"
        "• ❓ Частые вопросы - ответы\n"
        "• 📜 История - ваши поездки\n"
        "• 📞 Контакты - телефоны\n"
        "• ❌ Отмена - отменить заказ\n\n"
        "📝 **Как оформить заказ:**\n"
        "1️⃣ Нажмите '🚕 Начать'\n"
        "2️⃣ Введите имя (при первом заказе)\n"
        "3️⃣ Выберите город отправления\n"
        "4️⃣ Выберите город назначения\n"
        "5️⃣ Выберите дату поездки\n"
        "6️⃣ Выберите время\n"
        "7️⃣ Выберите количество мест\n"
        "8️⃣ Укажите телефон\n"
        "9️⃣ Добавьте комментарий\n\n"
        "💰 **Цены зависят от маршрута**\n"
        "🎁 **Бонусы начисляются за каждый заказ!**\n"
        "💳 Оплата: наличными или переводом",
        reply_markup=get_back_keyboard()
    )

@dp.message(F.text == "❓ Частые вопросы")
async def show_faq(message: types.Message):
    await message.answer(
        "❓ **Часто задаваемые вопросы**\n\nВыберите интересующий вас вопрос:",
        reply_markup=get_faq_keyboard()
    )

# ========== FAQ ОТВЕТЫ ==========

@dp.message(F.text == "💰 Стоимость проезда")
async def faq_price(message: types.Message):
    await message.answer(
        "💰 **Стоимость проезда**\n\n"
        "Цена зависит от направления и количества мест.\n\n"
        "📋 **Основные направления:**\n"
        "• Оренбург — Уфа: 2300₽/место\n"
        "• Оренбург — Стерлитамак: 2000₽/место\n"
        "• Оренбург — Салават: 2000₽/место\n"
        "• Уфа — Оренбург: 2300₽/место\n\n"
        "📞 **Точную стоимость уточняйте у диспетчера!**\n\n"
        "💳 **Способы оплаты:**\n"
        "• Наличные водителю\n"
        "• Перевод на карту\n"
        "• СБП",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "⏰ Время выезда")
async def faq_time(message: types.Message):
    await message.answer(
        "⏰ **Время выезда**\n\n"
        "Доступное время отправления:\n\n"
        "🕐  6:00, 9:00\n"
        "🕐  12:00, 15:00\n"
        "🕐  18:00\n"
        "🕐  21:00 - 23:00\n\n"
        "⚠️ **Важно:**\n"
        "• Время в пути может меняться из-за погоды\n"
        "• При заказе указывайте точное время\n"
        "• Диспетчер подтвердит наличие мест",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🕐 Время в пути")
async def faq_travel_time(message: types.Message):
    await message.answer(
        "🕐 **Время в пути**\n\n"
        "Стандартное время в пути:\n\n"
        "• **Оренбург — Уфа:** 4-5 часов\n"
        "• **Оренбург — Стерлитамак:** 3-4 часа\n"
        "• **Уфа — Салават:** 2-3 часа\n\n"
        "⚠️ **Факторы, влияющие на время:**\n"
        "• Погодные условия\n"
        "• Загруженность трассы\n"
        "• Время суток\n\n"
        "📞 Диспетчер предупредит о задержках.",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "📦 Посылки")
async def faq_parcels(message: types.Message):
    await message.answer(
        "📦 **Перевозка посылок**\n\n"
        "Мы осуществляем доставку посылок между городами!\n\n"
        "💰 **Стоимость:** от 500 руб.\n"
        "• Цена зависит от размера и веса\n"
        "• Хрупкие грузы упаковываются отдельно\n\n"
        "📋 **Как отправить:**\n"
        "1. Оформите заказ с пометкой 'Посылка'\n"
        "2. Укажите вес и размеры\n"
        "3. Сообщите, кто отправляет и получает\n\n"
        "📞 Для точного расчета свяжитесь с диспетчером.",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🚕 Забрать до адреса")
async def faq_address_delivery(message: types.Message):
    await message.answer(
        "🚕 **Забрать и довезти до адреса**\n\n"
        "Мы можем забрать вас от любого адреса и довезти до нужного места!\n\n"
        "💰 **Дополнительная плата:** от 300 руб.\n"
        "• Зависит от удаленности от точки сбора\n\n"
        "📍 **Стандартные точки (бесплатно):**\n"
        "• Оренбург: ТЦ Север\n"
        "• Уфа: Универмаг 'Уфа'\n\n"
        "⚠️ **Укажите точный адрес в комментарии!**",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "📍 Точки отправления")
async def faq_departure_points(message: types.Message):
    await message.answer(
        "📍 **Точки отправления и прибытия**\n\n"
        "🏁 **Оренбург:** ТЦ Север, пр. Дзержинского 23\n\n"
        "🏁 **Уфа:** Универмаг 'Уфа', пр. Октября 31\n\n"
        "🏁 **Другие города:**\n"
        "• Стерлитамак — Автовокзал\n"
        "• Салават — Автовокзал\n"
        "• Мелеуз — Автовокзал\n"
        "• Кумертау — КПМ\n\n"
        "⚠️ **По другим адресам возможна доплата.**",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🐕 Животные")
async def faq_animals(message: types.Message):
    await message.answer(
        "🐕 **Перевозка животных**\n\n"
        "✅ Да, мы перевозим животных!\n\n"
        "📋 **Правила:**\n"
        "• Обязательно наличие переноски\n"
        "• Для крупных собак нужен намордник и поводок\n"
        "• Животное не должно мешать водителю\n"
        "• Возможна доплата за уборку салона\n\n"
        "💰 **Стоимость:** уточняйте у диспетчера\n\n"
        "⚠️ **Укажите в комментарии, что вы с животным!**",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🧳 Багаж")
async def faq_luggage(message: types.Message):
    await message.answer(
        "🧳 **Перевозка багажа**\n\n"
        "📋 **Правила:**\n\n"
        "• Средний чемодан входит в стоимость места\n"
        "• Багаж перевозится бесплатно в пределах разумного\n"
        "• При большом багаже укажите в комментарии\n\n"
        "📦 **Крупногабаритный багаж:**\n"
        "• Велосипеды, лыжи, сноуборды\n"
        "• Стоимость обсуждается отдельно\n\n"
        "💡 **Уточните детали у диспетчера.**",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🚭 Курить в машине")
async def faq_smoking(message: types.Message):
    await message.answer(
        "🚭 **Курение в автомобиле**\n\n"
        "❌ **Курение в салоне строго запрещено!**\n\n"
        "💰 **Штраф:** 5000 рублей\n"
        "(на химчистку салона)\n\n"
        "✅ **Можно курить на остановках**\n"
        "(попросите водителя)\n\n"
        "✅ Благодарим за понимание!",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🔙 Назад")
async def back_to_main(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔙 **Главное меню**", reply_markup=get_main_keyboard())

# ========== ОСНОВНОЙ ХЭНДЛЕР ЗАКАЗА (FSM) ==========

@dp.message(StateFilter(OrderForm.waiting_name))
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text) > 100:
        await message.answer("❌ Имя слишком длинное!")
        return
    
    await state.update_data(username=message.text)
    await state.set_state(OrderForm.waiting_from_city)
    update_user_name(message.from_user.id, message.text)
    
    await message.answer(
        f"👋 **Приятно познакомиться, {message.text}!**\n\n"
        f"📍 **Выберите город отправления:**",
        reply_markup=get_cities_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_from_city))
async def process_from_city(message: types.Message, state: FSMContext):
    if message.text not in CITIES:
        await message.answer("❌ Выберите город из кнопок!", reply_markup=get_cities_keyboard())
        return
    
    await state.update_data(from_city=message.text)
    await state.set_state(OrderForm.waiting_to_city)
    await message.answer(
        f"📍 **Откуда:** {message.text}\n\n"
        f"🏁 **Выберите город назначения:**",
        reply_markup=get_cities_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_to_city))
async def process_to_city(message: types.Message, state: FSMContext):
    if message.text not in CITIES:
        await message.answer("❌ Выберите город из кнопок!", reply_markup=get_cities_keyboard())
        return
    
    data = await state.get_data()
    if message.text == data.get('from_city'):
        await message.answer("❌ Города не должны совпадать!", reply_markup=get_cities_keyboard())
        return
    
    await state.update_data(to_city=message.text)
    await state.set_state(OrderForm.waiting_date)
    await message.answer(
        f"📍 **Маршрут:** {data['from_city']} → {message.text}\n\n"
        f"📅 **Выберите дату поездки:**",
        reply_markup=get_calendar_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_date))
async def process_date(message: types.Message, state: FSMContext):
    if message.text == "📅 Сегодня":
        formatted_date = datetime.now().strftime("%d.%m.%y")
    elif message.text == "📅 Завтра":
        formatted_date = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%y")
    elif message.text == "📅 Послезавтра":
        formatted_date = (datetime.now() + timedelta(days=2)).strftime("%d.%m.%y")
    elif message.text == "✏️ Ввести вручную":
        await message.answer("📅 **Введите дату вручную**\n\nФормат: `04.04.26`\nПример: 25.12.26")
        return
    elif message.text == "🔙 Назад":
        await state.set_state(OrderForm.waiting_to_city)
        await message.answer("🏁 **Выберите город назначения:**", reply_markup=get_cities_keyboard())
        return
    else:
        clean = re.sub(r'[\.\s]', '', message.text)
        if len(clean) >= 6:
            formatted_date = f"{clean[0:2]}.{clean[2:4]}.{clean[4:6]}"
        else:
            formatted_date = message.text
    
    if is_date_past(formatted_date):
        await message.answer(
            "❌ **Неверная дата или дата уже прошла!**\n\n"
            "Выберите дату из меню или введите будущую дату в формате: `04.04.26`",
            reply_markup=get_calendar_keyboard()
        )
        return
    
    await state.update_data(date=formatted_date)
    await state.set_state(OrderForm.waiting_time)
    await message.answer(
        f"📅 **Дата:** {formatted_date}\n\n⏰ **Выберите время:**",
        reply_markup=get_time_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_time))
async def process_time(message: types.Message, state: FSMContext):
    if message.text not in AVAILABLE_TIMES:
        await message.answer("❌ Выберите время из кнопок!", reply_markup=get_time_keyboard())
        return
    
    await state.update_data(time=message.text)
    await state.set_state(OrderForm.waiting_seats)
    
    data = await state.get_data()
    from_city = data.get('from_city', '')
    to_city = data.get('to_city', '')
    price_per_seat = get_price_per_seat(from_city, to_city)
    
    await message.answer(
        f"⏰ **Время:** {message.text}\n\n"
        f"👥 **Выберите количество мест:**\n\n"
        f"💰 Цена за место: {format_price(price_per_seat)}₽\n"
        f"📍 {from_city} → {to_city}",
        reply_markup=get_seats_keyboard(from_city, to_city)
    )

@dp.message(StateFilter(OrderForm.waiting_seats))
async def process_seats(message: types.Message, state: FSMContext):
    seats_match = re.search(r'(\d+) мест', message.text)
    if seats_match:
        seats = int(seats_match.group(1))
        data = await state.get_data()
        from_city = data.get('from_city', '')
        to_city = data.get('to_city', '')
        price_per_seat = get_price_per_seat(from_city, to_city)
        price = price_per_seat * seats
        
        await state.update_data(seats=seats, price_per_seat=price_per_seat, price=price)
        await state.set_state(OrderForm.waiting_bonus)
        
        bonus_points, used_bonus = get_user_bonus(message.from_user.id)
        available_options = get_available_bonus_options(bonus_points)
        
        if not available_options:
            await state.set_state(OrderForm.waiting_phone)
            await message.answer(
                f"👥 **Мест:** {seats}\n"
                f"💰 **Цена за место:** {format_price(price_per_seat)}₽\n"
                f"💰 **Общая стоимость:** {format_price(price)}₽\n\n"
                f"🎁 У вас {bonus_points} бонусов (нужно минимум {MIN_BONUS_FOR_USE} для списания)\n\n"
                f"📞 **Ваш номер телефона**\n\n"
                f"Примеры: 89001234567, +7-900-123-45-67"
            )
        else:
            await message.answer(
                f"🎁 **У вас на счету {bonus_points} бонусов**\n\n"
                f"Хотите использовать бонусы для оплаты?",
                reply_markup=get_bonus_keyboard(available_options)
            )
    elif message.text == "🔙 Назад":
        await state.set_state(OrderForm.waiting_time)
        await message.answer("⏰ **Выберите время:**", reply_markup=get_time_keyboard())
    else:
        data = await state.get_data()
        from_city = data.get('from_city', '')
        to_city = data.get('to_city', '')
        await message.answer("❌ Выберите количество мест из кнопок!", reply_markup=get_seats_keyboard(from_city, to_city))

@dp.message(StateFilter(OrderForm.waiting_bonus))
async def process_bonus(message: types.Message, state: FSMContext):
    if message.text == "🔙 Пропустить":
        await state.update_data(bonus_used=0)
        await state.set_state(OrderForm.waiting_phone)
        data = await state.get_data()
        await message.answer(
            f"👥 **Мест:** {data.get('seats', 1)}\n"
            f"💰 **Цена за место:** {format_price(data.get('price_per_seat', 0))}₽\n"
            f"💰 **Общая стоимость:** {format_price(data.get('price', 0))}₽\n\n"
            f"📞 **Ваш номер телефона**\n\n"
            f"Примеры: 89001234567, +7-900-123-45-67"
        )
    else:
        match = re.search(r'(\d+)', message.text)
        if match:
            bonus_used = int(match.group(1))
            await state.update_data(bonus_used=bonus_used)
            await state.set_state(OrderForm.waiting_phone)
            data = await state.get_data()
            price = data.get('price', 0)
            final_price = calculate_final_price(price, bonus_used)
            await message.answer(
                f"👥 **Мест:** {data.get('seats', 1)}\n"
                f"💰 **Цена за место:** {format_price(data.get('price_per_seat', 0))}₽\n"
                f"💰 **Стоимость:** {format_price(price)}₽\n"
                f"💳 **Списано бонусов:** {bonus_used}\n"
                f"💰 **Итоговая стоимость:** {format_price(final_price)}₽\n\n"
                f"📞 **Ваш номер телефона**\n\n"
                f"Примеры: 89001234567, +7-900-123-45-67"
            )
        else:
            await message.answer("❌ Выберите сумму из кнопок!")

@dp.message(StateFilter(OrderForm.waiting_phone))
async def process_phone(message: types.Message, state: FSMContext):
    if not validate_phone(message.text):
        await message.answer(
            "❌ **Неверный номер телефона!**\n\n"
            "📝 **Примеры:** 89001234567, +7-900-123-45-67\n\n"
            "Попробуйте еще раз:"
        )
        return
    
    await state.update_data(phone=message.text)
    await state.set_state(OrderForm.waiting_comment)
    update_user_phone(message.from_user.id, message.text)
    await message.answer(
        "💬 **Дополнительные пожелания?**\n\n"
        "Напишите комментарий или нажмите '⏩ Пропустить'",
        reply_markup=get_skip_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_comment))
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    comment = "Без комментария" if message.text == "⏩ Пропустить" else message.text
    await state.update_data(comment=comment)
    data['comment'] = comment
    
    total_orders = get_user_total_orders(message.from_user.id)
    bonus_earned = calculate_bonus(data.get('price', 0), total_orders)
    bonus_used = data.get('bonus_used', 0)
    final_price = calculate_final_price(data.get('price', 0), bonus_used)
    
    order_id = add_order(
        user_id=message.from_user.id,
        username=data.get('username', message.from_user.first_name),
        from_city=data.get('from_city', ''),
        to_city=data.get('to_city', ''),
        order_date=data.get('date', ''),
        order_time=data.get('time', ''),
        phone=data.get('phone', ''),
        seats=data.get('seats', 1),
        comment=comment,
        price_per_seat=data.get('price_per_seat', 0),
        price=data.get('price', 0),
        bonus_earned=bonus_earned,
        bonus_used=bonus_used,
        final_price=final_price
    )
    
    if bonus_earned > 0:
        add_bonus(message.from_user.id, bonus_earned, order_id, f"Заказ #{order_id}")
    if bonus_used > 0:
        use_bonus(message.from_user.id, bonus_used, order_id, f"Списание за заказ #{order_id}")
    
    try:
        await send_order_to_dispatcher(data, message.from_user.id, bonus_earned, bonus_used, final_price)
        
        bonus_text = ""
        if bonus_earned > 0:
            bonus_text += f"\n🎁 Начислено бонусов: +{bonus_earned}"
        if bonus_used > 0:
            bonus_text += f"\n💳 Списано бонусов: -{bonus_used}"
        
        await message.answer(
            f"✅ **ЗАКАЗ ОТПРАВЛЕН!**\n\n"
            f"📍 {data.get('from_city')} → {data.get('to_city')}\n"
            f"📅 {data.get('date')} в {data.get('time')}\n"
            f"👥 {data.get('seats')} мест\n"
            f"💰 {format_price(final_price)}₽{bonus_text}\n\n"
            f"🚕 Диспетчер свяжется с вами!",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("❌ Ошибка при отправке заказа", reply_markup=get_main_keyboard())
        await state.clear()

async def send_order_to_dispatcher(order: dict, user_id: int, bonus_earned: int, bonus_used: int, final_price: int):
    total_orders = get_user_total_orders(user_id)
    new_orders = get_user_orders_by_status(user_id, "новый")
    last_order = get_user_last_order(user_id)
    bonus_points, used_bonus = get_user_bonus(user_id)
    level, level_emoji, level_percent = get_user_level(total_orders)
    
    stats_text = ""
    if total_orders > 0:
        stats_text += f"\n📊 **СТАТИСТИКА КЛИЕНТА:**\n"
        stats_text += f"   • Всего заказов: {total_orders}\n"
        stats_text += f"   • Активных заказов: {new_orders}\n"
        stats_text += f"   • 🎁 Бонусов на счету: {bonus_points}\n"
        
        if last_order:
            last_date, last_from, last_to, last_price_per_seat, last_price = last_order
            stats_text += f"   • Последний заказ: {last_from} → {last_to} ({last_date})\n"
        
        stats_text += f"   • {level_emoji} {level} (+{level_percent})\n"
    
    order_text = (
        f"🚕 **НОВЫЙ ЗАКАЗ!**\n"
        f"{'='*35}\n"
        f"👤 **Клиент:** {order.get('username', 'Не указано')}\n"
        f"📍 **Откуда:** {order.get('from_city', 'Не указано')}\n"
        f"🏁 **Куда:** {order.get('to_city', 'Не указано')}\n"
        f"📅 **Дата:** {order.get('date', 'Не указано')}\n"
        f"⏰ **Время:** {order.get('time', 'Не указано')}\n"
        f"👥 **Мест:** {order.get('seats', 1)}\n"
        f"💰 **Цена за место:** {format_price(order.get('price_per_seat', 0))}₽\n"
        f"💰 **Стоимость:** {format_price(order.get('price', 0))}₽\n"
        f"🎁 **Начислено бонусов:** {bonus_earned}\n"
        f"💳 **Списано бонусов:** {bonus_used}\n"
        f"💰 **Итоговая стоимость:** {format_price(final_price)}₽\n"
        f"📞 **Телефон:** {order.get('phone', 'Не указано')}\n"
        f"💬 **Комментарий:** {order.get('comment', 'Без комментария')}\n"
        f"{'='*35}\n"
        f"📱 **Telegram ID:** {user_id}\n"
        f"🔗 **Ссылка:** tg://user?id={user_id}"
        f"{stats_text}"
    )
    
    await bot.send_message(
        chat_id=DISPATCHER_CHAT_ID,
        text=order_text,
        parse_mode="Markdown"
    )

# ========== ЗАПУСК БОТА ==========
async def main():
    print("=" * 60)
    print("🤖 TELEGRAM ТАКСИ БОТ (с бонусной системой)")
    print("=" * 60)
    print(f"📋 Города: {', '.join(CITIES)}")
    print(f"🎁 Бонусы: {MIN_BONUS_FOR_USE}-{MAX_BONUS_FOR_USE} баллов, шаг {BONUS_STEP}")
    print(f"👑 Администраторы: {ADMIN_IDS}")
    print("=" * 60)
    
    await send_and_pin_button()
    
    print("✅ Бот запущен и готов к работе!")
    print("=" * 60)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
