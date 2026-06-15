import random
import json
import asyncio
import logging
import sys
import os

from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


dp = Dispatcher()

with open("data/surprise.json", "r", encoding="utf-8") as f:
    SURPRISE_DATA = json.load(f)


async def send_products(message: Message, filename: str):
    path = f"data/{filename}"

    if not os.path.exists(path):
        await message.answer("Файл не найден.")
        return

    with open(path, "r", encoding="utf-8") as f:
        products = json.load(f)

    text = ""

    for i, product in enumerate(products, start=1):
        text += (
            f"{i}. {product['name']}\n"
            f"Цена: {product['price']:,} сум\n\n"
        )

    await message.answer(text)


async def send_photo(message: Message, path: str, caption: str):
    if not os.path.isfile(path):
        await message.answer(f"Файл не найден:\n{path}")
        return

    await message.answer_photo(
        photo=FSInputFile(path),
        caption=caption
    )


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🛍️ Каталог"),
            KeyboardButton(text="ℹ️ О нас"),
            KeyboardButton(text="🧑‍💻 Поддержка"),
        ],
        [
            KeyboardButton(text="☕ дать мне на кофе или энергетик"),
        ]
    ],
    resize_keyboard=True
)


async def cmd_start(message: Message):
    photo_path = "images/main/start.png"

    caption_text = (
        "Привет! Добро пожаловать в официальный мерч-шоп ofi_piko ✨\n\n"
        "Здесь собрано всё самое уютное и эксклюзивное. Помогу тебе выбрать крутой дроп и быстро оформить заказ.\n\n"
        "Нажимай на кнопки меню, чтобы начать шопинг! 👇"
    )

    if not os.path.isfile(photo_path):
        await message.answer(
            caption_text,
            reply_markup=main_menu
        )
        return

    await message.answer_photo(
        photo=FSInputFile(photo_path),
        caption=caption_text,
        reply_markup=main_menu
    )



@dp.message(F.text == "☕ дать мне на кофе")
async def coffee(message: Message):
    photo_path = "images/main/coffe.png"
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="☕ Перейти к покупке мне на кофе или энергетик",
                    url="https://www.donationalerts.com/r/ofi_piko"
                )
            ]
        ]
    )
    
    if photo_path not in image_cache:
        image_cache[photo_path] = FSInputFile(photo_path)
    
    await message.answer_photo(
        photo=image_cache[photo_path],
        caption="Спасибо за поддержку ❤️",
        reply_markup=kb
    )

#-----------------------------------------------------------------

@dp.message(Command("clothes"))
async def clothes(message: Message):
    await send_products(message, "clothes.json")


@dp.message(Command("accessories"))
async def accessories(message: Message):
    await send_products(message, "accessories.json")


@dp.message(Command("fan"))
async def fan(message: Message):
    await send_products(message, "fan.json")


@dp.message(Command("merch"))
async def merch(message: Message):
    await send_products(message, "merch.json")


@dp.message(Command("posters"))
async def posters(message: Message):
    await send_products(message, "posters.json")


@dp.message(Command("all"))
async def allgets(message: Message):
    await send_products(message, "all.json")


@dp.message(Command("gadgets"))
async def gadgets(message: Message):
    await send_products(message, "gadgets.json")

@dp.message(Command("surprise"))
async def gadgets(message: Message):
    await message.answer("функция не добавленна ещё")



#-----------------------------------------------------------------





@dp.message(Command("start"))
async def cmd_start(message: Message):
    photo_path = "images/main/start.png"

    caption_text = (
        "Привет! Добро пожаловать в официальный мерч-шоп ofi_piko ✨\n\n"
        "Здесь собрано всё самое уютное и эксклюзивное. Помогу тебе выбрать крутой дроп и быстро оформить заказ.\n\n"
        "Нажимай на кнопки меню, чтобы начать шопинг! 👇"
    )

    if not os.path.isfile(photo_path):
        await message.answer(
            caption_text,
            reply_markup=main_menu
        )
        return

    await message.answer_photo(
        photo=FSInputFile(photo_path),
        caption=caption_text,
        reply_markup=main_menu
    )


@dp.message(Command("catalog"))
async def cmd_catalog(message: Message):
    await send_photo(
        message,
        "images/main/caterygory.png",
        "Привет! Это каталог."
    )


@dp.message(F.text == "🛍️ Каталог")
async def catalog_button(message: Message):
    await send_photo(
        message,
        "images/main/caterygory.png",
        """
🛍️ Каталог OFI-SHOP

👕 Одежда
/clothes

🧢 Аксессуары
/accessories

⭐ Фанатские товары
/fan

🎎 Фигурки и мерч
/merch

🖼️ Постеры и принты
/posters

📱 Гаджеты
/gadgets

🎁 Всё подряд
/all

❓ Сюрпризы
/surprise
        """
    )


@dp.message(F.text == "ℹ️ О нас")
async def about_us(message: Message):
    text = (
        "👋 Добро пожаловать в ofi_shop!\n\n"
        "Мы создаём уникальный мерч, аксессуары, товары для фанатов, "
        "аксессуары для телефонов и коллекционные вещи.\n\n"
        "🔥 Почему выбирают нас:\n"
        "🧵 Качественные материалы и пошив.\n"
        "🎨 Вышивка вместо обычных принтов.\n"
        "📦 Доставка по всему миру.\n"
        "👕 Полная кастомизация под ваш стиль.\n\n"
        "🌟 Особая услуга:\n"
        "Не нашли нужную вещь? Мы можем воссоздать образ любимого персонажа "
        "или героя и адаптировать его под ваши размеры и пожелания.\n\n"
        "Выберите действие ниже 👇"
    )

    await message.answer(text)


@dp.message(F.text == "🧑‍💻 Поддержка")
async def support(message: Message):
    text = (
        "🧑‍💻 Поддержка ofi_shop\n\n"
        "Есть вопрос по заказу, доставке, размеру или кастомизации?\n\n"
        "💬 Telegram: @ofi_piko\n"
        "📧 Email: ofipiko@gmail.com\n\n"
        "⏰ Рабочее время:\n"
        "10:00 - 01:00 (UTC+5)"
    )

    await message.answer(text)


async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    asyncio.run(main())