from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from config import PROVIDER_TOKEN
from config import SPEAKERS
from models.silero_tts import synthesize_speech
from utils.normalizer import normalize_numbers
from services.analytics import increment_tts
from services.analytics import increment_purchase
from services.user_limits import (
    get_left, get_user_limit, get_next_free_reset,
    add_used, can_speak, can_request, set_last_request, seconds_to_wait, add_purchased
)


router = Router()
user_speakers = {}

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Озвучить текст")],
            [KeyboardButton(text="Мой баланс"), KeyboardButton(text="Купить озвучки")],
            [KeyboardButton(text="Помощь"), KeyboardButton(text="Другие нейросети")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие ↓"
    )

@router.message(Command("start"))
async def start(message: Message):
    about_text = (
        "🤖 <b>Привет! Я голосовой бот, который озвучит любой твой текст разными голосами.</b>\n\n"
        "Озвучивает ваш текст с помощью нейросетей!\n"
        "1. Сначала выберите голос ('Озвучить текст')\n"
        "2. Затем отправьте текст (до 500 символов)\n"
        "3. Получите аудиофайл\n\n"
        "Вам доступно <b>20 бесплатных озвучек</b>! Бесплатные озвучки восстанавливаются раз в неделю.\n"
        "Можно купить ещё озвучки ('Купить озвучки')\n\n"
        "Статистика по вашим озвучкам ('Мой баланс')"

    )
    await message.answer(
        about_text,
        reply_markup=get_main_menu(),
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "Озвучить текст")
async def handle_tts(message: Message):
    kb = InlineKeyboardBuilder()
    for v in SPEAKERS:
        kb.button(text=v.capitalize(), callback_data=f"voice_{v}")
    kb.adjust(2)
    await message.answer("Отправляйте текст боту только на русском языке. Текст на других языках бот игнорирует.\n"
                         "Что бы изменить ударение, поставьте '+' перед нужной гласной.\n\n"
                         "Выберите голос для озвучивания:",
                         reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("voice_"))
