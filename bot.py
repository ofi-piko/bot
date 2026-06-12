import json
import asyncio
import logging
import sys
import os
import re
from time import time

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

TOKEN = "8935821147:AAHwYio_ZEW4MwFj_pGpl_1XVZ_7GffG8OU"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Caching for data.json to avoid repeated file reads
_DATA_CACHE = {"mtime": 0, "data": None}


def load_data():
    global _DATA_CACHE
    path = os.path.join(os.path.dirname(__file__), "data.json")
    try:
        mtime = os.path.getmtime(path)
    except Exception:
        mtime = 0

    if _DATA_CACHE["data"] is None or mtime > _DATA_CACHE["mtime"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                _DATA_CACHE["data"] = json.load(f)
                _DATA_CACHE["mtime"] = mtime
        except Exception:
            _DATA_CACHE["data"] = {}
            _DATA_CACHE["mtime"] = mtime

    return _DATA_CACHE["data"]


# Image index to avoid repeated os.walk calls
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
ALLOWED_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_IMG_INDEX = None


def build_image_index():
    """Build a simple in-memory index: list of (path, lowername)."""
    global _IMG_INDEX
    entries = []
    for root, _, filenames in os.walk(IMAGES_DIR):
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in ALLOWED_EXTS:
                continue
            path = os.path.join(root, fn)
            # use relative path from IMAGES_DIR for matching
            rel = os.path.relpath(path, IMAGES_DIR)
            entries.append((path, rel.replace("\\", "/").lower()))
    _IMG_INDEX = entries


def ensure_image_index():
    global _IMG_INDEX
    if _IMG_INDEX is None:
        build_image_index()


def find_image_for(category, character, style=None):
    ensure_image_index()
    cat_token = str(category).lower()
    char_token = str(character).lower()
    style_token = str(style).lower() if style else None

    best = None
    for path, lname in _IMG_INDEX:
        if cat_token in lname and char_token in lname:
            if style_token and style_token in lname:
                return path
            if best is None:
                best = path

    if best:
        return best

    for path, lname in _IMG_INDEX:
        if char_token in lname:
            return path

    for path, lname in _IMG_INDEX:
        if cat_token in lname:
            return path

    for path, lname in _IMG_INDEX:
        if "default" in lname:
            return path

    return None


def list_styles_for(category, character):
    """Scan images folder and return list of style tokens available for this character.

    Returns list of style strings (e.g. 'school', 'work', 'street', 'default').
    """
    ensure_image_index()
    cat_token = str(category).lower()
    char_token = str(character).lower()

    styles = []
    for _, lname in _IMG_INDEX:
        if cat_token in lname and char_token in lname:
            s = os.path.splitext(lname)[0]
            s = s.replace(cat_token, "")
            s = s.replace(char_token, "")
            for ch in ["_", "-", " ", ".", "/"]:
                s = s.replace(ch, " ")
            s = s.strip()
            if not s:
                style = "default"
            else:
                tokens = [tok for tok in s.split() if tok]
                style = tokens[-1] if tokens else "default"
            if style not in styles:
                styles.append(style)

    return styles


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! OFI Shop активен.\n" \
        "Используй /menu для навигации или /catalog для входа в каталог."
    )


@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Каталог", callback_data="catalog_button")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help:menu")]
    ])
    await message.answer("Меню OFI Shop:", reply_markup=keyboard)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "/menu — главное меню\n"
        "/catalog — открыть каталог\n"
        "Выбирай персонажа, затем стиль и выбирай, что купить.\n"
        "После выбора заказа бот выдаст QR-код суммы."
    )


