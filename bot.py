import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 ዋና ዋና መረጃዎች
ADMIN_CHAT_ID = 1065443252  
TELEBIRR_NUMBER = "+251913064239" 
GROUP_LINK = "https://t.me/Yechewatamenkurakur" # 🔗 የቴሌግራም ግሩፕህ ሊንክ እዚህ ይግባ

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🗄️ በGitHub ላይ ብቻ የሚቀመጡ የውስጥ ዳታቤዞች (In-Memory Database)
GAME_ROOM_ID = "main_game"
active_games = {GAME_ROOM_ID: {}}     
pending_payments = {} # {"user_id": {"num":..., "name":...}}

# 👥 አዲስ የተጨመሩ የዋሌት እና የሪፈራል ማከማቻዎች
user_wallets = {}     # {"user_id": balance_amount}
user_play_counts = {} # {"user_id": total_games_played}
referred_users = {}   # {"user_id": referrer_id}

# --- 🛠️ አዳዲስ የረዳት ተግባራት (Helper Functions) ---

def check_and_create_user(user_id: int):
    """ተጫዋቹ በሲስተሙ ከሌለ ዋሌትና የጨዋታ አካውንት ይከፍታል"""
    if user_id not in user_wallets:
        user_wallets[user_id] = 0.0
    if user_id not in user_play_counts:
        user_play_counts[user_id] = 0

# --- 📱 የቁልፍ ሰሌዳዎች (Keyboards) ---

def generate_keyboard():
    """ሁልጊዜ ከዋናው ዳታቤዝ ጋር የተመሳሰለ የቁጥሮች ሰሌዳ ያመነጫል"""
    game = active_games[GAME_ROOM_ID]
    buttons = []
    row = []
    for i in range(1, 11):
        num_str = str(i)
        if num_str in game:
            text = f"🔴 ቁጥር {i} (ተሽጧል)"
            callback_data = f"already_sold_{i}"
        else:
            text = f"🟢 ቁጥር {i}"
            callback_data = f"buy_num_{i}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0: 
            buttons.append(row)
            row = []
            
    # የዋሌት እና የሪፈራል በተኖችን ከሰሌዳው ስር ማካተት
    buttons.append([
        InlineKeyboardButton(text="💳 የእኔ ዋሌት", callback_data="view_wallet"),
        InlineKeyboardButton(text="👥 ሰዎችን ጋብዝ", callback_data="view_ref")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_player_list_text():
    """ወቅታዊ የተጫዋቾችን ዝርዝር ያሳያል"""
    game = active_games[GAME_ROOM_ID]
    list_text = "<b>📊 የእድለኛ ተሳታፊዎች ወቅታዊ ዝርዝር፦</b>\n"
    list_text += "━━━━━━━━━━━━━━━━━━━\n"
    for i in range(1, 11):
        num_str = str(i)
        if num_str in game:
            list_text += f" {i} 🔴 <b>{game[num_str]['name']}</b>\n"
        else:
            list_text += f" {i} 🔓 <i>ነጻ ቁጥር (ክፍት)</i>\n"
    list_text += "━━━━━━━━━━━━━━━━━━━"
    return list_text

# --- 🚀 የቦቱ ትዕዛዞች (Handlers) ---

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    # ሴኩሪቲ፦ ይህ ጨዋታ የሚካሄደው በቦቱ የውስጥ መስмер ብቻ ነው
    if message.chat.type != "private":
        bot_info = await bot.get_me()
        bot_link = f"https://t.me/{bot_info.username}?start=play"
        await message.answer(
            f"🎡 <b>ወደ ዕድል እሽከርክሪት ጨዋታ ለመግባት ከታች ያለውን በተን ይጫኑ፦</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🕹️ አሁኑኑ ተጫወት", url=bot_link)]
            ]),
            parse_mode="HTML"
        )
        return

    user_id = message.from_user.id
    check_and_create_user(user_id)
    
    # 👥 የሪፈራል/ግብዣ ሊንክ ትንተና
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        
        # አንድ ሰው ራሱን እንዳይጋብዝ እና ድጋሚ እንዳይመዘገብ መከላከያ
        if referrer_id != user_id and user_id not in referred_users:
            referred_users[user_id] = referrer_id
            check_and_create_user(referrer_id)
            
            # ለጋባዡ የ 5 ብር የሪፈራል ኮሚሽን በቅጽበት መስጠት
            user_wallets[referrer_id] += 5.0
            try:
                await bot.send_message(
                    chat_id=referrer_id,
                    text=f"🎁 <b>የአፍሊየት ሽልማት!</b> የጋበዙት ሰው <code>{message.from_user.full_name}</code> ቦቱን ስለቀላቀለ <b>5 ብር</b> ዋሌትዎ ላይ ተጨምሯል!",
                    parse_mode="HTML"
                )
            except Exception:
                pass

    current_count = len(active_games[GAME_ROOM_ID])
    welcome_text = (
        "💎 <b>እንኳን ወደ ዕድል እሽከርክሪት ማዕከል በሰላም መጡ!</b> 💎\n\n"
        f"💰 <b>የአንድ ትኬት ዋጋ፦</b> <code>30 ብር</code>\n"
        f"🏆 <b>የአሸናፊው ሽልማት፦</b> <b>200 ብር በቀጥታ!</b>\n"
        f"👥 <b>የተሸጡ ትኬቶች፦</b> 📊 <b>{current_count}/10</b>\n\n"
        f"{get_player_list_text()}\n\n"
        "👇 እባክዎ ከታች ያለውን ሰሌዳ በመጠቀም ክፍት የሆነ የዕድል ቁጥር ይምረጡ፦"
    )
    await message.answer(text=welcome_text, reply_markup=generate_keyboard(), parse_mode="HTML")

