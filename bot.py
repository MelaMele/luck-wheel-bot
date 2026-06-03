import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 ያንተ መረጃዎች እዚህ ጋ በትክክል ገብተዋል
ADMIN_CHAT_ID = 1065443252  
TELEBIRR_NUMBER = "+251913064239" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# የጨዋታ መረጃዎች ማከማቻ
active_games = {} 
pending_payments = {} 

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in active_games:
        active_games[chat_id] = {}

    welcome_text = (
        "🎡 እንኳን ወደ ሕዝባዊ የዕድል እሽከርክሪት መድረክ መጡ! 🎡\n\n"
        "💵 የትኬት ዋጋ፦ <b>30 ብር</b>\n"
        f"👥 አሁን የተሸጡ ትኬቶች፦ <b>{len(active_games[chat_id])}/10</b>\n\n"
        "ከ1 እስከ 10 ያለውን የዕድል ቁጥርዎን በመምረጥ ይሳተፉ፦"
    )
    
    buttons = []
    row = []
    for i in range(1, 11):
        num_str = str(i)
        if num_str in active_games[chat_id]:
            text = f"🔴 {i} (የተሸጠ)"
            callback_data = f"already_sold_{i}"
        else:
            text = f"🔢 {i}"
            callback_data = f"buy_{i}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0: 
            buttons.append(row)
            row = []
            
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(text=welcome_text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    selected_num = callback_query.data.split("_")[1]
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    chat_id = callback_query.message.chat.id
    
    if user_id in pending_payments:
        await callback_query.answer("⚠️ ቀደም ሲል የላኩት ክፍያ ማረጋገጫ እየታየ ነው! እባክዎ ይጠብቁ።", show_alert=True)
        return

    await callback_query.answer()
    
    payment_instruction = (
        f"🎯 <b>ቁጥር {selected_num}ን መርጠዋል!</b>\n\n"
        f"💰 እባክዎ <b>30 ብር</b> በቴሌብር (Telebirr) በሚከተለው ስልክ ቁጥር ይላኩ፦\n"
        f"📱 ስልክ ቁጥር፦ <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 ስም፦ <b>Melaku Mebrate Tekle</b>\n\n"
        f"⚠️ <b>ዋናው ደረጃ፦</b> ክፍያውን እንደፈጸሙ የክፍያውን <b>ስክሪንሾት (Screenshot)</b> እዚህ ቦት ላይ ይላኩ። "
        f"የላኩት ምስል ተረጋግጦ ቁጥሩ በአንድ ደቂቃ ውስጥ ይመዘገብልዎታል።"
    )
    
    pending_payments[user_id] = {
        "chat_id": chat_id,
        "num": selected_num,
        "name": username,
        "message_id": callback_query.message.message_id
    }
    
    await callback_query.message.answer(text=payment_instruction, parse_mode="HTML")

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ተሽጧል! እባክዎ ሌላ ቁጥር ይምረጡ።", show_alert=True)

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ከላይ ቁጥር ይምረጡ፤ ከዚያ የክፍያ ስክሪንሾት ይላኩ።")
        return
        
    user_data = pending_payments[user_id]
    selected_num = user_data["num"]
    chat_id = user_data["chat_id"]
    
    await message.reply("📥 የክፍያ ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ እስኪመዘገብ እባክዎ በትዕግስት ይጠብቁ!")
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"admin_approve_{user_id}"),
            InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"admin_reject_{user_id}")
        ]
    ])
    
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 <b>አዲስ የክፍያ ማረጋገጫ ጥያቄ!</b>\n\n👤 ተጫዋች፦ {user_data['name']}\n🔢 የተመረጠ ቁጥር፦ <b>ቁጥር {selected_num}</b>",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("admin_approve_"))
async def admin_approve_handler(callback_query: types.CallbackQuery):
    target_user_id = int(callback_query.data.split("_")[2])
    
    if target_user_id not in pending_payments:
        await callback_query.answer("❌ ይህ ጥያቄ ቀድሞ ምላሽ አግኝቷል ወይም የለም።")
        return
        
    user_data = pending_payments[target_user_id]
    chat_id = user_data["chat_id"]
    selected_num = user_data["num"]
    
    if chat_id not in active_games:
        active_games[chat_id] = {}
        
    active_games[chat_id][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    
    await bot.send_message(
        chat_id=target_user_id,
        text=f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {selected_num}</b> በትክክል ለእርስዎ ተመዝግቧል። መልካም ዕድል!"
    )
    
    current_count = len(active_games[chat_id])
    await bot.send_message(
        chat_id=chat_id,
        text=f"👤 <b>{user_data['name']}</b> ቁጥር <b>{selected_num}</b>ን በ30 ብር ገዝቷል።\n📊 የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>"
    )
    
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption=f"✅ ይህ ክፍያ ጸድቋል! ቁጥር {selected_num} ተመዝግቧል።", reply_markup=None)
    
    if current_count >= 10:
        await start_spinning_effect(callback_query.message, chat_id)

@dp.callback_query(F.data.startswith("admin_reject_"))
async def admin_reject_handler(callback_query: types.CallbackQuery):
    target_user_id = int(callback_query.data.split("_")[2])
    
    if target_user_id not in pending_payments:
        await callback_query.answer()
        return
        
    await bot.send_message(
        chat_id=target_user_id,
        text="❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b>\nየላኩት ስክሪንሾት ትክክለኛ አይደለም ወይም ክፍያው አልደረሰንም። እባክዎ እንደገና በትክክል ይክፈሉ ወይም አስተዳዳሪውን ያነጋግሩ።"
    )
    
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption="❌ ይህ ክፍያ ውድቅ ተደርጓል።", reply_markup=None)

async def start_spinning_effect(message: types.Message, chat_id: int):
    # 🎰 እውነተኛነትን ለመጨመር በየሰከንዱ የሚቀያየር የበይነገጽ አኒሜሽን
    spinning_msg = await bot.send_message(chat_id=chat_id, text="🔄 10 ትኬቶች ሙሉ በሙሉ ተሽጠዋል! እጣው ሊወጣ 3 ሰከንድ ቀረው...")
    await asyncio.sleep(1)
    await spinning_msg.edit_text("⚡ መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🔄 SPINNING ]")
    await asyncio.sleep(1.5)
    await spinning_msg.edit_text("🎯 ወደ ማጠናቀቂያው እየተቃረበ ነው... አሸናፊው ቁጥር ሊታወቅ ነው!...")
    await asyncio.sleep(1.5)
    
    winner_number = str(random.randint(1, 10))
    players = active_games[chat_id]
    winner_user = players.get(winner_number)
    
    if winner_user:
        result_text = (
            f"🎉 <b>ዕጣው በይፋ ወጥቷል! እንኳን ደስ አሎት!</b> 🎉\n\n"
            f"🎯 የወጣው አሸናፊ ቁጥር፦ <b>ቁጥር {winner_number}</b>\n"
            f"👑 ሻምፒዮን፦ <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"💰 የ 300 ብር ሽልማትዎን ለመቀበል ቦቱ ላይ መልዕክት በመላክ አድሚኑን ያነጋግሩ!"
        )
    else:
        result_text = f"🎯 የወጣው ቁጥር፦ <b>ቁጥር {winner_number}</b> ነበር።\n😔 ይህንን ቁጥር በዚህ ዙር ማንም አልገዛውም ነበር። ገንዘቡ ለሚቀጥለው ዙር ይተላለፋል!"
        
    await spinning_msg.delete()
    await bot.send_message(chat_id=chat_id, text=result_text, parse_mode="HTML")
    active_games[chat_id] = {}

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
