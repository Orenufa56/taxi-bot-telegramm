import os
import re
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ========== НАСТРОЙКИ - ЗАМЕНИТЕ НА СВОИ! ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
DISPATCHER_CHAT_ID = "-1003980266463"
# ====================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== СПИСОК ГОРОДОВ ==========
CITIES = [
    "Оренбург", "Уфа", "Толбазы", "Стерлитамак",
    "Салават", "Мелеуз", "Кумертау", "Мурапталово", "Октябрьское"
]

# ========== КЛАВИАТУРЫ (ИСПРАВЛЕННЫЕ) ==========

def get_main_keyboard():
    """Главная клавиатура"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚕 Новый заказ")],
            [KeyboardButton(text="❓ Частые вопросы"), KeyboardButton(text="❌ Отмена")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )

def get_cities_keyboard():
    """Клавиатура с городами (3 колонки)"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Оренбург"), KeyboardButton(text="Уфа"), KeyboardButton(text="Толбазы")],
            [KeyboardButton(text="Стерлитамак"), KeyboardButton(text="Салават"), KeyboardButton(text="Мелеуз")],
            [KeyboardButton(text="Кумертау"), KeyboardButton(text="Мурапталово"), KeyboardButton(text="Октябрьское")]
        ],
        resize_keyboard=True
    )

def get_skip_keyboard():
    """Клавиатура с кнопкой пропуска"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏩ Пропустить")]],
        resize_keyboard=True
    )

def get_faq_keyboard():
    """Клавиатура с часто задаваемыми вопросами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Стоимость проезда")],
            [KeyboardButton(text="⏰ Время выезда"), KeyboardButton(text="🕐 Время в пути")],
            [KeyboardButton(text="📦 Посылки"), KeyboardButton(text="🚕 Забрать до адреса")],
            [KeyboardButton(text="📍 Точки отправления")],
            [KeyboardButton(text="🐕 Животные"), KeyboardButton(text="🧳 Багаж")],
            [KeyboardButton(text="🚭 Курить в машине")],
            [KeyboardButton(text="📞 Контакты")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

# ========== СОСТОЯНИЯ FSM ==========
class OrderForm(StatesGroup):
    waiting_name = State()
    waiting_from_city = State()
    waiting_to_city = State()
    waiting_time = State()
    waiting_phone = State()
    waiting_comment = State()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def format_time_with_dots(text: str) -> str:
    """Автоматически расставляет точки в дате и времени"""
    clean = re.sub(r'[\.\s]', '', text)
    if len(clean) >= 12:
        return f"{clean[0:2]}.{clean[2:4]}.{clean[4:6]} в {clean[6:8]}:{clean[8:10]}"
    elif len(clean) >= 10:
        return f"{clean[0:2]}.{clean[2:4]}.{clean[4:6]} в {clean[6:8]}:{clean[8:10]}"
    elif len(clean) >= 8:
        return f"{clean[0:2]}.{clean[2:4]}.{clean[4:6]} в {clean[6:8]}:"
    elif len(clean) >= 6:
        return f"{clean[0:2]}.{clean[2:4]}.{clean[4:6]} в "
    elif len(clean) >= 4:
        return f"{clean[0:2]}.{clean[2:4]}."
    elif len(clean) >= 2:
        return f"{clean[0:2]}."
    return text

def validate_phone(phone: str) -> bool:
    """Проверка телефона"""
    cleaned = re.sub(r'[\s\+\(\)\-]', '', phone)
    return cleaned.isdigit() and 10 <= len(cleaned) <= 12

def validate_time(time_str: str) -> bool:
    """Проверка формата даты и времени"""
    pattern = re.compile(r'^\d{2}\.\d{2}\.\d{2} в \d{2}:\d{2}$')
    if not pattern.match(time_str):
        return False
    try:
        datetime.strptime(time_str, "%d.%m.%y в %H:%M")
        return True
    except:
        return False

# ========== ОТПРАВКА ЗАКАЗА ДИСПЕТЧЕРУ ==========
async def send_order_to_dispatcher(order: dict, user_id: int, username: str = None):
    """Отправляет заказ диспетчеру"""
    # Безопасное получение комментария
    comment = order.get('comment', 'Без комментария')
    
    order_text = (
        f"🚕 **НОВЫЙ ЗАКАЗ!**\n\n"
        f"👤 Клиент: {order.get('username', 'Не указано')}\n"
        f"📍 Откуда: {order.get('from_city', 'Не указано')}\n"
        f"🏁 Куда: {order.get('to_city', 'Не указано')}\n"
        f"⏰ Время: {order.get('time', 'Не указано')}\n"
        f"📞 Телефон: {order.get('phone', 'Не указано')}\n"
        f"💬 Комментарий: {comment}\n\n"
        f"📱 Telegram: @{username if username else user_id}"
    )
    await bot.send_message(
        chat_id=DISPATCHER_CHAT_ID,
        text=order_text,
        parse_mode="Markdown"
    )

# ========== ПРИВЕТСТВИЕ ==========
async def send_welcome(message: types.Message):
    """Отправляет приветственное сообщение"""
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"🚕 **Добро пожаловать, {user_name}!**\n\n"
        "Я помогу вам быстро и комфортно добраться между городами:\n"
        f"• {', '.join(CITIES)}\n\n"
        "📌 **Что я умею:**\n"
        "✅ Заказать такси с выбором городов\n"
        "✅ Ответить на частые вопросы\n"
        "✅ Отменить заказ\n\n"
        "👇 **Нажмите на кнопку ниже, чтобы начать**"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

# ========== КОМАНДЫ ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await send_welcome(message)

@dp.message(F.text == "🚕 Новый заказ")
async def new_order(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderForm.waiting_name)
    await state.update_data(username=message.from_user.first_name)
    
    await message.answer(
        "🚕 **Начинаем оформление заказа!**\n\n"
        "👤 **Как к вам обращаться?**\n"
        "(Напишите ваше имя)",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "❌ Отмена")
@dp.message(Command("cancel"))
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ **Заказ отменен**\n\n"
        "Если захотите сделать новый заказ, нажмите '🚕 Новый заказ'",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text == "ℹ️ Помощь")
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "ℹ️ **Помощь по использованию бота**\n\n"
        "📌 **Основные команды:**\n"
        "• 🚕 Новый заказ - начать оформление поездки\n"
        "• ❓ Частые вопросы - ответы на популярные вопросы\n"
        "• ❌ Отмена - отменить текущий заказ\n\n"
        "📝 **Как оформить заказ:**\n"
        "1️⃣ Нажмите '🚕 Новый заказ'\n"
        "2️⃣ Введите ваше имя\n"
        "3️⃣ Выберите город отправления\n"
        "4️⃣ Выберите город назначения\n"
        "5️⃣ Укажите дату и время (формат: 04.04.26 в 15:00)\n"
        "6️⃣ Укажите номер телефона\n"
        "7️⃣ Добавьте комментарий или нажмите 'Пропустить'\n\n"
        "💰 **Оплата:**\n"
        "• Наличными водителю\n"
        "• Переводом на карту\n\n"
        "📞 **Контакты поддержки:**\n"
        "• По всем вопросам: +79292807979\n\n"
        "❓ **Есть вопросы?** Нажмите '❓ Частые вопросы'"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())

