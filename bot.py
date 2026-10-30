import asyncio, os, tempfile

import edge_tts
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (CallbackQuery, FSInputFile, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message)
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN", "")
VOICES = {"madina": "uz-UZ-MadinaNeural", "sardor": "uz-UZ-SardorNeural"}
MAX_CHARS = 4000

bot = Bot(TOKEN)
dp = Dispatcher()
choice = {}  # user_id -> "madina" | "sardor"


def voice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👩 Madina", callback_data="v:madina"),
        InlineKeyboardButton(text="👨 Sardor", callback_data="v:sardor"),
    ]])


@dp.message(Command("start"))
async def start(m: Message):
    await m.answer(
        "Salom! 🎙 Menga istalgan matnni yozing, men uni ovozga aylantirib beraman.\n\n"
        "Ovozni tanlash: /ovoz"
    )


@dp.message(Command("ovoz"))
async def pick_voice(m: Message):
    await m.answer("Ovozni tanlang:", reply_markup=voice_kb())


@dp.callback_query(F.data.startswith("v:"))
async def picked(c: CallbackQuery):
    key = c.data[2:]
    if key in VOICES:
        choice[c.from_user.id] = key
        await c.message.edit_text(f"✅ Tanlandi: {key.capitalize()}. Endi matn yozing.")
    await c.answer()


@dp.message(F.text & ~F.text.startswith("/"))
async def to_speech(m: Message):
    text = m.text.strip()
    if len(text) > MAX_CHARS:
        await m.answer(f"Matn uzun. {MAX_CHARS} belgigacha yuboring.")
        return
    voice = VOICES[choice.get(m.from_user.id, "madina")]
    await bot.send_chat_action(m.chat.id, "record_voice")
    path = os.path.join(tempfile.gettempdir(), f"{m.chat.id}_{m.message_id}.mp3")
    try:
        await edge_tts.Communicate(text, voice).save(path)
        await m.answer_voice(FSInputFile(path))
    except Exception:
        await m.answer("❌ Ovozga aylantirib bo'lmadi. Birozdan keyin qayta urinib ko'ring.")
    finally:
        if os.path.exists(path):
            os.remove(path)


async def ping(request):
    return web.Response(text="ok")


async def main():
    app = web.Application()
    app.add_routes([web.get("/", ping)])
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.getenv("PORT", "8080"))).start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