@dp.message(Command("catalog"))
async def cmd_catalog(message: Message):
    data = load_data()
    keyboard = [
        [InlineKeyboardButton(text=cat, callback_data=f"cat:{cat}")]
        for cat in data.keys()
    ]
    # Add a help/close row
    keyboard.append([
        InlineKeyboardButton(text="❓ Помощь", callback_data="help:catalog"),
        InlineKeyboardButton(text="✖️ Закрыть", callback_data="close:catalog")
    ])

    await message.answer(
        "📦 Выбери категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@dp.callback_query(F.data == "catalog_button")
async def catalog_button(call: CallbackQuery):
    await call.answer()
    await cmd_catalog(call.message)


@dp.callback_query(F.data.startswith("cat:"))
async def open_category(call: CallbackQuery):
    category = call.data.split(":")[1]
    data = load_data()

    await call.answer()

    category_data = data.get(category)

    # Detect whether this category maps to characters (dict of dicts)
    is_characters = False
    if isinstance(category_data, dict):
        # If all values are dicts (character -> sections), treat as characters
        if all(isinstance(v, dict) for v in category_data.values()):
            is_characters = True

    if is_characters:
        keyboard = [
            [InlineKeyboardButton(text=char, callback_data=f"char:{category}:{char}")]
            for char in category_data.keys()
        ]
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back:catalog")])

        await call.message.edit_text(
            f"🎭 {category}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        # Category directly contains sections/items — show items list
        text = f"🎭 {category}\n"
        for section, goods in (category_data or {}).items():
            text += f"\n📁 {section.upper()}\n"
            for item in goods:
                text += f"• {item.get('name')} — {item.get('price')}\n"

        keyboard = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="back:catalog")]]

        # Try to edit original message; fallback to new message if edit fails
        try:
            await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        except Exception:
            await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))


