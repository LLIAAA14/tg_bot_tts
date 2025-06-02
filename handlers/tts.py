from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import SPEAKERS, PROVIDER_TOKEN
from services.user_state import user_speakers
from models.silero_tts import synthesize_speech
from utils.normalizer import normalize_numbers
from services.user_limits import can_speak, add_used, get_left, add_purchased

router = Router()

@router.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardBuilder()
    for v in SPEAKERS:
        kb.button(text=v.capitalize(), callback_data=f"voice_{v}")
    kb.adjust(2)
    about_text = (
        "🤖 <b>Голосовой бот Silero</b>\n"
        "Озвучивает ваш текст с помощью нейросетей!\n"
        "1. Сначала выберите голос\n"
        "2. Затем отправьте текст (до 300 символов)\n"
        "3. Получите аудиофайл\n\n"
        "Вам доступно <b>20 бесплатных озвучек</b>! После — можно купить ещё пакеты:\n"
        "10 озвучек — 5₽\n20 озвучек — 10₽\n\n"
        "Посмотреть остаток: /my\nКупить пакет: /buy\n\n"
        "<i>Бот автоматически превращает числа в слова, чтобы они озвучивались правильно.</i>"
    )
    await message.answer(
        about_text,
        reply_markup=kb.as_markup(),
        parse_mode=ParseMode.HTML
    )

@router.message(Command("my"))
async def my_limit(message: Message):
    left = get_left(message.from_user.id)
    await message.answer(f"У вас осталось {left} озвучек.")

@router.message(Command("buy"))
async def buy_menu(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="10 озвучек — 5₽", callback_data="buy_10_5")
    kb.button(text="20 озвучек — 10₽", callback_data="buy_20_10")
    kb.adjust(1)
    await message.answer("Выберите пакет для покупки:", reply_markup=kb.as_markup())

@router.callback_query(F.data.startswith("buy_"))
async def buy_callback(call: CallbackQuery):
    # Пример: callback_data="buy_10_5"
    _, amount, price = call.data.split("_")
    amount = int(amount)  # Количество озвучек
    price = int(price)    # Цена пакета в рублях

    provider_token = PROVIDER_TOKEN
    title = f"{amount} озвучек"
    description = f"Пакет для бота: {amount} озвучек"
    payload = f"tts_pack_{amount}"
    currency = "RUB"
    prices = [LabeledPrice(label=title, amount=price * 10000)]  # Сумма в копейках!

    await call.message.answer_invoice(
        title=title,
        description=description,
        provider_token=provider_token,
        currency=currency,
        prices=prices,
        payload=payload
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
        left = get_left(user_id)
        await message.answer(
            f"✅ Платёж успешен! Вам начислено {amount} озвучек.\n"
            f"Теперь у вас {left} озвучек."
        )

@router.callback_query(F.data.startswith("voice_"))
async def set_voice(callback: CallbackQuery):
    user_id = callback.from_user.id
    speaker = callback.data.replace("voice_", "")
    if speaker not in SPEAKERS:
        await callback.answer("Ошибка выбора!", show_alert=True)
        return
    user_speakers[user_id] = speaker
    await callback.message.answer(
        f"✅ Голос <b>{speaker.capitalize()}</b> выбран.\n\nТеперь пришлите текст (до 300 символов) для озвучки.",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@router.message()
async def tts_message(message: Message):
    user_id = message.from_user.id
    speaker = user_speakers.get(user_id)
    if not speaker:
        kb = InlineKeyboardBuilder()
        for v in SPEAKERS:
            kb.button(text=v.capitalize(), callback_data=f"voice_{v}")
        kb.adjust(2)
        await message.answer(
            "Пожалуйста, сначала выберите голос для озвучки:",
            reply_markup=kb.as_markup()
        )
        return

    text = message.text.strip()
    if not text:
        return
    if len(text) > 300:
        await message.answer("⚠️ Текст слишком длинный! Максимум 300 символов.")
        return

    if not can_speak(user_id):
        await message.answer(
            "🚫 У вас закончились бесплатные озвучки!\n"
            "Купите пакет командой /buy"
        )
        return

    normalized_text = normalize_numbers(text)

    await message.answer(
        f"⏳ Генерирую аудио голосом <b>{speaker.capitalize()}</b>, подождите...",
        parse_mode=ParseMode.HTML
    )
    try:
        audio_path = await synthesize_speech(normalized_text, speaker, user_id)
        from aiogram.types import FSInputFile
        await message.answer_audio(FSInputFile(audio_path), title=f"Голос: {speaker.capitalize()}")
        import os
        os.remove(audio_path)
        add_used(user_id)
        left = get_left(user_id)
        await message.answer(f"Осталось озвучек: {left}")
    except Exception as e:
        await message.answer(f"🚫 Ошибка генерации аудио: {e}")