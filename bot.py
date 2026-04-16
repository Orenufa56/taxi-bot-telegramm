import os
import re
import asyncio
import logging
from datetime import datetime, timedelta
from calendar import monthcalendar
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from database import init_db, add_user, update_user_phone, add_order, get_user_history, get_user_stats

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DISPATCHER_CHAT_ID = "-1003980266463"
CLIENT_GROUP_ID = "-1003898088390"
# =================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация БД (один раз)
init_db()

# ========== СПИСОК ГОРОДОВ ==========
CITIES = [
    "Оренбург", "Уфа", "Толбазы", "Стерлитамак",
    "Салават", "Мелеуз", "Кумертау", "Мурапталово", "Октябрьское"
]

# ========== ДОСТУПНОЕ ВРЕМЯ ==========
AVAILABLE_TIMES = ["6:00", "9:00", "12:00", "15:00", "18:00", "21:00-23:00"]

# ========== ИНЛАЙН-КЛАВИАТУРЫ ==========

def get_main_inline_keyboard():
    """Главная клавиатура"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚕 Новый заказ", callback_data="new_order")],
            [InlineKeyboardButton(text="❓ Частые вопросы", callback_data="faq"),
             InlineKeyboardButton(text="📜 История", callback_data="history")],
            [InlineKeyboardButton(text="📞 Контакты", callback_data="faq_contacts"),
             InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
            [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
        ]
    )

def get_cities_inline_keyboard():
    """Клавиатура выбора города"""
    buttons = []
    row = []
    for i, city in enumerate(CITIES):
        row.append(InlineKeyboardButton(text=city, callback_data=f"city_{city}"))
        if len(row) == 3 or i == len(CITIES) - 1:
            buttons.append(row)
            row = []
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_time_inline_keyboard():
    """Клавиатура выбора времени"""
    buttons = []
    row = []
    for time in AVAILABLE_TIMES:
        row.append(InlineKeyboardButton(text=time, callback_data=f"time_{time}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cities")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_calendar_keyboard(year: int = None, month: int = None):
    """Календарь для выбора даты"""
    if year is None or month is None:
        now = datetime.now()
        year = now.year
        month = now.month
    
    months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
              "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    nav_buttons = [
        InlineKeyboardButton(text="◀️", callback_data=f"calendar_{prev_year}_{prev_month}"),
        InlineKeyboardButton(text=f"{months[month-1]} {year}", callback_data="ignore"),
        InlineKeyboardButton(text="▶️", callback_data=f"calendar_{next_year}_{next_month}")
    ]
    
    weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    week_buttons = [InlineKeyboardButton(text=day, callback_data="ignore") for day in weekdays]
    
    month_days = monthcalendar(year, month)
    day_buttons = []
    for week in month_days:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))
            else:
                date_str = f"{day:02d}.{month:02d}.{str(year)[-2:]}"
                row.append(InlineKeyboardButton(text=str(day), callback_data=f"date_{date_str}"))
        day_buttons.append(row)
    
    keyboard = [nav_buttons, week_buttons] + day_buttons
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_faq_inline_keyboard():
    """Клавиатура FAQ"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💰 Стоимость проезда", callback_data="faq_price")],
            [InlineKeyboardButton(text="⏰ Время выезда", callback_data="faq_time"),
             InlineKeyboardButton(text="🕐 Время в пути", callback_data="faq_travel")],
            [InlineKeyboardButton(text="📦 Посылки", callback_data="faq_parcels"),
             InlineKeyboardButton(text="🚕 Забрать до адреса", callback_data="faq_address")],
            [InlineKeyboardButton(text="📍 Точки отправления", callback_data="faq_points")],
            [InlineKeyboardButton(text="🐕 Животные", callback_data="faq_animals"),
             InlineKeyboardButton(text="🧳 Багаж", callback_data="faq_luggage")],
            [InlineKeyboardButton(text="🚭 Курить в машине", callback_data="faq_smoking"),
             InlineKeyboardButton(text="📞 Контакты", callback_data="faq_contacts")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )

def get_skip_inline_keyboard():
    """Клавиатура пропуска комментария"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏩ Пропустить", callback_data="skip_comment")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_phone")]
        ]
    )

def get_back_inline_keyboard():
    """Клавиатура с кнопкой назад"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ]
    )