# --- 💳 የዋሌት እና ሪፈራል በተኖች መቆጣጠሪያ ---

@dp.callback_query(F.data == "view_wallet")
async def view_wallet_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    check_and_create_user(user_id)
    
    wallet_text = (
        f"💳 <b>የእርስዎ ዲጂታል ዋሌት (Wallet)</b> 💳\n\n"
        f"💰 <b>ያለዎት የገንዘብ መጠን፦</b> <code>{user_wallets[user_id]} ETB</code>\n"
        f"🎮 <b>በጠቅላላ የተጫወቱት ብዛት፦</b> <code>{user_play_counts[user_id]} ጊዜ</code>\n\n"
        f"💡 <i>ማሳሰቢያ፦ ከሪፈራል ያገኙትን ኮሚሽን ለጨዋታ መክፈያነት መጠቀም ይችላሉ!</i>"
    )
    await callback_query.answer()
    await callback_query.message.answer(wallet_text, parse_mode="HTML")

@dp.callback_query(F.data == "view_ref")
async def view_ref_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    bot_info = await bot.get_me()
    
    # ስንት ሰው እንደጋበዘ መቁጠሪያ
    total_referred = list(referred_users.values()).count(user_id)
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    ref_text = (
        f"🤝 <b>የእርስዎ የመጋበዣ (Affiliate) ማዕከል</b> 🤝\n\n"
        f"👥 <b>እስካሁን የጋበዟቸው ሰዎች ብዛት፦</b> <code>{total_referred} ሰው</code>\n"
        f"🎁 <b>የግብዣ ስጦታ፦</b> ለእያንዳንዱ በእርስዎ ሊንክ ለሚገባ አዲስ ሰው <b>5 ብር</b> ያገኛሉ!\n\n"
        f"🔗 <b>የእርስዎ ልዩ መጋበዣ ሊንክ፦</b>\n<code>{ref_link}</code>\n\n"
        f"📢 ይህንን ሊንክ ለጓደኞችዎ በመላክ ወይም ግሩፖች ላይ በማጋራት በነጻ የዋሌት ባላንስ ይሰብስቡ!"
    )
    await callback_query.answer()
    await callback_query.message.answer(ref_text, parse_mode="HTML")

# --- 🎰 የቁጥር መግዣ እና የክፍያ ሂደት ---