async def set_voice(callback: CallbackQuery):
    user_id = callback.from_user.id
    speaker = callback.data.replace("voice_", "")
    user_speakers[user_id] = speaker
    await callback.message.answer(
        f"✅ Голос <b>{speaker.capitalize()}</b> выбран.\nТеперь пришлите текст для озвучки (до 300 символов).",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@router.message(F.text == "Мой баланс")
async def handle_balance(message: Message):
    user_id = message.from_user.id
    left = get_left(user_id)
    user_data = get_user_limit(user_id)
    total_used = user_data.get("used", 0)
    next_free_date = get_next_free_reset(user_id)
    text = (
        f"🗣 <b>Ваш баланс</b>\n\n"
        f"Озвучек осталось: <b>{left}</b>\n"
        f"Платных озвучек куплено: <b>{user_data.get('purchased', 0)}</b>\n"
        f"Всего озвучек использовано: <b>{total_used}</b>\n"
        f"Следующие бесплатные озвучки будут <b>{next_free_date}</b>."
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "Купить озвучки")
@router.message(Command("buy"))
async def buy_menu(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="10 озвучек — 100₽", callback_data="buy_10_1")
    kb.button(text="30 озвучек — 200₽", callback_data="buy_30_2")
    kb.button(text="50 озвучек — 300₽", callback_data="buy_50_3")
    kb.adjust(1)
    await message.answer("Выберите пакет для покупки:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("buy_"))
async def buy_callback(call: CallbackQuery):
    # Пример: callback_data="buy_10_5"
    _, amount, price = call.data.split("_")
    amount = int(amount)
    price = int(price)

    title = f"{amount} озвучек"
    description = f"Пакет для бота: {amount} озвучек"
    payload = f"tts_pack_{amount}"
    currency = "RUB"
    prices = [LabeledPrice(label=title, amount=price * 10000)]  # amount в копейках (rub * 100)

    await call.message.answer_invoice(
        title=title,
        description=description,
        provider_token=PROVIDER_TOKEN,
        currency=currency,
        prices=prices,
        payload=payload,
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
    )
    await call.answer()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@router.message(F.content_type == "successful_payment")
async def process_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    if payload.startswith("tts_pack_"):
        amount = int(payload.replace("tts_pack_", ""))
        add_purchased(user_id, amount)
        increment_purchase(user_id, amount)
        left = get_left(user_id)
        await message.answer(
            f"✅ Платёж успешен! Вам начислено {amount} озвучек.\n"
            f"Теперь у вас {left} озвучек."
        )

@router.message(F.text == "Помощь")
async def help_handler(message: Message):
    text = (
        "🤖 <b>Помощь по использованию бота</b>\n\n"
        "<b>Возможности:</b>\n"
        "• Озвучивание любого текста выбранным голосом (до 300 символов за раз)\n"
        "• 20 бесплатных озвучек каждую неделю\n"
        "• Возможность покупки дополнительных пакетов озвучек\n\n"
        "<b>Как пользоваться:</b>\n"
        "1. Нажмите кнопку \"Озвучить текст\" и выберите голос\n"
        "2. Отправьте текст (до 300 символов)\n"
        "3. Получите аудиофайл в ответ\n\n"
        "<b>Баланс и покупки:</b>\n"
        "• Узнать остаток озвучек — \"Мой баланс\"\n"
        "• Купить дополнительные озвучки — \"Купить озвучки\"\n\n"
        "<b>Частые вопросы:</b>\n"
        "• <i>Не приходит озвучка?</i> — Проверьте, не превышен ли лимит, и подождите немного, чтобы не попасть под антифлуд\n"
        "• <i>Не проходит оплата?</i> — Попробуйте ещё раз или напишите в поддержку\n\n"
        "<b>Контакты поддержки:</b>\n"
        "@skynet0001\n\n"
        "<b>Приватность:</b>\n"
        "Тексты пользователей не сохраняются и не передаются третьим лицам."
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "Другие нейросети")
async def other_nets(message: Message):
    text = (
        "<b>Другие нейросети и боты:</b>\n\n"
        "🤖 <a href='https://t.me/your_voicebot_en'>Озвучка на английском</a>\n"
        "🎨 <a href='https://t.me/your_imagegen_bot'>Генерация картинок</a>\n"
        "🎧 <a href='https://t.me/your_musicbot'>Генерация музыки</a>\n"
        "💬 <a href='https://t.me/your_chatbot'>AI-чат</a>\n"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@router.message()
async def tts_message(message: Message):
    user_id = message.from_user.id

    if not can_request(user_id):
        sec = seconds_to_wait(user_id)
        await message.answer(f"⏳ Подождите {sec} сек. перед следующей озвучкой.")
        return

    speaker = user_speakers.get(user_id)
    if not speaker:
        await message.answer("Сначала выберите голос через кнопку 'Озвучить текст'.")
        return
    text = message.text.strip()
    if not text:
        await message.answer("Пожалуйста, отправьте текст для озвучки.")
        return
    if len(text) > 500:
        await message.answer("⚠️ Текст слишком длинный! Максимум 300 символов.")
        return
    if not can_speak(user_id):
        await message.answer("У вас закончились бесплатные и купленные озвучки.\nПополните баланс через 'Купить озвучки'.")
        return

    set_last_request(user_id)
    await message.answer(f"⏳ Генерирую озвучку голосом <b>{speaker.capitalize()}</b>...", parse_mode=ParseMode.HTML)
    try:
        normalized_text = normalize_numbers(text)
        audio_path = await synthesize_speech(normalized_text, speaker, user_id)
        add_used(user_id)
        increment_tts(user_id)
        await message.answer_audio(FSInputFile(audio_path), title=f"Голос: {speaker.capitalize()}")
        import os
        os.remove(audio_path)
    except Exception as e:
        await message.answer("Ошибка при генерации или отправке аудиофайла.")
        print("TTS error:", e)

