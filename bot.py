import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 የአድሚን መለያ እና የቴሌብር መረጃ
ADMIN_CHAT_ID = 1065443252  
TELEBIRR_NUMBER = "+251913064239" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# የውስጥ ዳታቤዝ (ማከማቻ)
active_games = {}     # በየግሩፑ የተሸጡ ቁጥሮች {"chat_id": {"1": {"user_id":..., "name":...}}}
pending_payments = {} # ማረጋገጫ የሚጠብቁ {"user_id": {"chat_id":..., "num":..., "main_msg_id":...}}

def generate_keyboard(chat_id):
    """የቁጥሮችን ሰሌዳ ወቅታዊ ሁኔታ አይቶ የሚያዘጋጅ ተግባር"""
    game = active_games.get(chat_id, {})
    buttons = []
    row = []
    for i in range(1, 11):
        num_str = str(i)
        if num_str in game:
            text = f"🔴 {i} (የተሸጠ)"
            callback_data = f"already_sold_{i}"
        else:
            text = f"🔢 {i}"
            callback_data = f"buy_{i}_{chat_id}" # የትኛው ግሩፕ እንደሆነ መለየት
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0: 
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    chat_id = message.chat.id
    
    # ቦቱ በግል መስመር (Private) ከተከፈተ የመቀበያ መልዕክት
    if message.chat.type == "private":
        await message.answer(
            "👋 ሰላም! ይህ የዕድል እሽከርክሪት የክፍያ ማረጋገጫ መቀበያ ክፍል ነው።\n"
            "እባክዎ መጀመሪያ ጨዋታው ባለበት የቴሌግራም ግሩፕ ውስጥ ቁጥር ይምረጡ።"
        )
        return

    if chat_id not in active_games:
        active_games[chat_id] = {}

    welcome_text = (
        "🎡 <b>እንኳን ወደ ሕዝባዊ የዕድል እሽከርክሪት መድረክ መጡ!</b> 🎡\n\n"
        "💵 የትኬት ዋጋ፦ <b>30 ብር</b>\n"
        f"👥 አሁን የተሸጡ ትኬቶች፦ <b>{len(active_games[chat_id])}/10</b>\n\n"
        "ከ1 እስከ 10 ያለውን የዕድል ቁጥርዎን በመምረጥ ይሳተፉ፦"
    )
    
    await message.answer(text=welcome_text, reply_markup=generate_keyboard(chat_id), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    selected_num = parts[1]
    chat_id = int(parts[2]) # የጨዋታው ግሩፕ ID
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    # ደህንነት፦ በሂደት ላይ ያለ ክፍያ ካለው መከልከል
    if user_id in pending_payments:
        await callback_query.answer("⚠️ ቀደም ሲል የላኩት ክፍያ ማረጋገጫ በሂደት ላይ ነው! እባክዎ ይጠብቁ።", show_alert=True)
        return

    # ተጫዋቹን ወደ ቦቱ የውስጥ መስመር (Inbox) እንዲሄድ ማሳሰቢያ መስጠት
    bot_user = await bot.get_me()
    bot_username = bot_user.username
    
    await callback_query.answer()
    
    # በግሩፑ ላይ መመሪያ መላክ
    await callback_query.message.answer(
        f"📩 <b>{username}</b>፣ ቁጥር <b>{selected_num}</b>ን ለመግዛት የክፍያ መመሪያውን በቦቱ የውስጥ መስመር ልከናል።\n"
        f"🔗 <a href='t.me/{bot_username}?start=start'>እዚህ በመጫን ወደ ቦቱ ኢንቦክስ ይሂዱ</a>", 
        parse_mode="HTML"
    )
    
    # በውስጥ መስመር ለተጫዋቹ መመሪያ መላክ (Inbox)
    payment_instruction = (
        f"🎯 <b>ቁጥር {selected_num}ን መርጠዋል!</b>\n\n"
        f"💰 እባክዎ <b>30 ብር</b> በቴሌብር (Telebirr) በሚከተለው ስልክ ቁጥር ይላኩ፦\n"
        f"📱 ስልክ ቁጥር፦ <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 ስም፦ <b>Melaku Mebrate Tekle</b>\n\n"
        f"📸 <b>ክፍያውን ፈጽመው እንደጨረሱ የክፍያውን ስክሪንሾት (Screenshot) እዚህ ላይ ይላኩ።</b>"
    )
    
    pending_payments[user_id] = {
        "chat_id": chat_id,
        "num": selected_num,
        "name": username,
        "main_msg_id": callback_query.message.message_id # ዋናውን የኪቦርድ መልዕክት ID መያዝ
    }
    
    try:
        await bot.send_message(chat_id=user_id, text=payment_instruction, parse_mode="HTML")
    except Exception:
        await callback_query.message.answer(f"⚠️ <b>{username}</b> እባክዎ መጀመሪያ ቦቱን ስታርት (Start) ያድርጉት።")

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ተሽጧል! እባክዎ ሌላ ቁጥር ይምረጡ።", show_alert=True)

# 📸 ተጫዋቹ በውስጥ መስመር (Inbox) ስክሪንሾት ሲልክ
@dp.message(F.chat.type == "private", F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ግሩፕ ውስጥ ገብተው ቁጥር ይምረጡ።")
        return
        
    user_data = pending_payments[user_id]
    
    await message.reply("📥 <b>የክፍያ ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ እስኪመዘገብ እባክዎ ይጠብቁ!</b>", parse_mode="HTML")
    
    # ለአድሚኑ (ላንተ) በግል ብቻ ማረጋገጫ መላክ
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"adm_ap_{user_id}"),
            InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"adm_rj_{user_id}")
        ]
    ])
    
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 <b>አዲስ የክፍያ ማረጋገጫ!</b>\n\n👤 ተጫዋች፦ {user_data['name']}\n🔢 ቁጥር፦ <b>ቁጥር {user_data['num']}</b>",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

