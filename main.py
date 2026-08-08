import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from yt_dlp import YoutubeDL
from aiohttp import web

TOKEN = "8627549326:AAFSVDJjlehaaLZEvN2v5g0KIxtTjtvrd_zY"
bot = Bot(token=TOKEN)
dp = Dispatcher()

TEXTS = {
    "ru": {
        "welcome": "Салом! Выберите язык / Забонро интихоб кунед:",
        "set_lang": "Язык изменен на русский! Отправьте ссылку на видео.",
        "choose_format": "Выберите формат для скачивания:",
        "processing": "Загружаю файл, подождите...",
        "error": "Произошла ошибка при загрузке. Возможно, файл слишком большой."
    },
    "tg": {
        "welcome": "Салом! Выберите язык / Забонро интихоб кунед:",
        "set_lang": "Забон ба тоҷикӣ тағйир ёфт! Линки видеоро биристед.",
        "choose_format": "Формати боргириро интихоб кунед:",
        "processing": "Файл боргирӣ шуда истодааст, андаке сабр кунед...",
        "error": "Ҳангоми боргирӣ хатогӣ рӯй дод. Шояд файл хеле калон бошад."
    }
}

user_languages = {}
user_links = {}

def get_lang_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇹🇯 Тоҷикӣ", callback_data="lang_tg"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]
    ])

def get_format_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 High Video (Беҳтарин)", callback_data="fmt_high"),
            InlineKeyboardButton(text="📉 Low Video (Миёна)", callback_data="fmt_low")
        ],
        [
            InlineKeyboardButton(text="🎵 MP3 (Танҳо Аудио)", callback_data="fmt_mp3")
        ]
    ])

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(TEXTS["tg"]["welcome"], reply_markup=get_lang_keyboard())

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split("_")[-1]
    user_languages[callback.from_user.id] = lang
    await callback.message.edit_text(TEXTS[lang]["set_lang"])
    await callback.answer()

@dp.message(F.text.contains("http"))
async def handle_links(message: Message):
    user_id = message.from_user.id
    lang = user_languages.get(user_id, "tg")
    user_links[user_id] = message.text.strip()
    await message.answer(TEXTS[lang]["choose_format"], reply_markup=get_format_keyboard())

@dp.callback_query(F.data.startswith("fmt_"))
async def download_file(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = user_languages.get(user_id, "tg")
    url = user_links.get(user_id)
    fmt_type = callback.data.split("_")[-1]
    
    if not url:
        await callback.answer("Линки видео ёфт нашуд. Аз нав биристед.")
        return
        
    status_msg = await callback.message.answer(TEXTS[lang]["processing"])
    await callback.answer()
    
    if fmt_type == "high":
        ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'video_{user_id}.%(ext)s'}
    elif fmt_type == "low":
        ydl_opts = {'format': 'worst[ext=mp4]/worst', 'outtmpl': f'video_{user_id}.%(ext)s'}
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'audio_{user_id}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if fmt_type == "mp3" and not filename.endswith(".mp3"):
                filename = os.path.splitext(filename)[0] + ".mp3"
        
        if os.path.exists(filename):
            if fmt_type == "mp3":
                await callback.message.answer_audio(audio=open(filename, 'rb'))
            else:
                await callback.message.answer_video(video=open(filename, 'rb'))
            os.remove(filename)
            await status_msg.delete()
    except Exception as e:
        print(f"Хатогӣ: {e}")
        await status_msg.edit_text(TEXTS[lang]["error"])

# Веб-сервери хурд барои фиреб додани Render
async def handle_web(request):
    return web.Response(text="Bot is running!")

async def start_web():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await start_web()  # Сар кардани веб-сервер
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
