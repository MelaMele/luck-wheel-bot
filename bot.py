import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    BotCommand
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 የአድሚን መለያ እና የቴሌብር መረጃ
ADMIN_CHAT_ID = 1065443252  
TELEBIRR_NUMBER = "+251913064239" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# የውስጥ ማከማቻ
active_games = {}     # {"group_chat_id": {"1": {"user_id":..., "name":...}}}
pending_payments = {} # {"user_id": {"chat_id": group_chat_id, "num":..., "main_msg_id":...}}

def generate_keyboard(target_chat_id):
    """ዘመናዊ እና ግልጽ የቁጥሮች ሰሌዳ"""
    game = active_games.get(target_chat_id, {})
    buttons = []
    row = []
    for i in range(1, 11):
        num_str = str(i)
        if num_str in game:
            text = f"🔴 {i} (የተያዘ)"
            callback_data = f"already_sold_{i}"
        else:
            text = f"🟢 ቁጥር {i}"
            callback_data = f"buy_{i}_{target_chat_id}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0: 
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_player_list_text(target_chat_id):
    """በአሁኑ ሰዓት የትኞቹ ቁጥሮች በቅደም ተከተል በማን እንደተያዙ የሚያሳይ ውብ ሰንጠረዥ"""
    game = active_games.get(target_chat_id, {})
    list_text = "<b>📊 የእድለኛ ተሳታፊዎች ዝርዝር፦</b>\n"
    list_text += "━━━━━━━━━━━━━━━━━━━\n"
    for i in range(1, 11):
        num_str = str(i)
        if num_str in game:
            list_text += f" {i} 🔴 <b>{game[num_str]['name']}</b>\n"
        else:
            list_text += f" {i} 🔓 <i>ነጻ ቁጥር (ክፍት)</i>\n"
    list_text += "━━━━━━━━━━━━━━━━━━━"
    return list_text