# ✅ አድሚኑ ማረጋገጫ ሲጫን (ደህንነቱ የተጠበቀ)
@dp.callback_query(F.data.startswith("adm_ap_"))
async def admin_approve_handler(callback_query: types.CallbackQuery):
    # ደህንነት ማረጋገጫ፦ አድሚኑ ካልሆነ መከልከል
    if callback_query.from_user.id != ADMIN_CHAT_ID:
        await callback_query.answer("❌ ይህ ትዕዛዝ ለአስተዳዳሪው ብቻ የተፈቀደ ነው!", show_alert=True)
        return
        
    target_user_id = int(callback_query.data.split("_")[2])
    
    if target_user_id not in pending_payments:
        await callback_query.answer("❌ ይህ ጥያቄ የለም ወይም ምላሽ አግኝቷል።")
        return
        
    user_data = pending_payments[target_user_id]
    chat_id = user_data["chat_id"]
    selected_num = user_data["num"]
    
    if chat_id not in active_games:
        active_games[chat_id] = {}
        
    # ቁጥሩን በቋሚነት መመዝገብ
    active_games[chat_id][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    
    # ለተጫዋቹ በኢንቦክስ ማሳወቅ
    await bot.send_message(chat_id=target_user_id, text=f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {selected_num}</b> ለእርስዎ ተመዝግቧል። መልካም ዕድል!", parse_mode="HTML")
    
    # በሕዝባዊ ግሩፑ ላይ ማሳወቅ
    current_count = len(active_games[chat_id])
    await bot.send_message(
        chat_id=chat_id,
        text=f"📣 <b>የደስታ ዜና!</b>\n👤 <b>{user_data['name']}</b> ቁጥር <b>{selected_num}</b>ን በ30 ብር ገዝቷል።\n📊 በአጠቃላይ የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>",
        parse_mode="HTML"
    )
    
    # 🔥 ቁልፉ ወደ ላይ እንዳይደበቅ ዋናውን ኪቦርድ እዚያው ባለበት ማደስ (Edit)
    try:
        updated_text = (
            "🎡 <b>እንኳን ወደ ሕዝባዊ የዕድል እሽከርክሪት መድረክ መጡ!</b> 🎡\n\n"
            "💵 የትኬት ዋጋ፦ <b>30 ብር</b>\n"
            f"👥 አሁን የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>\n\n"
            "ከ1 እስከ 10 ያለውን የዕድል ቁጥርዎን በመምረጥ ይሳተፉ፦"
        )
        await bot.edit_message_text(
            text=updated_text,
            chat_id=chat_id,
            message_id=user_data["main_msg_id"],
            reply_markup=generate_keyboard(chat_id),
            parse_mode="HTML"
        )
    except Exception:
        pass
        
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption=f"✅ ተፈቅዷል! ቁጥር {selected_num} ተመዝግቧል።", reply_markup=None)
    
    # 10 ሰው ከሞላ ጨዋታውን ማስጀመር
    if current_count >= 10:
        await start_spinning_effect(chat_id, user_data["main_msg_id"])

# ❌ አድሚኑ ውድቅ ሲያደርገው
@dp.callback_query(F.data.startswith("adm_rj_"))
async def admin_reject_handler(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_CHAT_ID:
        await callback_query.answer("❌ ይህ ትዕዛዝ ለአስተዳዳሪው ብቻ የተፈቀደ ነው!", show_alert=True)
        return
        
    target_user_id = int(callback_query.data.split("_")[2])
    
    if target_user_id not in pending_payments:
        await callback_query.answer()
        return
        
    await bot.send_message(chat_id=target_user_id, text="❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b>\nየላኩት ስክሪንሾት ትክክለኛ አይደለም። እባክዎ እንደገና በትክክል ይክፈሉ ያረጋግጡ።", parse_mode="HTML")
    
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption="❌ ይህ ክፍያ ውድቅ ተደርጓል።", reply_markup=None)

async def start_spinning_effect(chat_id: int, main_msg_id: int):
    spinning_msg = await bot.send_message(chat_id=chat_id, text="🔄 <b>10 ትኬቶች ተሽጠዋል! እጣው ሊወጣ 3 ሰከንድ ቀረው...</b>", parse_mode="HTML")
    await asyncio.sleep(1)
    await spinning_msg.edit_text("⚡ <b>መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🔄 SPINNING ]</b>", parse_mode="HTML")
    await asyncio.sleep(1.5)
    
    winner_number = str(random.randint(1, 10))
    players = active_games[chat_id]
    winner_user = players.get(winner_number)
    
    if winner_user:
        result_text = (
            f"🎉 <b>ዕጣው በይፋ ወጥቷል! እንኳን ደስ አሎት!</b> 🎉\n\n"
            f"🎯 የወጣው አሸናፊ ቁጥር፦ <b>ቁጥር {winner_number}</b>\n"
            f"👑 ሻምፒዮን፦ <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"💰 የ 200 ብር ሽልማትዎን ለመቀበል አድሚኑን ያነጋግሩ!"
        )
    else:
        result_text = f"🎯 የወጣው ቁጥር፦ <b>ቁጥር {winner_number}</b> ነበር።\n😔 ይህንን ቁጥር ማንም ስላልገዛው ገንዘቡ ለሚቀጥለው ዙር ይተላለፋል!"
        
    await spinning_msg.delete()
    await bot.send_message(chat_id=chat_id, text=result_text, parse_mode="HTML")
    active_games[chat_id] = {}

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
