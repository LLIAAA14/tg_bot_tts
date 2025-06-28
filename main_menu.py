from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
from config import PROVIDER_TOKEN, SPEAKERS
from models.silero_tts import synthesize_speech
from utils.normalizer import normalize_numbers
from services.analytics_db import (
    get_stats, increment_tts, increment_purchase, register_user
)
from services.user_limits_db import (
    get_left, get_user_limit,
    add_used, can_speak, can_request, set_last_request, seconds_to_wait, add_purchased
)

router = Router()
user_speakers = {}
user_languages = {}

speaker_names = {
    # RU
    "aidar": "👨Михаил",
    "baya": "👱‍♀️Ольга",
    "kseniya": "👱‍♀️Ксения",
    "xenia": "👱‍♀️Алла",
    "eugene": "👨Евгений",
    # EN
    "en_0": "👱‍♀️Сьюзен",
    "en_1": "👨Бил",
    "en_2": "👨Дэвид",
    "en_3": "👱‍♀️Эшли",
    "en_4": "👱‍♀️Мэг",
    # DE
    "bernd_ungerer": "👨Бернд",
    "eva_k": "👱‍♀️Ева",
    "friedrich": "👨Фридрих",
    "hokuspokus": "👱‍♀️Ханна",
    "karlsson": "👨Карлссон",
    # FR
    "fr_0": "👨Филипп",
    "fr_1": "👨Патрик",
    "fr_2": "👨Даниэль",
    "fr_3": "👨Алан",
    "fr_4": "👱‍♀️Анет",
    "fr_5": "👱‍♀️Вивьен",
    # ES
    "es_0": "👨Луис",
    "es_1": "👨Диего",
    "es_2": "👨Педро"
}

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🗣 Озвучить текст")],
            [KeyboardButton(text="💼 Мой баланс"), KeyboardButton(text="💰 Купить озвучки")],
            [KeyboardButton(text="🆘 Помощь"), KeyboardButton(text="📃 Другие нейросети")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие ↓"
    )

@router.message(Command("start"))
async def start(message: Message):
    user_name = message.from_user.first_name or ""
    about_text = (
        f"🤖 <b>Привет, {user_name}!\n\n"
        "Я — твой голосовой помощник. Озвучу любой твой текст разными голосами и на разных языках — быстро и качественно!</b>\n\n"
        "Как пользоваться ботом:\n"
        "1️⃣ Сначала выберите язык и голос (Озвучить текст)\n"
        "2️⃣ Затем отправьте текст (до 500 символов)\n"
        "3️⃣ Получите аудиофайл\n\n"
        "Вам доступно <b>30 бесплатных озвучек</b>!\n"
        "Можно купить ещё озвучки (Купить озвучки)\n\n"
        "Статистика по вашим озвучкам (Мой баланс)"
    )
    await message.answer(
        about_text,
        reply_markup=get_main_menu(),
        parse_mode=ParseMode.HTML
    )

@router.message(F.text == "🗣 Озвучить текст")
async def handle_tts(message: Message):
    # Показываем выбор языка - все поддерживаемые языки Silero TTS
    kb = InlineKeyboardBuilder()
    kb.button(text="Русский 🇷🇺", callback_data="lang_ru")
    kb.button(text="Английский 🇬🇧", callback_data="lang_en")
    kb.button(text="Немецкий 🇩🇪", callback_data="lang_de")
    kb.button(text="Французский 🇫🇷", callback_data="lang_fr")
    kb.button(text="Испанский 🇪🇸", callback_data="lang_es")
    kb.adjust(2)
    await message.answer(
        "Выберите язык для озвучки:",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data.startswith("lang_"))
async def handle_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.replace("lang_", "")
    user_languages[user_id] = lang

    kb = InlineKeyboardBuilder()
    speakers = SPEAKERS.get(lang, [])
    for v in speakers:
        kb.button(text=speaker_names.get(v, v.capitalize()), callback_data=f"voice_{v}")
    kb.adjust(2)
    lang_map = {
        "ru": "русском", "en": "английском", "de": "немецком", "fr": "французском",
        "es": "испанском"
    }
    lang_label = {
        "ru": "Русский", "en": "Английский", "de": "Немецкий", "fr": "Французский",
        "es": "Испанский"
    }
    await callback.message.answer(
        f"Вы выбрали <b>{lang_label.get(lang, lang.capitalize())}</b> язык.\n\n"
        "Присылайте боту текст только на соответствующем языке. Текст на других языках бот игнорирует.\n\n"
        "Для изменения ударения добавьте '+' перед гласной.\n"
        "Для добавления паузы '.-'.\n\n"
        f"Теперь выберите голос для озвучивания на {lang_map.get(lang, lang)} языке:",
        parse_mode=ParseMode.HTML,
        reply_markup=kb.as_markup()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("voice_"))