def get_main_reply_keyboard():
    """VIP ቋሚ የምናሌ ቁልፍ"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 አዲስ ጨዋታ ጀምር"), KeyboardButton(text="ℹ️ የጨዋታ መመሪያ")],
            [KeyboardButton(text="💳 የክፍያ አማራጭ (Telebirr)")]
        ],
        resize_keyboard=True,
        placeholder="ከታች ካሉት አማራጮች አንዱን ይምረጡ..."
    )
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    chat_id = message.chat.id
    
    if message.chat.type == "private":
        await message.answer(
            "💎 <b>እንኳን ወደ ዕድል እሽከርክሪት ፕሪሚየም ቦት በሰላም መጡ!</b> 💎\n\n"
            "⚠️ ጨዋታውን ለመጀመር እባክዎ ቦቱ ባለበት <b>የቴሌግራም ግሩፕ</b> ውስጥ ይግቡና ግሩፑ ላይ <b>/start</b> ይበሉ። የቁጥር ሰሌዳው በግሩፑ ውስጥ በደማቁ ይወጣልዎታል!", 
            reply_markup=get_main_reply_keyboard(),
            parse_mode="HTML"
        )
        return

    if chat_id not in active_games:
        active_games[chat_id] = {}

    current_count = len(active_games[chat_id])
    welcome_text = (
        "🔥 <b>የዕድል እሽከርክሪት ሜዳ ተከፍቷል!</b> 🔥\n\n"
        f"💰 <b>የአንድ ትኬት ዋጋ፦</b> <code>30 ብር</code>\n"
        f"🏆 <b>የአሸናፊው ሽልማት፦</b> <b>200 ብር በቀጥታ!</b>\n"
        f"👥 <b>የተሸጡ ትኬቶች፦</b> 📊 <b>{current_count}/10</b>\n\n"
        f"{get_player_list_text(chat_id)}\n\n"
        "👇 እባክዎ ከታች ያለውን ሰሌዳ በመጠቀም የዕድል ቁጥርዎን ይምረጡ፦"
    )
    await message.answer(text=welcome_text, reply_markup=generate_keyboard(chat_id), parse_mode="HTML")

@dp.message(F.text == "🎰 አዲስ ጨዋታ ጀምር")
async def menu_start_game(message: types.Message):
    if message.chat.type == "private":
        await message.answer("⚠️ ጨዋታ መጀመር የሚቻለው በዋናው የቴሌግራም ግሩፕ ውስጥ ብቻ ነው! እባክዎ ግሩፕ ውስጥ በመግባት /start ይበሉ።")
    else:
        await start_handler(message)

@dp.message(F.text == "ℹ️ የጨዋታ መመሪያ")
async def menu_help(message: types.Message):
    help_text = (
        "📖 <b>የአጫዋች ሙሉ መመሪያ፦</b>\n\n"
        "1️⃣ ግሩፑ ውስጥ ካሉት ቁጥሮች የሚፈልጉትን <b>🟢 ቁጥር</b> ይጫኑ።\n"
        "2️⃣ ቦቱ በውስጥ መስመር የክፍያ መመሪያ እና ማረጋገጫ ይልክልዎታል።\n"
        "3️⃣ በቴሌብር 30 ብር ከፍለው የክፍያውን <b>ስክሪንሾት (Screenshot)</b> ለቦቱ ይልካሉ።\n"
        "4️⃣ አስተዳዳሪው ሲያጸድቀው ቁጥሩ በግሩፑ ሰሌዳ ላይ በስምዎ ይቆለፋል!\n"
        "5️⃣ 10ቱም ሲሞሉ ቦቱ በዕድል እሽከርክሪት እጣ አውጥቶ አሸናፊውን ይለያል።"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "💳 የክፍያ አማራጭ (Telebirr)")
async def menu_payment_info(message: types.Message):
    pay_text = (
        f"💳 <b>ይፋዊ የክፍያ መረጃ (Telebirr)</b> 💳\n\n"
        f"📱 <b>የቴሌብር ስልክ ቁጥር፦</b> <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 <b>የአካውንቱ ስም፦</b> <b>Melaku Mebrate Tekle</b>\n\n"
        f"⚠️ <i>ማሳሰቢያ፦ እባክዎ ክፍያ ከፈጸሙ በኋላ ስክሪንሾት መላክ እንዳይረሱ!</i>"
    )
    await message.answer(pay_text, parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    selected_num = parts[1]
    group_chat_id = int(parts[2]) 
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    if group_chat_id in active_games and selected_num in active_games[group_chat_id]:
        await callback_query.answer("❌ ይቅርታ፣ ይህ ቁጥር አሁን በሌላ ሰው ተገዝቷል!", show_alert=True)
        return

    if user_id in pending_payments:
        await callback_query.answer("⚠️ ቀደም ሲል የላኩት ክፍያ ማረጋገጫ በሂደት ላይ ነው! እባክዎ ይጠብቁ።", show_alert=True)
        return

    await callback_query.answer()
    
    payment_instruction = (
        f"✨ <b>የክፍያ ማረጋገጫ ፎርም</b> ✨\n\n"
        f"🎯 <b>የመረጡት ቁጥር፦</b> <b>ቁጥር {selected_num}</b>\n"
        f"💰 <b>የሚከፍሉት መጠን፦</b> <code>30 ብር</code>\n\n"
        f"📱 <b>የቴሌብር ቁጥር፦</b> <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 <b>ስም፦</b> Melaku Mebrate Tekle\n\n"
        f"📸 እባክዎ ክፍያውን ፈጽመው ሲጨርሱ <b>የክፍያውን ስክሪንሾት (Screenshot)</b> እዚህ ላይ ይላኩ።"
    )
    
    pending_payments[user_id] = {
        "chat_id": group_chat_id, 
        "num": selected_num,
        "name": username,
        "main_msg_id": callback_query.message.message_id 
    }
    
    try:
        await bot.send_message(chat_id=user_id, text=payment_instruction, parse_mode="HTML")
        await bot.send_message(chat_id=group_chat_id, text=f"📥 <b>{username}</b> ቁጥር {selected_num}ን ለመግዛት የክፍያ መመሪያ በውስጥ መስመር ተልኮለታል። ✨", parse_mode="HTML")
    except Exception:
        await callback_query.message.answer(
            f"❌ <b>አቶ {username}፣ ቦቱን በውስጥ መስመር አልከፈቱትም!</b>\n"
            f"እባክዎ መጀመሪያ እዚህ ይጫኑ 👉 @{(await bot.get_me()).username} በመግባት <b>Start</b> ይበሉ፤ ከዚያ መልሰው ግሩፑ ላይ ቁጥሩን ይጫኑ።",
            parse_mode="HTML"
        )

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ቀደም ብሎ ተሽጧል! እባክዎ ሌላ ክፍት ቁጥር ይምረጡ።", show_alert=True)

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    if user_id not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ከግሩፑ ላይ ቁጥር ይምረጡ፤ ከዚያ የስክሪንሾት ፎቶ ይላኩ።")
        return
        
    user_data = pending_payments[user_id]
    selected_num = user_data["num"]
    
    await message.reply("📥 <b>የክፍያ ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ በግሩፑ ላይ እስኪመዘገብ እባክዎ በትዕግስት ይጠብቁ! 🕒</b>", parse_mode="HTML")
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"adm_ap_{user_id}"),
            InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"adm_rj_{user_id}")
        ]
    ])
    
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 <b>አዲስ የክፍያ ማረጋገጫ!</b>\n\n👤 <b>ተጫዋች፦</b> {user_data['name']}\n🔢 <b>ቁጥር፦</b> <b>ቁጥር {selected_num}</b>",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("adm_ap_"))
async def admin_approve_handler(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_CHAT_ID:
        await callback_query.answer("❌ ይህ ትዕዛዝ ለአስተዳዳሪው ብቻ የተፈቀደ ነው!", show_alert=True)
        return
        
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments:
        await callback_query.answer("❌ ይህ ጥያቄ ቀደም ብሎ ምላሽ አግኝቷል።")
        return
        
    user_data = pending_payments[target_user_id]
    group_chat_id = user_data["chat_id"] 
    selected_num = user_data["num"]
    
    if group_chat_id not in active_games:
        active_games[group_chat_id] = {}
        
    active_games[group_chat_id][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    
    await bot.send_message(chat_id=target_user_id, text=f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {selected_num}</b> በግሩፑ ሰሌዳ ላይ በስምዎ ተመዝግቧል። መልካም ዕድል! 🍀", parse_mode="HTML")
    
    current_count = len(active_games[group_chat_id])
    
    # 🔄 በዋናው ግሩፕ ላይ የዘመነውን ሰሌዳ እና የተጫዋቾችን ዝርዝር አንድ ላይ ልኮ ማደስ
    try:
        updated_text = (
            "🔥 <b>የዕድል እሽከርክሪት ወቅታዊ ሁኔታ</b> 🔥\n\n"
            f"👥 <b>የተሸጡ ትኬቶች፦</b> 📊 <b>{current_count}/10</b>\n\n"
            f"{get_player_list_text(group_chat_id)}\n\n"
            "👇 አሁኑኑ የእርስዎን ቁጥር በመምረጥ ይሳተፉ፦"
        )
        await bot.send_message(
            chat_id=group_chat_id,
            text=updated_text,
            reply_markup=generate_keyboard(group_chat_id),
            parse_mode="HTML"
        )
    except Exception:
        pass
        
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption=f"✅ ተፈቅዷል! ቁጥር {selected_num} ተመዝግቧል።", reply_markup=None)
    
    if current_count >= 10:
        asyncio.create_task(start_spinning_effect(group_chat_id))

@dp.callback_query(F.data.startswith("adm_rj_"))
async def admin_reject_handler(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_CHAT_ID:
        await callback_query.answer("❌ ይህ ትዕዛዝ ለአስተዳዳሪው ብቻ የተፈቀደ ነው!", show_alert=True)
        return
        
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments:
        await callback_query.answer()
        return
        
    await bot.send_message(chat_id=target_user_id, text="❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b>\nየላኩት ስክሪንሾት ትክክለኛ አይደለም ወይም አልደረሰንም።", parse_mode="HTML")
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption="❌ ይህ ክፍያ ውድቅ ተደርጓል።", reply_markup=None)

# 🎰 እጅግ ዘመናዊ እና የካሲኖ ስሜት የሚሰጥ የዕጣ አወጣጥ ሂደት
async def start_spinning_effect(group_chat_id: int):
    winner_number = str(random.randint(1, 10))
    
    msg = await bot.send_message(
        chat_id=group_chat_id, 
        text="🚨 <b>10ቱም ትኬቶች በሙሉ ተሽጠዋል! የዕድል መንኮራኩሩ አሁን ይጀምራል...</b> 🚨", 
        parse_mode="HTML"
    )
    
    await asyncio.sleep(4)
    await msg.edit_text("🔄 <b>የዕድል መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🎰 SPINNING ]</b>", parse_mode="HTML")
    await asyncio.sleep(4)
    await msg.edit_text("⚡ <b>ፍጥነቱ እጅግ ጨምሯል! አሸናፊው ማን ይሆን? የሁሉም ሰው ዓይን ስክሪኑ ላይ ነው... 👀</b>", parse_mode="HTML")
    await asyncio.sleep(4)
    await msg.edit_text("🎡 <b>መንኮራኩሩ ፍጥነቱን ቀስ በቀስ እየቀነሰ ነው... ወደ መቆሚያው እየተቃረበ ነው! ⏳</b>", parse_mode="HTML")
    await asyncio.sleep(4)
    await msg.edit_text("🎯 <b>አንድ ቁጥር ላይ ሊያርፍ ነው!... የመጨረሻ 3 ሰከንዶች! 🛑</b>", parse_mode="HTML")
    await asyncio.sleep(3)
    
    players = active_games.get(group_chat_id, {})
    winner_user = players.get(winner_number)
    
    if winner_user:
        result_text = (
            f"🎉 <b>ዕጣው በይፋ ወጥቷል! እንኳን ደስ አሎት!</b> 🎉\n\n"
            f"👑 <b>የዚህ ዙር ታላቅ ሻምፒዮን፦</b> <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n"
            f"🎰 <b>የመጣው የዕድል ቁጥር፦</b> 🔥 <b>ቁጥር {winner_number}</b> 🔥\n\n"
            f"💰 <b>የ 200 ብር</b> የሽልማት ገንዘብዎን ለመቀበል አሁኑኑ ለአስተዳዳሪው መልዕክት ይላኩ! 🎁"
        )
    else:
        result_text = (
            f"🎰 የዕድል መንኮራኩሩ ያረፈበት ቁጥር፦ <b>ቁጥር {winner_number}</b> ነበር።\n\n"
            f"😔 <b>የሚገርም ነው!</b> ይህንን ቁጥር በዚህ ዙር ማንም ስላልገዛው አሸናፊ የለም።\n"
            f"💰 የተሰበሰበው ገንዘብ በቀጥታ ወደ ሚቀጥለው ዙር ተላልፏል! አዲስ ዙር ለመጀመር በግሩፑ ውስጥ /start ይበሉ።"
        )
        
    await msg.edit_text(text=result_text, parse_mode="HTML")
    active_games[group_chat_id] = {}

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="🕹️ ጨዋታውን ይጀምሩ / ማደሻ")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
