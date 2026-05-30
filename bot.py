import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ቶከኑን ከ GitHub Secrets ላይ በደህንነት ያነባል
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ERROR: BOT_TOKEN አልተገኘም! እባክህ GitHub Secrets ላይ በትክክል አዋቅር።")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# የተጫዋቾች መረጃ ጊዜያዊ ማከማቻ
active_games = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "👋 እንኳን ወደ ዕድል መንኮራኩር ቦት በሰላም መጡ!\n\n"
        "🎰 ይህ 10 ተጫዋቾችን በአንዴ የሚያሳትፍ ፕሮፌሽናል የዕጣ ጨዋታ ነው።\n"
        "ለመጀመር ከታች ካሉት ቁጥሮች የፈለጉትን የዕድል ቁጥር ይምረጡ፦"
    )
    
    # ከ1 እስከ 10 ያሉትን ቁጥሮች የያዘ ማራኪ ኪቦርድ መስራት
    buttons = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=f"🔢 {i}", callback_data=f"select_{i}"))
        if i % 5 == 0:
            buttons.append(row)
            row = []
            
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # ያጸደቅነውን አንደኛውን 3D መንኮራኩር ፎቶ መላክ
    await message.answer_photo(
        photo="https://raw.githubusercontent.com/Mela-Content-Bot/assets/main/wheel_start.jpg",
        caption=welcome_text,
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("select_"))
async def number_selection_handler(callback_query: types.CallbackQuery):
    selected_num = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    await callback_query.answer(f"ቁጥር {selected_num}ን መርጠዋል!", show_alert=True)
    
    chat_id = callback_query.message.chat.id
    if chat_id not in active_games:
        active_games[chat_id] = []
        
    # ተጫዋቹ ከዚህ በፊት መርጦ ከሆነ እንዳይደግም መከላከል
    if any(p["user_id"] == user_id for p in active_games[chat_id]):
        await callback_query.message.answer(f"⚠️ {username} ከዚህ በፊት ቁጥር መርጠዋል። እባክዎ እጣው እስኪወጣ ይጠብቁ!")
        return
        
    active_games[chat_id].append({"user_id": user_id, "name": username, "num": selected_num})
    current_players = len(active_games[chat_id])
    
    await callback_query.message.answer(
        f"👤 **{username}** ቁጥር **{selected_num}**ን መርጧል።\n"
        f"📊 የተመዘገቡ ተጫዋቾች፦ {current_players}/10"
    )
    
    # 10 ተጫዋቾች ሲሞሉ ጨዋታውን በራሱ እንዲጀምር ማድረግ
    if current_players >= 10:
        await start_spinning_effect(callback_query.message, chat_id)

async def start_spinning_effect(message: types.Message, chat_id: str):
    # 1. የሽክርክሪት አኒሜሽን (Motion Blur 3D) ምስል መላክ
    spinning_msg = await message.answer_photo(
        photo="https://raw.githubusercontent.com/Mela-Content-Bot/assets/main/wheel_spin.jpg",
        caption="⚡ መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው! አሸናፊው ማን ይሆን?..."
    )
    
    await asyncio.sleep(5)  # ለ 5 ሰከንድ እንዲሽከረከር ማድረግ
    
    winner_number = str(random.randint(1, 10))
    players = active_games[chat_id]
    winner_user = None
    
    for p in players:
        if p["num"] == winner_number:
            winner_user = p
            break
            
    if winner_user:
        result_text = (
            f"🎉 <b>እንኳን ደስ አሎት! ጨዋታው ተጠናቋል!</b> 🎉\n\n"
            f"🎯 አሸናፊ ቁጥር፦ <b>ቁጥር {winner_number}</b>\n"
            f"👑 አሸናፊ ተጫዋች፦ <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"💰 ሽልማትዎን ለመቀበል ከታች ያለውን ቁልፍ ይጫኑ!"
        )
    else:
        result_text = (
            f"🎯 የወጣው ቁጥር፦ <b>ቁጥር {winner_number}</b> ነበር።\n"
            f"😔 አሳዛኝ ነው! ይህንን ቁጥር ማንም አልመረጠውም ነበር። ለሚቀጥለው ዙር ይሞክሩ!"
        )
        
    inline_claim = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 ሻምፒዮን ሽልማትህን ተቀበል", callback_data="claim_prize")]
    ])
    
    await spinning_msg.delete()
    # 3. የመጨረሻውን የ3D አሸናፊ ምስል መላክ
    await message.answer_photo(
        photo="https://raw.githubusercontent.com/Mela-Content-Bot/assets/main/wheel_winner.jpg",
        caption=result_text,
        parse_mode="HTML",
        reply_markup=inline_claim if winner_user else None
    )
    
    active_games[chat_id] = []

async def main():
    print("🤖 ቦቱ ስራ ጀምሯል...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