async def set_voice(callback: CallbackQuery):
    user_id = callback.from_user.id
    speaker = callback.data.replace("voice_", "")
    user_speakers[user_id] = speaker
    lang = user_languages.get(user_id, "ru")
    lang_label = {
        "ru": "Русский", "en": "Английский", "de": "Немецкий", "fr": "Французский",
        "es": "Испанский"
    }
    speaker_display = speaker_names.get(speaker, speaker.capitalize())
    await callback.message.answer(
        f"✅ Голос <b>{speaker_display}</b> выбран ({lang_label.get(lang, lang.capitalize())}).\nТеперь пришлите текст для озвучки (до 500 символов).",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@router.message(F.text == "💼 Мой баланс")
async def handle_balance(message: Message):
    user_id = message.from_user.id
    left = get_left(user_id)
    user_data = get_user_limit(user_id)
    total_used = user_data.get("used", 0)
    text = (
        f"🗣 <b>Ваш баланс</b>\n\n"
        f"Озвучек осталось: <b>{left}</b>\n"
        f"Платных озвучек куплено: <b>{user_data.get('purchased', 0)}</b>\n"
        f"Всего озвучек использовано: <b>{total_used}</b>\n"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "💰 Купить озвучки")
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
    _, amount, price = call.data.split("_")
    amount = int(amount)
    price = int(price)

    title = f"{amount} озвучек"
    description = f"Пакет для бота: {amount} озвучек"
    payload = f"tts_pack_{amount}"
    currency = "RUB"
    prices = [LabeledPrice(label=title, amount=price * 10000)]

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

@router.message(F.text == "🆘 Помощь")
async def help_handler(message: Message):
    text = (
        "🤖 <b>Помощь по использованию бота</b>\n\n"
        "<b>Возможности:</b>\n"
        "• Озвучивание любого текста выбранным языком и голосом (до 500 символов за раз)\n"
        "• 30 бесплатных озвучек\n"
        "• Возможность покупки дополнительных пакетов озвучек\n\n"
        "<b>Как пользоваться:</b>\n"
        "1. Нажмите кнопку \"Озвучить текст\", выберите язык и голос\n"
        "2. Отправьте текст (до 500 символов)\n"
        "3. Получите аудиофайл в ответ\n\n"
        "<b>Баланс и покупки:</b>\n"
        "• Узнать остаток озвучек — \"Мой баланс\"\n"
        "• Купить дополнительные озвучки — \"Купить озвучки\"\n\n"
        "<b>Перезагрузить бота:</b>\n"
        "•/start\n\n"
        "<b>Частые вопросы:</b>\n"
        "• <i>Не приходит озвучка?</i> — Проверьте, не превышен ли лимит, и подождите немного, чтобы не попасть под антифлуд\n"
        "• <i>Не проходит оплата?</i> — Попробуйте ещё раз или напишите в поддержку\n\n"
        "<b>Контакты поддержки:</b>\n"
        "@skynet0001\n\n"
        "<b>Приватность:</b>\n"
        "Тексты пользователей не сохраняются и не передаются третьим лицам."
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "📃 Другие нейросети")
async def other_nets(message: Message):
    text = (
        "<b>Другие нейросети и боты:</b>\n\n"
        '1️⃣ <a href="https://t.me/text_generation1_bot">Голос в текст</a>'
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
        await message.answer("Сначала выберите язык и голос через кнопку 'Озвучить текст'.")
        return
    text = message.text.strip()
    if not text:
        await message.answer("Пожалуйста, отправьте текст для озвучки.")
        return
    if len(text) > 500:
        await message.answer("⚠️ Текст слишком длинный! Максимум 500 символов.")
        return
    if not can_speak(user_id):
        await message.answer("У вас закончились бесплатные и купленные озвучки.\nПополните баланс через 'Купить озвучки'.")
        return

    set_last_request(user_id)
    lang = user_languages.get(user_id, "ru")
    lang_label = {
        "ru": "Русский", "en": "Английский", "de": "Немецкий", "fr": "Французский",
        "es": "Испанский", "tt": "Татарский", "uz": "Узбекский",
        "ba": "Башкирский", "xal": "Калмыцкий"
    }
    speaker_display = speaker_names.get(speaker, speaker.capitalize())
    await message.answer(f"⏳ Генерирую озвучку голосом <b>{speaker_display}</b> ({lang_label.get(lang, lang.capitalize())})...", parse_mode=ParseMode.HTML)
    try:
        normalized_text = normalize_numbers(text, lang=lang)
        audio_path = await synthesize_speech(normalized_text, speaker, user_id)
        add_used(user_id)
        increment_tts(user_id)
        await message.answer_audio(FSInputFile(audio_path), title=f"Голос: {speaker_display}")
        import os
        os.remove(audio_path)
    except Exception as e:
        await message.answer("Ошибка при генерации или отправке аудиофайла.")
        print("TTS error:", e)
