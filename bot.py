import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 💡 ይህ አዲስ ክፍል ነው፦ ፎቶ ስትልክለት የፋይሉን ID አውጥቶ መልሶ ይልክልሃል!
@dp.message(lambda message: message.photo)
async def get_photo_file_id(message: types.Message):
    file_id = message.photo[-1].file_id
    await message.reply(f"📷 <b>የፎቶው FILE ID ይህ ነው፦</b>\n\n<code>{file_id}</code>", parse_mode="HTML")

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("ሰላም! እባክህ የሽክርክሪቱን ፎቶ ላክልኝና File IDውን ልንገርህ።")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
