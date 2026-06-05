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
active_games = {}     # {"chat_id": {"1": {"user_id":..., "name":...}}}
pending_payments = {} # {"user_id": {"chat_id":..., "num":..., "main_msg_id":...}}

def generate_keyboard(chat_id):
    """የቁጥሮችን ሰሌዳ እጅግ ዘመናዊ በሆነ መልኩ የአሸናፊዎችን ስም ጭምር ይዞ የሚመነጭ ተግባር"""
    game = active_games.get(chat_id, {})
    buttons = []
    row = []
    for i in range(1, 11):
        num_str = str(i)
        if num_str in game:
            # የገዛውን ሰው ስም በአጭሩ በተኑ ላይ ያሳያል (እጅግ ዘመናዊ ያደርገዋል)
            buyer_name = game[num_str]['name'][:8]  
            text = f"🔴 {i} ({buyer_name}...)"
            callback_data = f"already_sold_{i}"
        else:
            text = f"🔢 ቁጥር {i}"
            callback_data = f"buy_{i}_{chat_id}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0: 
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_main_reply_keyboard():
    """ከታች ሁልጊዜ የሚቀመጥ ቋሚ የምናሌ ቁልፍ (Persistent Menu)"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 አዲስ ጨዋታ ጀምር"), KeyboardButton(text="ℹ️ እንዴት ልጫወት?")],
            [KeyboardButton(text="💳 የክፍያ መረጃ (Telebirr)")]
        ],
        resize_keyboard=True,
        placeholder="ከታች ካሉት አማራጮች አንዱን ይምረጡ..."
    )
    return keyboard

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    chat_id = message.chat.id
    if chat_id not in active_games:
        active_games[chat_id] = {}

    welcome_text = (
        "🎡 <b>እንኳን ወደ ዕድል እሽከርክሪት መድረክ በሰላም መጡ!</b> 🎡\n\n"
        "💵 <b>የአንድ ትኬት ዋጋ፦</b> 30 ብር\n"
        f"👥 <b>የተሸጡ ትኬቶች፦</b> {len(active_games[chat_id])}/10\n\n"
        "👇 እባክዎ ከታች ካለው ሰሌዳ ላይ የዕድል ቁጥርዎን በመምረጥ ይሳተፉ፦"
    )
    # ቋሚ ምናሌውን እና መጫወቻ ሰሌዳውን በአንድ ላይ ያሳያል
    await message.answer(
        text=welcome_text, 
        reply_markup=generate_keyboard(chat_id), 
        parse_mode="HTML"
    )
    # በውስጥ መስመር ከሆነ ቋሚ ምናሌውን ይዘረጋል
    if message.chat.type == "private":
        await message.answer("🕹️ ዋናው ምናሌ ተከፍቷል፦", reply_markup=get_main_reply_keyboard())

# ቋሚ በተኖችን በጽሑፍ ሲጫኑ የሚሰሩ ተግባራት
@dp.message(F.text == "🎰 አዲስ ጨዋታ ጀምር")
async def menu_start_game(message: types.Message):
    await start_handler(message)

@dp.message(F.text == "ℹ️ እንዴት ልጫወት?")
async def menu_help(message: types.Message):
    help_text = (
        "📖 <b>የአጫዋች መመሪያ፦</b>\n\n"
        "1️⃣ ከ1 እስከ 10 ካሉት ቁጥሮች ውስጥ የሚፈልጉትን ይምረጡ።\n"
        "2️⃣ ቦቱ በውስጥ መስመር የሚልክልዎትን የቴሌብር ቁጥር በመጠቀም 30 ብር ይላኩ።\n"
        "3️⃣ የከፈሉበትን ስክሪንሾት (Screenshot) ለቦቱ ይላኩ።\n"
        "4️⃣ አስተዳዳሪው ሲያጸድቅልዎ ቁጥሩ ስምዎ ላይ ይመዘገባል።\n"
        "5️⃣ 10ቱም ቁጥሮች ሲያልቁ ቦቱ በቀጥታ እጣ አውጥቶ የ 200 ብር ተሸላሚውን ይለያል!"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(F.text == "💳 የክፍያ መረጃ (Telebirr)")
async def menu_payment_info(message: types.Message):
    pay_text = (
        f"💳 <b>ትክክለኛ የክፍያ መረጃ፦</b>\n\n"
        f"📱 የቴሌብር ስልክ ቁጥር፦ <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 የተጠቃሚ ስም፦ <b>Melaku Mebrate Tekle</b>\n\n"
        f"⚠️ ማሳሰቢያ፦ እባክዎ ክፍያ ሲፈጽሙ ስም መሳሳቱን ያረጋግጡ!"
    )
    await message.answer(pay_text, parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    selected_num = parts[1]
    chat_id = int(parts[2]) 
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    if user_id in pending_payments:
        await callback_query.answer("⚠️ ቀደም ሲል የላኩት ክፍያ ማረጋገጫ በሂደት ላይ ነው! እባክዎ ይጠብቁ።", show_alert=True)
        return

    await callback_query.answer()
    
    # 💳 ክፍያውን ወደ ተጫዋቹ የውስጥ መስመር (DM) ብቻ በመውሰድ ግሩፑን ነጻ ማድረግ
    payment_instruction = (
        f"⚡ <b>የውስጥ መስመር ክፍያ ማረጋገጫ</b> ⚡\n\n"
        f"🎯 <b>የመረጡት ቁጥር፦</b> ቁጥር {selected_num}\n"
        f"💰 <b>የሚከፍሉት መጠን፦</b> 30 ብር\n\n"
        f"📱 <b>የቴሌብር ስልክ ቁጥር፦</b> <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 <b>ስም፦</b> Melaku Mebrate Tekle\n\n"
        f"📸 እባክዎ ክፍያውን ፈጽመው እንደጨረሱ <b>የክፍያውን ስክሪንሾት (Screenshot)</b> እዚህ ላይ ይላኩ።"
    )
    
    pending_payments[user_id] = {
        "chat_id": chat_id,
        "num": selected_num,
        "name": username,
        "main_msg_id": callback_query.message.message_id 
    }
    
    try:
        await bot.send_message(chat_id=user_id, text=payment_instruction, parse_mode="HTML")
        await bot.send_message(chat_id=chat_id, text=f"📥 <b>@{callback_query.from_user.username or username}</b> ቁጥር {selected_num}ን ለመግዛት የክፍያ መመሪያ በውስጥ መስመር ተልኮለታል።")
    except Exception:
        # ተጫዋቹ ቦቱን Start ካላደረገው ግሩፑ ላይ መልዕክት ያሳያል
        await callback_query.message.answer(
            f"❌ <b>አቶ {username}፣ ቦቱን በውስጥ መስመር አላስነሱትም!</b>\n"
            f"እባክዎ መጀመሪያ እዚህ ይጫኑ 👉 @{(await bot.get_me()).username} በመግባት <b>Start</b> ይበሉ፤ ከዚያ መልሰው ቁጥሩን ይጫኑ።",
            parse_mode="HTML"
        )

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ተሽጧል! እባክዎ ሌላ ቁጥር ይምረጡ።", show_alert=True)

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    if user_id not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ከግሩፑ ላይ ቁጥር ይምረጡ፤ ከዚያ የስክሪንሾት ፎቶ ይላኩ።")
        return
        
    user_data = pending_payments[user_id]
    selected_num = user_data["num"]
    
    await message.reply("📥 <b>የክፍያ ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ እስኪመዘገብ እባክዎ በትዕግስት ይጠብቁ!</b>", parse_mode="HTML")
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"adm_ap_{user_id}"),
            InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"adm_rj_{user_id}")
        ]
    ])
    
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 <b>አዲስ የክፍያ ማረጋገጫ!</b>\n\n👤 ተጫዋች፦ {user_data['name']}\n🔢 ቁጥር፦ <b>ቁጥር {selected_num}</b>",
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
        await callback_query.answer("❌ ይህ ጥያቄ የለም ወይም ምላሽ አግኝቷል።")
        return
        
    user_data = pending_payments[target_user_id]
    chat_id = user_data["chat_id"]
    selected_num = user_data["num"]
    
    if chat_id not in active_games:
        active_games[chat_id] = {}
        
    active_games[chat_id][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    
    await bot.send_message(chat_id=target_user_id, text=f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {selected_num}</b> ለእርስዎ በትክክል ተመዝግቧል። መልካም ዕድል!", parse_mode="HTML")
    
    current_count = len(active_games[chat_id])
    await bot.send_message(
        chat_id=chat_id,
        text=f"📣 <b>የደስታ ዜና!</b>\n👤 <b>{user_data['name']}</b> ቁጥር <b>{selected_num}</b>ን በተሳካ ሁኔታ ገዝቷል።\n📊 የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>",
        parse_mode="HTML"
    )
    
    # 🔄 በዋናው ግሩፕ ላይ ሰሌዳው በሰዎች ስም ታድሶ እንዲወጣ ማድረግ
    try:
        updated_text = (
            "🎡 <b>እንኳን ወደ ዕድል እሽከርክሪት መድረክ በሰላም መጡ!</b> 🎡\n\n"
            "💵 <b>የአንድ ትኬት ዋጋ፦</b> 30 ብር\n"
            f"👥 <b>የተሸጡ ትኬቶች፦</b> {current_count}/10\n\n"
            "👇 ከታች ካለው ሰሌዳ ላይ የዕድል ቁጥርዎን በመምረጥ ይሳተፉ፦"
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
    
    if current_count >= 10:
        asyncio.create_task(start_spinning_effect(chat_id))

@dp.callback_query(F.data.startswith("adm_rj_"))
async def admin_reject_handler(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_CHAT_ID:
        await callback_query.answer("❌ ይህ ትዕዛዝ ለአስተዳዳሪው ብቻ የተፈቀደ ነው!", show_alert=True)
        return
        
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments:
        await callback_query.answer()
        return
        
    await bot.send_message(chat_id=target_user_id, text="❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b>\nየላኩት ስክሪንሾት ትክክለኛ አይደለም። እባክዎ በትክክል መክፈልዎን ያረጋግጡ።", parse_mode="HTML")
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption="❌ ይህ ክፍያ ውድቅ ተደርጓል።", reply_markup=None)

# 🛠 ልብ ሰቀላ የጽሑፍ አኒሜሽን ያለው የዕጣ አወጣጥ ክፍል
async def start_spinning_effect(chat_id: int):
    winner_number = str(random.randint(1, 10))
    
    msg = await bot.send_message(
        chat_id=chat_id, 
        text="🚨 <b>10ቱም ትኬቶች በሙሉ ተሽጠዋል! የዕድል እሽከርክሪቱ አሁን ይጀምራል...</b>", 
        parse_mode="HTML"
    )
    
    await asyncio.sleep(6)
    await msg.edit_text("🔄 <b>የዕድል መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🎰 SPINNING ]</b>", parse_mode="HTML")
    
    await asyncio.sleep(6)
    await msg.edit_text("⚡ <b>ፍጥነቱ ጨምሯል! ማንም ሊገምተው የማይችለው ሰዓት... አሸናፊው ማን ይሆን?</b>", parse_mode="HTML")
    
    await asyncio.sleep(6)
    await msg.edit_text("🎡 <b>መንኮራኩሩ ፍጥነቱን ቀስ በቀስ እየቀነሰ ነው... ወደ መቆሚያው እየተቃረበ ነው!</b>", parse_mode="HTML")
    
    await asyncio.sleep(6)
    await msg.edit_text("🎯 <b>አንድ ቁጥር ላይ ሊያርፍ ነው!... የመጨረሻ 5 ሰከንዶች!</b>", parse_mode="HTML")
    await asyncio.sleep(6)
    
    players = active_games.get(chat_id, {})
    winner_user = players.get(winner_number)
    
    if winner_user:
        result_text = (
            f"🎉 <b>ዕጣው በይፋ ወጥቷል! እንኳን ደስ አሎት!</b> 🎉\n\n"
            f"🎰 የዕድል መንኮራኩሩ ያረፈበት ቁጥር፦ <b>ቁጥር {winner_number}</b>\n"
            f"👑 የዚህ ዙር ሻምፒዮን፦ <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"💰 <b>የ 200 ብር</b> ሽልማትዎን ለመቀበል አሁኑኑ ለአስተዳዳሪው መልዕክት ይላኩ!"
        )
    else:
        result_text = (
            f"🎰 የዕድል መንኮራኩሩ ያረፈበት ቁጥር፦ <b>ቁጥር {winner_number}</b> ነበር።\n\n"
            f"😔 <b>የሚገርም ነው!</b> ይህንን ቁጥር በዚህ ዙር ማንም ስላልገዛው አሸናፊ የለም።\n"
            f"💰 የተሰበሰበው ገንዘብ በቀጥታ ወደ ሚቀጥለው ዙር ተላልፏል! አዲስ ዙር ለመጀመር /start ይበሉ።"
        )
        
    await msg.edit_text(text=result_text, parse_mode="HTML")
    active_games[chat_id] = {}

async def main():
    # በቴሌግራም ሜኑ ላይ የቦት ትዕዛዞችን በቋሚነት መመዝገብ
    await bot.set_my_commands([
        BotCommand(command="start", description="🕹️ ጨዋታውን ይጀምሩ / ማደሻ")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
