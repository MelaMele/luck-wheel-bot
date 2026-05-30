import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("ERROR: BOT_TOKEN አልተገኘም!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

active_games = {}

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    welcome_text = (
        "👋 እንኳን ወደ ዕድል መንኮራኩር ቦት በሰላም መጡ!\n\n"
        "🎰 ይህ 10 ተጫዋቾችን በአንዴ የሚያሳትፍ ፕሮፌሽናል የዕጣ ጨዋታ ነው።\n"
        "ለመጀመር ከታች ካሉት ቁጥሮች የፈለጉትን የዕድል ቁጥር ይምረጡ፦"
    )
    
    buttons = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=f"🔢 {i}", callback_data=f"select_{i}"))
        if i % 5 == 0:
            buttons.append(row)
            row = []
            
    # ለሙከራ ያህል ብቻ አዘጋጁ (Admin) 10 ሰው ሳይሞላ እጣ ማውጣት እንዲችል የሙከራ ቁልፍ መጨመር
    buttons.append([InlineKeyboardButton(text="⚡ [Admin] ዕጣውን አሁኑኑ አስጀምር", callback_data="admin_force_spin")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text=welcome_text, reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith("select_"))
async def number_selection_handler(callback_query: types.CallbackQuery):
    selected_num = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    chat_id = callback_query.message.chat.id
    if chat_id not in active_games:
        active_games[chat_id] = []
        
    if any(p["user_id"] == user_id for p in active_games[chat_id]):
        await callback_query.answer("⚠️ ከዚህ በፊት ቁጥር መርጠዋል! እባክዎ እጣው እስኪወጣ ይጠብቁ።", show_alert=True)
        return
        
    await callback_query.answer(f"ቁጥር {selected_num}ን መርጠዋል!", show_alert=True)
    active_games[chat_id].append({"user_id": user_id, "name": username, "num": selected_num})
    current_players = len(active_games[chat_id])
    
    await callback_query.message.answer(
        f"👤 **{username}** ቁጥር **{selected_num}**ን መርጧል።\n"
        f"📊 የተመዘገቡ ተጫዋቾች፦ {current_players}/10"
    )
    
    if current_players >= 10:
        await start_spinning_effect(callback_query.message, chat_id)


# 💡 ይህ አዘጋጁ 10 ሰው ሳይሞላ ጨዋታውን እንዲፈትሽ የሚያስችለው አዲሱ ቁልፍ ነው
@dp.callback_query(lambda c: c.data == "admin_force_spin")
async def admin_force_spin_handler(callback_query: types.CallbackQuery):
    chat_id = callback_query.message.chat.id
    
    # አንድም ሰው ካልተመዘገበ ለሙከራ እንዲሆን ራስህንም ቢሆን አስገብቶ እንዲሰራ ማድረግ
    if chat_id not in active_games or len(active_games[chat_id]) == 0:
        active_games[chat_id] = [{"user_id": callback_query.from_user.id, "name": callback_query.from_user.full_name, "num": "7"}]
        
    await callback_query.answer("⚡ የሙከራ እጣ ማውጣት ተጀምሯል!...", show_alert=False)
    await start_spinning_effect(callback_query.message, chat_id)


async def start_spinning_effect(message: types.Message, chat_id: str):
    # 1. መንኮራኩሩ ሲሽከረከር የሚታየው መልዕክት
    spinning_msg = await message.answer("⚡ መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው! አሸናፊው ማን ይሆን?...")
    
    await asyncio.sleep(4)  # ለ 4 ሰከንድ እንዲሽከረከር ማድረግ
    
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
    await message.answer(text=result_text, parse_mode="HTML", reply_markup=inline_claim if winner_user else None)
    
    # ጨዋታውን ማጽዳት
    active_games[chat_id] = []

async def main():
    print("🤖 ቦቱ ስራ ጀምሯል...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
