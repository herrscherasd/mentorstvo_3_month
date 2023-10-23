from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from dotenv import load_dotenv
from logging import basicConfig, INFO
import os, requests
import sqlite3

load_dotenv('.env')

bot = Bot(os.environ.get('token'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
basicConfig(level=INFO)

conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INT, username TEXT, first_name TEXT, last_name TEXT)')
conn.commit()

@dp.message_handler(commands=('start'))
async def start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

   
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    existing_user = cursor.fetchone()

    if existing_user is None:
        cursor.execute('INSERT INTO users VALUES (?, ?, ?, ?)', (user_id, username, first_name, last_name))
        conn.commit()

    await message.answer(f"Привет {message.from_user.full_name}, отправьте мне ссылку на видео из TikTok, и я попробую его скачать.")

@dp.message_handler()
async def get_message_url(message:types.Message):
    if 'tiktok.com' in message.text:
        await message.answer(f"{message.text}")
        input_url = message.text.split("?")
        get_id_video = input_url[0].split("/")[5] 
        video_api = requests.get(f'https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/?aweme_id={get_id_video}').json()
        video_url = video_api.get("aweme_list")[0].get("video").get("play_addr").get("url_list")[0]
        await message.answer(video_url)

        video_data = video_api.get("aweme_list")[0]
        author = video_data.get("author").get("nickname")
        description = video_data.get("desc")
        statistics = video_data.get("statistics")

        views = statistics.get("play_count")
        likes = statistics.get("digg_count")
        comments = statistics.get("comment_count")

        await message.answer(f"Описание видео: {description}\n"
                           f"ID видео: {get_id_video}\n"
                           f"Автор: {author}\n"
                           f"Просмотры: {views}\n"
                           f"Лайки: {likes}\n"
                           f"Комментарии: {comments}")
        
       


        if video_url:
            await message.answer("Скачиваем видео...")
            title_video = video_api.get("aweme_list")[1].get("desc")
            await message.answer(title_video)
            try:
                with open(f'video/{title_video}.mp4', 'wb') as video_file:
                    video_file.write(requests.get(video_url).content)
                await message.answer(f"Видео {title_video} успешно скачан XD")
                with open(f'video/{title_video}.mp4', 'rb') as send_video_file:
                    await message.answer_video(send_video_file)
            except Exception as error:
                await message.answer(f"Error: {error}")
    else:
        await message.answer("Неправильная ссылка на видео TikTok")

executor.start_polling(dp, skip_updates=True)