def get_group_button():
    """Кнопка для закрепления в группе"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚕 Заказать такси", url="https://t.me/Taxi56OrenUfabot")]
        ]
    )

# ========== СОСТОЯНИЯ FSM ==========
class OrderForm(StatesGroup):
    waiting_name = State()
    waiting_from_city = State()
    waiting_to_city = State()
    waiting_date = State()
    waiting_time = State()
    waiting_phone = State()
    waiting_comment = State()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

async def send_and_pin_button():
    """Отправляет и закрепляет кнопку в группе"""
    try:
        try:
            chat_info = await bot.get_chat(chat_id=CLIENT_GROUP_ID)
            if chat_info.pinned_message:
                await bot.unpin_chat_message(chat_id=CLIENT_GROUP_ID)
        except:
            pass
        
        msg = await bot.send_message(
            chat_id=CLIENT_GROUP_ID,
            text="🚕 **Бот для заказа такси Оренбург - Уфа**\n\n"
                 "📋 **Как оформить заказ:**\n\n"
                 "1️⃣ Нажмите на кнопку ниже\n"
                 "2️⃣ В личном чате с ботом нажмите /start\n"
                 "3️⃣ Выберите '🚕 Новый заказ' и следуйте инструкциям\n\n"
                 "💰 **Стоимость:**\n"
                 "• Место: 2300 руб.\n"
                 "• 4-местное авто: 9200 руб.\n"
                 "• 6-местное авто: 13800 руб.\n\n"
                 "⏰ **Время выезда:** 6:00, 9:00, 12:00, 15:00, 18:00, 21:00-23:00\n\n"
                 "📍 **Точки отправления:**\n"
                 "• Оренбург: ТЦ Север\n"
                 "• Уфа: Универмаг 'Уфа'\n\n"
                 "📞 **Контакты диспетчера:** +7 9292 80 7979\n\n"
                 "👇 **Нажмите на кнопку ниже, чтобы оформить заказ**",
            reply_markup=get_group_button(),
            parse_mode="Markdown"
        )
        await bot.pin_chat_message(chat_id=CLIENT_GROUP_ID, message_id=msg.message_id)
        logging.info("✅ Кнопка отправлена и закреплена в группе клиентов!")
        return True
    except Exception as e:
        logging.error(f"❌ Ошибка: {e}")
        return False

def validate_phone(phone: str) -> bool:
    """Проверка номера телефона"""
    cleaned = re.sub(r'[\s\+\(\)\-]', '', phone)
    return cleaned.isdigit() and 10 <= len(cleaned) <= 12

def is_date_past(date_str: str) -> bool:
    """Проверка, не прошла ли дата"""
    try:
        order_date = datetime.strptime(date_str, "%d.%m.%y")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return order_date < today
    except:
        return True

async def send_order_to_dispatcher(order: dict, user_id: int, username: str = None):
    """Отправляет заказ диспетчеру"""
    order_text = (
        f"🚕 **НОВЫЙ ЗАКАЗ!**\n\n"
        f"👤 Клиент: {order.get('username', 'Не указано')}\n"
        f"📍 Откуда: {order.get('from_city', 'Не указано')}\n"
        f"🏁 Куда: {order.get('to_city', 'Не указано')}\n"
        f"📅 Дата: {order.get('date', 'Не указано')}\n"
        f"⏰ Время: {order.get('time', 'Не указано')}\n"
        f"📞 Телефон: {order.get('phone', 'Не указано')}\n"
        f"💬 Комментарий: {order.get('comment', 'Без комментария')}\n\n"
        f"📱 Telegram: @{username if username else user_id}"
    )
    await bot.send_message(
        chat_id=DISPATCHER_CHAT_ID,
        text=order_text,
        parse_mode="Markdown"
    )

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Если сообщение из группы
    if chat_id != user_id:
        rules_text = (
            "🚕 **Бот для заказа такси Оренбург - Уфа**\n\n"
            "📋 **Правила пользования:**\n\n"
            "💰 **Стоимость:**\n"
            "• Место: 2300 руб.\n"
            "• 4-местное авто: 9200 руб.\n"
            "• 6-местное авто: 13800 руб.\n\n"
            "⏰ **Время выезда:** 6:00, 9:00, 12:00, 15:00, 18:00, 21:00-23:00\n\n"
            "📍 **Точки отправления:**\n"
            "• Оренбург: ТЦ Север\n"
            "• Уфа: Универмаг 'Уфа'\n\n"
            "📞 **Контакты диспетчера:** +7 9292 80 7979\n\n"
            "👇 **Нажмите на закреплённую кнопку выше, чтобы оформить заказ**"
        )
        await message.answer(rules_text, parse_mode="Markdown")
        return
    
    # Личное сообщение
    await message.answer(
        f"🚕 **Добро пожаловать, {message.from_user.first_name}!**\n\n"
        "Я помогу вам быстро и комфортно добраться между городами.\n\n"
        "👇 **Выберите действие:**",
        reply_markup=get_main_inline_keyboard()
    )

# ========== CALLBACK-ОБРАБОТЧИКИ ==========

@dp.callback_query(F.data == "new_order")
async def callback_new_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await state.set_state(OrderForm.waiting_name)
    await state.update_data(username=callback.from_user.first_name)
    
    await callback.message.edit_text(
        "🚕 **Начинаем оформление заказа!**\n\n"
        "👤 **Как к вам обращаться?**\n"
        "(Напишите ваше имя)",
        reply_markup=get_back_inline_keyboard()
    )

@dp.callback_query(F.data == "history")
async def callback_history(callback: types.CallbackQuery):
    await callback.answer()
    orders = get_user_history(callback.from_user.id)
    stats = get_user_stats(callback.from_user.id)
    
    if not orders:
        await callback.message.edit_text(
            "📜 **История поездок**\n\n"
            "У вас пока нет ни одной поездки.\n\n"
            "Нажмите '🚕 Новый заказ', чтобы сделать первый заказ!",
            reply_markup=get_back_inline_keyboard()
        )
        return
    
    history_text = "📜 **История ваших поездок**\n\n"
    for i, order in enumerate(orders, 1):
        from_city, to_city, order_date, order_time, created_at, status = order
        history_text += (
            f"{i}. 📍 {from_city} → {to_city}\n"
            f"   📅 {order_date} в {order_time}\n"
            f"   📅 Заказ: {created_at.split()[0]}\n"
            f"   🏷 Статус: {status}\n\n"
        )
    
    if stats:
        total_orders, phone, _, _ = stats
        history_text += f"📊 **Всего поездок:** {total_orders}\n"
        if phone:
            history_text += f"📞 **Ваш телефон:** {phone}"
    
    await callback.message.edit_text(history_text, reply_markup=get_back_inline_keyboard())

@dp.callback_query(F.data == "faq")
async def callback_faq(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "❓ **Часто задаваемые вопросы**\n\n"
        "Выберите интересующий вас вопрос:",
        reply_markup=get_faq_inline_keyboard()
    )

@dp.callback_query(F.data == "help")
async def callback_help(callback: types.CallbackQuery):
    await callback.answer()
    help_text = (
        "ℹ️ **Помощь по использованию бота**\n\n"
        "📌 **Основные команды:**\n"
        "• 🚕 Новый заказ - начать оформление поездки\n"
        "• ❓ Частые вопросы - ответы на популярные вопросы\n"
        "• 📜 История - посмотреть историю поездок\n"
        "• 📞 Контакты - контакты диспетчера\n"
        "• ❌ Отмена - отменить текущий заказ\n\n"
        "📝 **Как оформить заказ:**\n"
        "1️⃣ Нажмите '🚕 Новый заказ'\n"
        "2️⃣ Введите ваше имя\n"
        "3️⃣ Выберите город отправления\n"
        "4️⃣ Выберите город назначения\n"
        "5️⃣ Выберите дату в календаре\n"
        "6️⃣ Выберите время\n"
        "7️⃣ Укажите номер телефона\n"
        "8️⃣ Добавьте комментарий\n\n"
        "💰 **Оплата:** наличными водителю или переводом на карту\n\n"
        "📞 **Контакты поддержки:** +79292807979"
    )
    await callback.message.edit_text(help_text, reply_markup=get_back_inline_keyboard())

@dp.callback_query(F.data == "cancel")
async def callback_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        "❌ **Действие отменено**\n\n"
        "Выберите действие в меню:",
        reply_markup=get_main_inline_keyboard()
    )

@dp.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        f"🚕 **Добро пожаловать, {callback.from_user.first_name}!**\n\n"
        "👇 **Выберите действие:**",
        reply_markup=get_main_inline_keyboard()
    )

@dp.callback_query(F.data == "back_to_cities")
async def callback_back_to_cities(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(OrderForm.waiting_from_city)
    await callback.message.edit_text(
        "📍 **Выберите город отправления:**",
        reply_markup=get_cities_inline_keyboard()
    )

@dp.callback_query(F.data == "back_to_phone")
async def callback_back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(OrderForm.waiting_phone)
    await callback.message.edit_text(
        "📞 **Ваш номер телефона**\n\n"
        "📝 **Примеры:** 89001234567, +7-900-123-45-67",
        reply_markup=get_back_inline_keyboard()
    )

@dp.callback_query(F.data.startswith("calendar_"))
async def callback_calendar(callback: types.CallbackQuery):
    await callback.answer()
    data = callback.data.split("_")
    if len(data) == 3 and data[1] != "ignore":
        year = int(data[1])
        month = int(data[2])
        await callback.message.edit_reply_markup(reply_markup=get_calendar_keyboard(year, month))

@dp.callback_query(F.data.startswith("date_"))
async def callback_date_selected(callback: types.CallbackQuery, state: FSMContext):
    date_str = callback.data.replace("date_", "")
    
    if is_date_past(date_str):
        await callback.answer("❌ Нельзя выбрать прошедшую дату!", show_alert=True)
        return
    
    await state.update_data(date=date_str)
    await state.set_state(OrderForm.waiting_time)
    await callback.message.edit_text(
        f"📅 **Выбрана дата:** {date_str}\n\n"
        f"⏰ **Выберите время отправления:**",
        reply_markup=get_time_inline_keyboard()
    )

@dp.callback_query(F.data.startswith("time_"))
async def callback_time_selected(callback: types.CallbackQuery, state: FSMContext):
    time_str = callback.data.replace("time_", "")
    await state.update_data(time=time_str)
    await state.set_state(OrderForm.waiting_phone)
    
    await callback.message.edit_text(
        f"⏰ **Выбрано время:** {time_str}\n\n"
        f"📞 **Ваш номер телефона**\n\n"
        f"📝 **Примеры:** 89001234567, +7-900-123-45-67",
        reply_markup=get_back_inline_keyboard()
    )

@dp.callback_query(F.data == "skip_comment")
async def callback_skip_comment(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    await state.update_data(comment="Без комментария")
    data['comment'] = "Без комментария"
    
    add_order(
        user_id=callback.from_user.id,
        username=data.get('username', callback.from_user.first_name),
        from_city=data.get('from_city', ''),
        to_city=data.get('to_city', ''),
        order_date=data.get('date', ''),
        order_time=data.get('time', ''),
        phone=data.get('phone', ''),
        comment="Без комментария"
    )
    
    update_user_phone(callback.from_user.id, data.get('phone', ''))
    
    try:
        await send_order_to_dispatcher(
            order=data,
            user_id=callback.from_user.id,
            username=callback.from_user.username
        )
        
        await callback.message.edit_text(
            f"✅ **ЗАКАЗ УСПЕШНО ОТПРАВЛЕН!**\n\n"
            f"📝 **Детали заказа:**\n"
            f"📍 {data.get('from_city', '?')} → {data.get('to_city', '?')}\n"
            f"📅 {data.get('date', '?')}\n"
            f"⏰ {data.get('time', '?')}\n"
            f"📞 {data.get('phone', '?')}\n"
            f"💬 Комментарий: Без комментария\n\n"
            f"🚕 **Диспетчер свяжется с вами в ближайшее время!**\n\n"
            f"⭐ Спасибо, что выбрали наш сервис!",
            reply_markup=get_main_inline_keyboard()
        )
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await callback.message.edit_text(
            "❌ **Ошибка при отправке заказа**\n\nПожалуйста, попробуйте позже.",
            reply_markup=get_main_inline_keyboard()
        )
        await state.clear()

# ========== ОБРАБОТЧИКИ ВЫБОРА ГОРОДОВ ==========

@dp.callback_query(F.data.startswith("city_"))
async def callback_city_selection(callback: types.CallbackQuery, state: FSMContext):
    city = callback.data.replace("city_", "")
    current_state = await state.get_state()
    
    if current_state == OrderForm.waiting_from_city:
        await state.update_data(from_city=city)
        await state.set_state(OrderForm.waiting_to_city)
        await callback.message.edit_text(
            f"📍 **Откуда:** {city}\n\n"
            f"🏁 **Выберите город назначения:**",
            reply_markup=get_cities_inline_keyboard()
        )
    elif current_state == OrderForm.waiting_to_city:
        data = await state.get_data()
        if city == data.get('from_city'):
            await callback.answer("❌ Город назначения не может совпадать с городом отправления!", show_alert=True)
            return
        await state.update_data(to_city=city)
        await state.set_state(OrderForm.waiting_date)
        await callback.message.edit_text(
            f"📍 **Маршрут:** {data.get('from_city')} → {city}\n\n"
            f"📅 **Выберите дату поездки:**",
            reply_markup=get_calendar_keyboard()
        )
    await callback.answer()

# ========== РАЗВЁРНУТЫЕ FAQ ОТВЕТЫ ==========

faq_answers = {
    "faq_price": "💰 **Стоимость проезда**\n\nСтоимость поездки рассчитывается индивидуально:\n\n• **Одно место:** 2300 руб.\n  (средний чемодан входит в стоимость)\n\n• **4-местное авто:** 9200 руб.\n  (комфортабельный автомобиль для компании)\n\n• **6-местное авто:** 13800 руб.\n  (микроавтобус для большой компании)\n\n📞 **Точную стоимость уточняйте у диспетчера при оформлении заказа!**",
    
    "faq_time": "⏰ **Время выезда**\n\nДоступное время отправления:\n\n🕐  6:00, 9:00\n🕐  12:00, 15:00\n🕐  18:00\n🕐  21:00 - 23:00\n\n⚠️ **Важно:**\n• Время в пути может меняться из-за погоды\n• При заказе указывайте точное время\n• Диспетчер подтвердит наличие мест",
    
    "faq_travel": "🕐 **Время в пути**\n\nСтандартное время в пути между городами:\n\n• **Оренбург — Уфа:** 4-5 часов\n• **Оренбург — Стерлитамак:** 3-4 часа\n• **Уфа — Салават:** 2-3 часа\n\n⚠️ **Факторы, влияющие на время:**\n• Погодные условия\n• Загруженность трассы\n• Время суток\n• Дорожные работы\n\n📞 Диспетчер предупредит вас о возможных задержках.",
    
    "faq_parcels": "📦 **Перевозка посылок**\n\nМы осуществляем доставку посылок между городами!\n\n💰 **Стоимость:** от 500 руб.\n• Цена формируется от размера и веса посылки\n• Хрупкие грузы упаковываются отдельно\n\n📋 **Как отправить посылку:**\n1. Оформите заказ с пометкой 'Посылка'\n2. Укажите вес и размеры\n3. Сообщите, кто будет отправлять и получать\n\n📞 Для точного расчета стоимости свяжитесь с диспетчером.",
    
    "faq_address": "🚕 **Забрать и довезти до адреса**\n\nМы можем забрать вас от любого адреса и довезти до нужного места!\n\n💰 **Дополнительная плата:** от 300 руб.\n• Зависит от удаленности от точки сбора\n• Стоимость обсуждается с водителем\n\n📍 **Стандартные точки сбора (бесплатно):**\n• Оренбург: ТЦ Север\n• Уфа: Универмаг 'Уфа'\n\n⚠️ **При оформлении заказа укажите точный адрес в комментарии!**",
    
    "faq_points": "📍 **Точки отправления и прибытия**\n\n🏁 **Оренбург:**\nТЦ Север, пр. Дзержинского 23, вход 2\n\n🏁 **Уфа:**\nУнивермаг 'Уфа', пр. Октября 31\n\n🏁 **Другие города:**\n• Стерлитамак — Автовокзал\n• Салават — Автовокзал\n• Мелеуз — Автовокзал\n• Кумертау — КПМ\n\n⚠️ **По другим адресам возможна подача с дополнительной платой.**",
    
    "faq_animals": "🐕 **Перевозка животных**\n\n✅ Да, мы перевозим животных!\n\n📋 **Правила перевозки:**\n• Обязательно наличие переноски (для кошек и мелких собак)\n• Для крупных собак нужен намордник и поводок\n• Животное не должно мешать водителю\n• Возможна дополнительная плата за уборку салона\n\n💰 **Стоимость:** уточняйте у диспетчера\n\n⚠️ **Важно:** Укажите в комментарии к заказу, что вы будете с животным, а также породу и размер!",
    
    "faq_luggage": "🧳 **Перевозка багажа**\n\n📋 **Правила перевозки багажа:**\n\n• Средний чемодан уже входит в стоимость места (2300 руб.)\n• Багаж перевозится бесплатно в пределах разумного\n• Если у вас много багажа, укажите это в комментарии\n• При необходимости можно заказать автомобиль с увеличенным багажником\n\n📦 **Крупногабаритный багаж:**\n• Велосипеды, лыжи, сноуборды\n• Стоимость обсуждается отдельно\n\n💡 **Совет:** Для крупногабаритного багажа уточните детали у диспетчера.",
    
    "faq_smoking": "🚭 **Курение в автомобиле**\n\n❌ **Курение в салоне автомобиля строго запрещено!**\n\n💰 **Штраф за курение:** 5000 рублей\n(на профессиональную химчистку салона)\n\n✅ **Что можно делать:**\n• Курить на остановках (попросите водителя)\n\n📞 Если вам нужно покурить, попросите водителя сделать остановку.\n\n✅ Благодарим за понимание и уважение к нашему транспорту!",
    
    "faq_contacts": "📞 **Контакты для связи**\n\n📱 **По всем вопросам обращайтесь:**\n\n• Диспетчерская служба: +79058907979\n• Телефон диспетчера: +7 9292 80 7979\n\n🕐 **Время работы диспетчерской:**\n• Ежедневно: Круглосуточно\n• Без выходных\n\n📧 **Email для предложений:** orenufa56@gmail.com\n\n💬 **Мы в соцсетях:**\n• ВКонтакте: vk.com/ufaoren\n\n📞 **Срочные вопросы звоните!**"
}

@dp.callback_query(F.data.startswith("faq_"))
async def callback_faq_answer(callback: types.CallbackQuery):
    await callback.answer()
    answer = faq_answers.get(callback.data, "Информация временно недоступна")
    await callback.message.edit_text(
        answer,
        reply_markup=get_faq_inline_keyboard()
    )

# ========== ОСНОВНОЙ ХЭНДЛЕР ЗАКАЗА (FSM) ==========

@dp.message(StateFilter(OrderForm.waiting_name))
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text) > 100:
        await message.answer("❌ Имя слишком длинное! Введите имя короче:")
        return
    
    await state.update_data(username=message.text)
    await state.set_state(OrderForm.waiting_from_city)
    
    await message.answer(
        f"👋 **Приятно познакомиться, {message.text}!**\n\n"
        f"📍 **Выберите город отправления:**",
        reply_markup=get_cities_inline_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_phone))
async def process_phone(message: types.Message, state: FSMContext):
    if not validate_phone(message.text):
        await message.answer(
            "❌ **Неверный номер телефона!**\n\n"
            "📝 **Примеры:** 89001234567, +7-900-123-45-67\n\n"
            "Попробуйте еще раз:",
            reply_markup=get_back_inline_keyboard()
        )
        return
    
    await state.update_data(phone=message.text)
    await state.set_state(OrderForm.waiting_comment)
    
    await message.answer(
        "💬 **Дополнительные пожелания?**\n\n"
        "Напишите комментарий или нажмите кнопку 'Пропустить'",
        reply_markup=get_skip_inline_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_comment))
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    comment = message.text
    
    await state.update_data(comment=comment)
    data['comment'] = comment
    
    add_order(
        user_id=message.from_user.id,
        username=data.get('username', message.from_user.first_name),
        from_city=data.get('from_city', ''),
        to_city=data.get('to_city', ''),
        order_date=data.get('date', ''),
        order_time=data.get('time', ''),
        phone=data.get('phone', ''),
        comment=comment
    )
    
    update_user_phone(message.from_user.id, data.get('phone', ''))
    
    try:
        await send_order_to_dispatcher(
            order=data,
            user_id=message.from_user.id,
            username=message.from_user.username
        )
        
        await message.answer(
            f"✅ **ЗАКАЗ УСПЕШНО ОТПРАВЛЕН!**\n\n"
            f"📝 **Детали заказа:**\n"
            f"📍 {data.get('from_city', '?')} → {data.get('to_city', '?')}\n"
            f"📅 {data.get('date', '?')}\n"
            f"⏰ {data.get('time', '?')}\n"
            f"📞 {data.get('phone', '?')}\n"
            f"💬 Комментарий: {comment}\n\n"
            f"🚕 **Диспетчер свяжется с вами в ближайшее время!**\n\n"
            f"⭐ Спасибо, что выбрали наш сервис!",
            reply_markup=get_main_inline_keyboard()
        )
        await state.clear()
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer(
            "❌ **Ошибка при отправке заказа**\n\nПожалуйста, попробуйте позже.",
            reply_markup=get_main_inline_keyboard()
        )
        await state.clear()

# ========== ЗАПУСК БОТА ==========
async def main():
    print("=" * 60)
    print("🤖 TELEGRAM ТАКСИ БОТ")
    print("=" * 60)
    print("📨 Заказы отправляются диспетчеру")
    print("=" * 60)
    
    await send_and_pin_button()
    
    print("✅ Бот запущен и готов к работе!")
    print("=" * 60)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