@dp.callback_query(F.data.startswith("buy_num_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    selected_num = callback_query.data.split("_")[2]
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    if selected_num in active_games[GAME_ROOM_ID]:
        await callback_query.answer("❌ ይቅርታ፣ ይህ ቁጥር አሁን በሌላ ሰው ተገዝቷል! እባክዎ ሌላ ይምረጡ።", show_alert=True)
        await callback_query.message.edit_reply_markup(reply_markup=generate_keyboard())
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
        f"📸 እባክዎ ክፍያውን ፈጽመው ሲጨርሱ <b>የክፍያውን ስክሪንሾት (Screenshot) ፎቶ</b> ብቻ እዚህ ላይ ይላኩ።"
    )
    
    pending_payments[user_id] = {"num": selected_num, "name": username}
    await callback_query.message.answer(payment_instruction, parse_mode="HTML")

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ቀደም ብሎ ተሽጧል! እባክዎ ሌላ አረንጓዴ ቁጥር ይምረጡBlock።", show_alert=True)

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    if user_id not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ቁጥር ይምረጡ፤ ከዚያ የስክሪንሾት ፎቶ ይላኩ።")
        return
        
    user_data = pending_payments[user_id]
    selected_num = user_data["num"]
    
    await message.reply(
        "📥 <b>የክፍያ ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ እስኪመዘገብ እባክዎ በትዕግስት ይጠብቁ! 🕒</b>", 
        parse_mode="HTML"
    )
    
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

@dp.message()
async def block_other_messages(message: types.Message):
    if message.chat.type == "private":
        await message.reply("⚠️ እባክዎ የክፍያ ስክሪንሾት (የፎቶ ፋይል) ብቻ ይላኩ። ሌላ አይነት ፋይል ወይም ጽሑፍ ሲስተሙ አይቀበልም።")

# --- 👑 የአድሚን ማጽደቂያ እና የታማኝነት ጉርሻ (Loyalty Bonus) ---

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
    selected_num = user_data["num"]
    
    # 🎰 የጨዋታውን ቁጥር መቆለፍ
    active_games[GAME_ROOM_ID][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    
    # 🎖️ የታማኝነት ጉርሻ (Loyalty Logic)
    check_and_create_user(target_user_id)
    user_play_counts[target_user_id] += 1  # የጨዋታ ብዛቱን 1 እንጨምራለን
    
    loyalty_text = ""
    # ተጫዋቹ በየ 5 ጊዜ በተጫወተ ቁጥር የ 10 ብር የዋሌት ስጦታ በራስ-ሰር ያገኛል!
    if user_play_counts[target_user_id] % 5 == 0:
        user_wallets[target_user_id] += 10.0
        loyalty_text = f"\n\n🎁 <b>ልዩ የታማኝነት ስጦታ፦</b> ስለደጋገሙ ስሪት ያደረጉት ይህ <code>{user_play_counts[target_user_id]}ኛው</code> ጨዋታዎ ስለሆነ <b>10 ብር</b> በራስ-ሰር ዋሌትዎ ላይ ተጨምሯል!"
    
    back_to_group_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃‍♂️ ወደ ግሩፑ ተመለስ", url=GROUP_LINK)]
    ])
    
    await bot.send_message(
        chat_id=target_user_id, 
        text=f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {selected_num}</b> በስምዎ ተመዝግቧል። አሁኑኑ ወደ ግሩፑ በመመለስ የጨዋታውን ሂደት ይከታተሉ! 🍀{loyalty_text}", 
        reply_markup=back_to_group_kb,
        parse_mode="HTML"
    )
    
    current_count = len(active_games[GAME_ROOM_ID])
    
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID, # ግሩፕህ ውስጥ ቦቱን አድሚን አድርገህ እዚህ ላይ የግሩፕህን ID መተካት ትችላለህ
            text=f"📣 <b>የደስታ ዜና!</b>\n👤 <b>{user_data['name']}</b> ቁጥር <b>{selected_num}</b>ን በይፋ ገዝቷል።\n📊 የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
        
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption=f"✅ ተፈቅዷል! ቁጥር {selected_num} ተመዝግቧል።", reply_markup=None)
    
    if current_count >= 10:
        await start_spinning_effect(ADMIN_CHAT_ID) # እጣ ማውጫውን ማስነሳት

@dp.callback_query(F.data.startswith("adm_rj_"))
async def admin_reject_handler(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_CHAT_ID:
        await callback_query.answer("❌ ይህ ትዕዛዝ ለአስተዳዳሪው ብቻ የተፈቀደ ነው!", show_alert=True)
        return
        
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments:
        await callback_query.answer()
        return
        
    await bot.send_message(chat_id=target_user_id, text="❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b>\nየላኩት ስክሪንሾት ትክክለኛ አይደለም።", parse_mode="HTML")
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption="❌ ይህ ክፍያ ውድቅ ተደርጓል።", reply_markup=None)

# --- 🎡 አውቶሜትድ የዕድል እሽከርክሪት (የቀድሞው ውጤታማ አሰራር) ---

async def start_spinning_effect(chat_id: int):
    winner_number = str(random.randint(1, 10))
    large_numbers = {"1": "️⃣1️⃣", "2": "️⃣2️⃣", "3": "️⃣3️⃣", "4": "️⃣4️⃣", "5": "️⃣5️⃣", "6": "️⃣6️⃣", "7": "️⃣7️⃣", "8": "️⃣8️⃣", "9": "️⃣9️⃣", "10": "🔟"}
    big_num = large_numbers.get(winner_number, winner_number)

    msg = await bot.send_message(chat_id=chat_id, text="🚨 <b>10ቱም ትኬቶች ተሽጠዋል! የዕድል መንኮራኩሩ አሁን ይጀምራል...</b>", parse_mode="HTML")
    await asyncio.sleep(2)
    await msg.edit_text("🔄 <b>የዕድል መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🎰 SPINNING ]</b>", parse_mode="HTML")
    await asyncio.sleep(2)
    
    players = active_games[GAME_ROOM_ID]
    winner_user = players.get(winner_number)
    
    if winner_user:
        result_text = (
            f"🎆✨🎉 <b>እጣው በይፋ ወጥቷል!</b> 🎉✨🎆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎰 <b>የመጣው የዕድል ቁጥር፦</b>\n"
            f"⚡️⚡️  <b>{big_num}</b>  ⚡️⚡️\n\n"
            f"👑 <b>የዚህ ዙር ታላቅ ሻምፒዮን፦</b> <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>የ 200 ብር</b> የሽልማት ገንዘብዎ በቀጥታ ይላክሎታል። እንኳን ደስ አለዎት! 🎁"
        )
    else:
        result_text = f"🎰 ያረፈበት ቁጥር፦ <b>{big_num}</b> ነበር። ግን ማንም ስላልገዛው አሸናፊ የለም።"
        
    await msg.edit_text(text=result_text, parse_mode="HTML")
    active_games[GAME_ROOM_ID] = {} # ጨዋታውን ለቀጣይ ዙር ማጽዳት

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="🕹️ ጨዋታውን ይጀምሩ")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
