import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

TOKEN = "8667354291:AAGk9cAoCPyDi7rV0TwrakE1lCCJNiD-aGw"
bot = Bot(token=TOKEN)
dp = Dispatcher()

TEXTS = {
    "ru": {
        "welcome": "Салом! Выберите язык / Забонро интихоб кунед:",
        "set_lang": "Язык изменен на русский! Отправьте ссылку на видео.",
        "choose_format": "Выберите формат для скачивания:",
        "processing": "Загружаю файл, подождите...",
        "error": "Произошла ошибка при загрузке. Возможно, линк неверный или файл слишком большой."
    },
    "tg": {
        "welcome": "Салом! Выберите язык / Забонро интихоб кунед:",
        "set_lang": "Забон ба тоҷикӣ тағйир ёфт! Линки видеоро биристед.",
        "choose_format": "Формати боргириро интихоб кунед:",
        "processing": "Файл боргирӣ шуда истодааст, андаке сабр кунед...",
        "error": "Ҳангоми боргирӣ хатогӣ рӯй дод. Шояд линк хато бошад ё файл хеле калон аст."
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
    
    # Истифодаи API-сервери ройгони устувор барои скачать кардани видео/аудио
    api_url = f"https://dreadful-dev.pro{url}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "success":
                        file_url = ""
                        # Интихоби линк вобаста ба тугмаи пахшшуда
                        if fmt_type == "mp3":
                            file_url = data.get("audio_url")
                        elif fmt_type == "low":
                            file_url = data.get("video_low_url") or data.get("video_url")
                        else:
                            file_url = data.get("video_url")
                            if file_url:
                                      if fmt_type == "mp3":
                                await callback.message.answer_audio(audio=file_url)
                            else:
                                await callback.message.answer_video(video=file_url)
                            await status_msg.delete()
                            return
                            
                    await status_msg.edit_text(TEXTS[lang]["error"])
                else:
                    await status_msg.edit_text(TEXTS[lang]["error"])
        except Exception as e:
            print(f"Хатогӣ: {e}")
            await status_msg.edit_text(TEXTS[lang]["error"])

# Веб-сервери оддӣ барои Render
from aiohttp import web
async def handle_web(request):
    return web.Response(text="Bot is online!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())