# ========== ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ ==========
@dp.message(F.text == "❓ Частые вопросы")
async def show_faq(message: types.Message):
    await message.answer(
        "❓ **Часто задаваемые вопросы**\n\n"
        "Выберите интересующий вас вопрос из кнопок ниже:",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "💰 Стоимость проезда")
async def faq_price(message: types.Message):
    await message.answer(
        "💰 **Стоимость проезда**\n\n"
        "Стоимость поездки рассчитывается индивидуально:\n\n"
        "• **Одно место:** 2300 руб.\n"
        "  (средний чемодан входит в стоимость)\n\n"
        "• **4-местное авто:** 9200 руб.\n"
        "• **6-местное авто:** 13800 руб.\n\n"
        "📞 **Точную стоимость уточняйте у диспетчера!**",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "⏰ Время выезда")
async def faq_departure_time(message: types.Message):
    await message.answer(
        "⏰ **Время выезда**\n\n"
        "Доступное время отправления: 6:00, 9:00, 12:00, 15:00, 18:00, 21:00, 22:00, 23:00\n\n"
        "⚠️ При заказе указывайте точное время",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🕐 Время в пути")
async def faq_travel_time(message: types.Message):
    await message.answer(
        "🕐 **Время в пути**\n\n"
        "• **Оренбург — Уфа:** 4-5 часов\n"
        "• **Оренбург — Стерлитамак:** 3-4 часа\n\n"
        "⚠️ Время может меняться из-за погоды",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "📦 Посылки")
async def faq_parcels(message: types.Message):
    await message.answer(
        "📦 **Перевозка посылок**\n\n"
        "💰 **Стоимость:** от 500 руб.\n"
        "📞 Для точного расчета свяжитесь с диспетчером",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🚕 Забрать до адреса")
async def faq_address_delivery(message: types.Message):
    await message.answer(
        "🚕 **Забрать до адреса**\n\n"
        "💰 **Дополнительная плата:** от 300 руб.\n"
        "📍 **Стандартные точки:** Оренбург (ТЦ Север), Уфа (Универмаг 'Уфа')",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "📍 Точки отправления")
async def faq_departure_points(message: types.Message):
    await message.answer(
        "📍 **Точки отправления**\n\n"
        "🏁 **Оренбург:** ТЦ Север, пр. Дзержинского 23\n"
        "🏁 **Уфа:** Универмаг 'Уфа', пр. Октября 31",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🐕 Животные")
async def faq_animals(message: types.Message):
    await message.answer(
        "🐕 **Перевозка животных**\n\n"
        "✅ Да, мы перевозим животных\n"
        "📋 Нужна переноска или намордник\n"
        "⚠️ Укажите в комментарии",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🧳 Багаж")
async def faq_luggage(message: types.Message):
    await message.answer(
        "🧳 **Багаж**\n\n"
        "• Средний чемодан входит в стоимость\n"
        "• Для крупного багажа уточните у диспетчера",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🚭 Курить в машине")
async def faq_smoking(message: types.Message):
    await message.answer(
        "🚭 **Курение в автомобиле**\n\n"
        "❌ Курение в салоне **строго запрещено**\n"
        "💰 Штраф: 5000 рублей",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "📞 Контакты")
async def faq_contacts(message: types.Message):
    await message.answer(
        "📞 **Контакты**\n\n"
        "📱 Диспетчер: +7 9292 80 7979\n"
        "🕐 Круглосуточно\n"
        "📧 orenufa56@gmail.com",
        reply_markup=get_faq_keyboard()
    )

@dp.message(F.text == "🔙 Назад")
async def back_to_main(message: types.Message):
    await message.answer(
        "🔙 **Главное меню**",
        reply_markup=get_main_keyboard()
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
        reply_markup=get_cities_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_from_city))
async def process_from_city(message: types.Message, state: FSMContext):
    if message.text not in CITIES:
        await message.answer("❌ Пожалуйста, выберите город из кнопок!", reply_markup=get_cities_keyboard())
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
        await message.answer("❌ Пожалуйста, выберите город из кнопок!", reply_markup=get_cities_keyboard())
        return
    
    data = await state.get_data()
    if message.text == data.get('from_city'):
        await message.answer("❌ Город назначения не может совпадать с городом отправления!", reply_markup=get_cities_keyboard())
        return
    
    await state.update_data(to_city=message.text)
    await state.set_state(OrderForm.waiting_time)
    
    await message.answer(
        f"📍 **Маршрут:** {data['from_city']} → {message.text}\n\n"
        f"⏰ **Укажите дату и время подачи**\n\n"
        f"📅 **Формат:** `04.04.26 в 15:00`\n"
        f"📝 **Пример:** 25.12.26 в 09:30\n\n"
        f"💡 **Подсказка:** просто вводите цифры подряд",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(StateFilter(OrderForm.waiting_time))
async def process_time(message: types.Message, state: FSMContext):
    formatted_time = format_time_with_dots(message.text)
    
    if not validate_time(formatted_time):
        await message.answer(
            f"❌ **Неверный формат!**\n\n"
            f"Используйте формат: `04.04.26 в 15:00`\n\n"
            f"📝 **Пример:** 2504261500 → 25.04.26 в 15:00"
        )
        return
    
    await state.update_data(time=formatted_time)
    await state.set_state(OrderForm.waiting_phone)
    
    await message.answer(
        f"⏰ **Время подачи:** {formatted_time}\n\n"
        f"📞 **Ваш номер телефона**\n\n"
        f"📝 **Примеры:** 89001234567, +7-900-123-45-67"
    )

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
    
    await message.answer(
        "💬 **Дополнительные пожелания?**\n\n"
        "Напишите комментарий или нажмите кнопку 'Пропустить'",
        reply_markup=get_skip_keyboard()
    )

@dp.message(StateFilter(OrderForm.waiting_comment))
async def process_comment(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    if message.text == "⏩ Пропустить":
        comment = "Без комментария"
    else:
        comment = message.text
    
    await state.update_data(comment=comment)
    
    try:
        await send_order_to_dispatcher(
            order=data,
            user_id=message.from_user.id,
            username=message.from_user.username
        )
        
        await message.answer(
            f"✅ **ЗАКАЗ УСПЕШНО ОТПРАВЛЕН!**\n\n"
            f"📝 {data['from_city']} → {data['to_city']}\n"
            f"⏰ {data['time']}\n"
            f"📞 {data['phone']}\n\n"
            f"🚕 **Диспетчер свяжется с вами!**\n\n"
            f"Для нового заказа нажмите '🚕 Новый заказ'",
            reply_markup=get_main_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Ошибка отправки: {e}")
        await message.answer(
            f"❌ **Ошибка при отправке заказа**\n\n"
            f"Попробуйте позже",
            reply_markup=get_main_keyboard()
        )
        await state.clear()

# ========== ЗАПУСК БОТА ==========
async def main():
    print("=" * 50)
    print("🤖 TELEGRAM ТАКСИ БОТ")
    print("=" * 50)
    print("✅ Бот запущен и готов к работе!")
    print("=" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