@dp.callback_query(F.data.startswith("char:"))
async def open_character(call: CallbackQuery):
    _, category, character = call.data.split(":")
    data = load_data()

    # Build text description for the character
    items = data.get(category, {}).get(character, {})

    text = f"👤 {character}\n\n"
    for section, goods in items.items():
        text += f"\n📁 {section.upper()}\n"
        for item in goods:
            text += f"• {item.get('name')} — {item.get('price')}\n"

    await call.answer()

    # Find available styles from image filenames
    styles = list_styles_for(category, character)

    if not styles:
        # No style options: show default immediately
        img_path = find_image_for(category, character)
        buttons = [
            [InlineKeyboardButton(text="⬅️ Назад к персонажам", callback_data=f"cat:{category}")],
            [InlineKeyboardButton(text="🏠 В каталог", callback_data="back:catalog")]
        ]

        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as f:
                await call.message.answer_photo(
                    photo=f,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
        else:
            await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
        return

    # Build keyboard of styles
    STYLE_LABELS = {"school": "Школьный", "work": "Рабочий", "street": "Уличный", "default": "Обычный"}
    kb = []
    for s in styles:
        kb.append([
            InlineKeyboardButton(
                text=STYLE_LABELS.get(s, s.capitalize()),
                callback_data=f"style:{category}:{character}:{s}"
            )
        ])

    kb.append([InlineKeyboardButton(text="⬅️ Назад к персонажам", callback_data=f"cat:{category}")])

    img_path = find_image_for(category, character)
    if img_path and os.path.exists(img_path):
        try:
            with open(img_path, "rb") as f:
                await call.message.answer_photo(
                    photo=f,
                    caption=text + "\nВыбери стиль внешнего вида:",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
                )
            return
        except Exception:
            pass

    # Fallback text with buttons
    try:
        await call.message.edit_text(text + "\nВыбери стиль внешнего вида:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    except Exception:
        await call.message.answer(text + "\nВыбери стиль внешнего вида:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@dp.callback_query(F.data == "back:catalog")
async def back_to_catalog(call: CallbackQuery):
    await call.answer()
    await cmd_catalog(call.message)


@dp.callback_query(F.data == "close:catalog")
async def close_catalog(call: CallbackQuery):
    await call.answer("Закрыто.")
    try:
        await call.message.delete()
    except Exception:
        pass


@dp.callback_query(F.data.startswith("help:"))
async def help_callback(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        "/menu — главное меню\n"
        "/catalog — открыть каталог\n"
        "Выбирай персонажа, затем стиль и что купить.\n"
        "После заказа бот выдаст QR к оплате."
    )


PRICE_RE = re.compile(r"\d+[\.,]?\d*")


def extract_price_value(price_text):
    if not price_text:
        return None
    normalized = price_text.replace("$", "").replace("₽", "").replace("USD", "").replace("EUR", "")
    normalized = normalized.replace("–", "-").replace("—", "-")
    parts = PRICE_RE.findall(normalized)
    if not parts:
        return None
    values = []
    for part in parts:
        try:
            values.append(float(part.replace(",", ".")))
        except ValueError:
            continue
    if not values:
        return None
    if "-" in normalized:
        return sum(values) / len(values)
    return values[0]


def calculate_section_amount(items, section):
    section_items = items.get(section, [])
    total = 0.0
    count = 0
    for item in section_items:
        price = extract_price_value(item.get("price", ""))
        if price is not None:
            total += price
            count += 1
    return total if count else None


def calculate_total_amount(items):
    total = 0.0
    count = 0
    for section_items in items.values():
        for item in section_items:
            price = extract_price_value(item.get("price", ""))
            if price is not None:
                total += price
                count += 1
    return total if count else None


def make_payment_payload(amount):
    return f"https://pay.example.com/checkout?amount={amount:.2f}"


def generate_qr_image(data, path):
    try:
        import qrcode
    except ImportError:
        return False
    qr = qrcode.QRCode(border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(path)
    return True


@dp.callback_query(F.data.startswith("style:"))
async def show_style(call: CallbackQuery):
    # style:<category>:<character>:<style>
    parts = call.data.split(":")
    if len(parts) < 4:
        await call.answer()
        return

    _, category, character, style = parts
    data = load_data()

    items = data.get(category, {}).get(character, {})

    text = f"👤 {character} — {style.capitalize()}\n\n"
    for section, goods in items.items():
        text += f"\n📁 {section.upper()}\n"
        for item in goods:
            text += f"• {item.get('name')} — {item.get('price')}\n"

    await call.answer()

    # Try to find an image matching category + character + style
    found = find_image_for(category, character, style)

    if not found:
        # fallback to any image for character
        found = find_image_for(category, character)

    buttons = [
        [InlineKeyboardButton(text="👖 Штаны", callback_data=f"order:{category}:{character}:{style}:bottoms")],
        [InlineKeyboardButton(text="💍 Украшение", callback_data=f"order:{category}:{character}:{style}:accessories")],
        [InlineKeyboardButton(text="🛍️ Купить всё", callback_data=f"order:{category}:{character}:{style}:all")],
        [InlineKeyboardButton(text="⬅️ Назад к стилям", callback_data=f"char:{category}:{character}")],
        [InlineKeyboardButton(text="🏠 В каталог", callback_data="back:catalog")]
    ]

    if found and os.path.exists(found):
        with open(found, "rb") as f:
            await call.message.answer_photo(photo=f, caption=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    else:
        await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@dp.callback_query(F.data.startswith("order:"))
async def order_item(call: CallbackQuery):
    parts = call.data.split(":")
    if len(parts) != 5:
        await call.answer()
        return

    _, category, character, style, section = parts
    data = load_data()
    items = data.get(category, {}).get(character, {})

    if section == "all":
        amount = calculate_total_amount(items)
        label = "всё"
    else:
        amount = calculate_section_amount(items, section)
        label = section

    if amount is None:
        amount = 100.0

    amount = round(amount, 2)
    payload = make_payment_payload(amount)
    qr_path = os.path.join(os.path.dirname(__file__), "tmp_qr.png")
    qr_created = generate_qr_image(payload, qr_path)

    caption = (
        f"Заказ: {character} — {style.capitalize()} — {label}\n"
        f"Сумма: {amount:.2f}$\n"
        "Сканируй QR для оплаты."
    )

    await call.answer()
    if qr_created and os.path.exists(qr_path):
        with open(qr_path, "rb") as f:
            await call.message.answer_photo(photo=f, caption=caption)
        try:
            os.remove(qr_path)
        except Exception:
            pass
    else:
        await call.message.answer(caption + f"\nПлатёжная ссылка: {payload}")


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


@dp.message(Command("refresh_cache"))
async def cmd_refresh_cache(message: Message):
    """Dev command to rebuild caches without restarting the bot."""
    build_image_index()
    # clear data cache so next load reads file
    global _DATA_CACHE
    _DATA_CACHE["data"] = None
    await message.answer("Кеши обновлены.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    asyncio.run(main())