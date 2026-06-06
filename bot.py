import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 ዋና ዋና መረጃዎች
ADMIN_CHAT_ID = 1065443252  
TELEBIRR_NUMBER = "0920628769" 
TELEBIRR_NAME = "Tsige Tulu"
GROUP_LINK = "https://t.me/Yechewatamenkurakur" 

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 📊 የጨዋታ ክፍሎች መዋቅር
ROOMS = {
    "30": {"name": "🥉 የነሐስ ክፍል (30 ብር)", "price": 30, "max_players": 10, "prize": 250},
    "50": {"name": "🥈 የብር ክፍል (50 ብር)", "price": 50, "max_players": 5, "prize": 200},
    "100": {"name": "🥇 የወርቅ ክፍል (100 ብር)", "price": 100, "max_players": 5, "prize": 400}
}

# 🗄️ በGitHub ላይ ብቻ የሚቀመጡ የውስጥ ዳታቤዞች
active_games = {"30": {}, "50": {}, "100": {}} 
pending_payments = {} 

user_wallets = {}     
user_play_counts = {} 
referred_users = {}   # {"የተጋበዘው_id": "የጋባዡ_id"}
rewarded_referrals = set() # 🛑 አንድ ሰው ከአንድ ሰው በላይ ድጋሚ ኮሚሽን እንዳይበላ መከላከያ

def check_and_create_user(user_id: int):
    if user_id not in user_wallets:
        user_wallets[user_id] = 0.0
    if user_id not in user_play_counts:
        user_play_counts[user_id] = 0

# --- 📱 የቁልፍ ሰሌዳዎች (Keyboards) ---

def generate_rooms_keyboard():
    buttons = []
    for room_id, info in ROOMS.items():
        current_count = len(active_games[room_id])
        text = f"{info['name']} - [{current_count}/{info['max_players']}]"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"select_room_{room_id}")])
    
    buttons.append([
        InlineKeyboardButton(text="💳 የእኔ ዋሌት", callback_data="view_wallet"),
        InlineKeyboardButton(text="👥 ሰዎችን ጋብዝ", callback_data="view_ref")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def generate_numbers_keyboard(room_id: str):
    game = active_games[room_id]
    max_players = ROOMS[room_id]["max_players"]
    buttons = []
    row = []
    
    for i in range(1, max_players + 1):
        num_str = str(i)
        if num_str in game:
            text = f"🔴 {i}"
            callback_data = f"already_sold_{room_id}_{i}"
        else:
            text = f"🟢 ቁጥር {i}"
            callback_data = f"buy_{room_id}_{i}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0 or i == max_players: 
            buttons.append(row)
            row = []
            
    buttons.append([InlineKeyboardButton(text="🔙 ወደ ክፍሎች ተመለስ", callback_data="back_to_rooms")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_player_list_text(room_id: str):
    game = active_games[room_id]
    info = ROOMS[room_id]
    list_text = f"<b>📊 የ{info['name']} ተሳታፊዎች ዝርዝር፦</b>\n"
    list_text += "━━━━━━━━━━━━━━━━━━━\n"
    for i in range(1, info["max_players"] + 1):
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
    
    # 👥 የሪፈራል ትስስር ማስታወሻ መያዣ (ብር እዚህ ጋር አይጨመርም!)
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        if referrer_id != user_id and user_id not in referred_users:
            referred_users[user_id] = referrer_id

    welcome_text = (
        "💎 <b>እንኳን ወደ ዕድል እሽከርክሪት ማዕከል በሰላም መጡ!</b> 💎\n\n"
        "👇 እባክዎ መጫወት የሚፈልጉትን የጨዋታ ክፍል ይምረጡ፦"
    )
    await message.answer(text=welcome_text, reply_markup=generate_rooms_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data == "back_to_rooms")
async def back_to_rooms_handler(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text("👇 እባክዎ መጫወት የሚፈልጉትን የጨዋታ ክፍል ይምረጡ፦", reply_markup=generate_rooms_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("select_room_"))
async def select_room_handler(callback_query: types.CallbackQuery):
    room_id = callback_query.data.split("_")[2]
    info = ROOMS[room_id]
    current_count = len(active_games[room_id])
    
    welcome_text = (
        f"<b>⚙️ {info['name']}</b>\n\n"
        f"💰 <b>የትኬት ዋጋ፦</b> <code>{info['price']} ብር</code>\n"
        f"🏆 <b>የአሸናፊው ሽልማት፦</b> <b>{info['prize']} ብር በቀጥታ!</b>\n"
        f"👥 <b>የተሸጡ ትኬቶች፦</b> 📊 <b>{current_count}/{info['max_players']}</b>\n\n"
        f"{get_player_list_text(room_id)}\n\n"
        "👇 ክፍት የሆነ የዕድል ቁጥር ይምረጡ፦"
    )
    await callback_query.answer()
    await callback_query.message.edit_text(text=welcome_text, reply_markup=generate_numbers_keyboard(room_id), parse_mode="HTML")

# --- 🎰 የቁጥር መግዣ እና የክፍያ ሂደት ---

@dp.callback_query(F.data.startswith("buy_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    room_id = parts[1]
    selected_num = parts[2]
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    info = ROOMS[room_id]
    
    if selected_num in active_games[room_id]:
        await callback_query.answer("❌ ይቅርታ፣ ይህ ቁጥር አሁን በሌላ ሰው ተገዝቷል!", show_alert=True)
        await callback_query.message.edit_reply_markup(reply_markup=generate_numbers_keyboard(room_id))
        return

    if user_id in pending_payments:
        await callback_query.answer("⚠️ ቀደም ሲል የላኩት ክፍያ ማረጋገጫ በሂደት ላይ ነው!", show_alert=True)
        return

    await callback_query.answer()
    
    payment_instruction = (
        f"✨ <b>የክፍያ ማረጋገጫ ፎርም</b> ✨\n\n"
        f"🎪 <b>ክፍል፦</b> {info['name']}\n"
        f"🎯 <b>የመረጡት ቁጥር፦</b> <b>ቁጥር {selected_num}</b>\n"
        f"💰 <b>የሚከፍሉት መጠን፦</b> <code>{info['price']} ብር</code>\n\n"
        f"📱 <b>የቴሌብር ቁጥር፦</b> <code>{TELEBIRR_NUMBER}</code>\n"
        f"👤 <b>ስም፦</b> {TELEBIRR_NAME}\n\n"
        f"📸 እባክዎ ክፍያውን ፈጽመው ሲጨርሱ <b>የክፍያውን ስክሪንሾት (Screenshot) ፎቶ</b> ብቻ እዚህ ላይ ይላኩ።"
    )
    
    pending_payments[user_id] = {"num": selected_num, "room": room_id, "name": username}
    await callback_query.message.answer(payment_instruction, parse_mode="HTML")

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ተሽጧል! እባክዎ ሌላ ክፍት ቁጥር ይምረጡ።", show_alert=True)

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    if user_id not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ቁጥር ይምረጡ፤ ከዚያ ፎቶ ይላኩ።")
        return
        
    user_data = pending_payments[user_id]
    info = ROOMS[user_data['room']]
    
    await message.reply("📥 <b>የክፍያ ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ እስኪመዘገብ እባክዎ ይጠብቁ! 🕒</b>", parse_mode="HTML")
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"adm_ap_{user_id}"),
            InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"adm_rj_{user_id}")
        ]
    ])
    
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 <b>አዲስ ክፍያ!</b>\n\n👤 <b>ተጫዋች፦</b> {user_data['name']}\n🎪 <b>ክፍል፦</b> {info['name']}\n🔢 <b>ቁጥር፦</b> <b>ቁጥር {user_data['num']}</b>",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

# --- 👑 የአድሚን ማጽደቂያ፣ የታማኝነት ጉርሻ እና የሪፈራል ክፍያ ---

@dp.callback_query(F.data.startswith("adm_ap_"))
async def admin_approve_handler(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != ADMIN_CHAT_ID:
        await callback_query.answer("❌ ይህ ትዕዛዝ ለአስተዳዳሪው ብቻ ነው!", show_alert=True)
        return
        
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments:
        await callback_query.answer("❌ ይህ ጥያቄ ቀደም ብሎ ምላሽ አግኝቷል።")
        return
        
    user_data = pending_payments[target_user_id]
    room_id = user_data["room"]
    selected_num = user_data["num"]
    info = ROOMS[room_id]
    
    active_games[room_id][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    
    check_and_create_user(target_user_id)
    user_play_counts[target_user_id] += 1  
    
    # 👥 💰 የሪፈራል ክፍያ ማረጋገጫ (ከተከፈለ በኋላ ብቻ የሚሰጥ)
    ref_text = ""
    if target_user_id in referred_users and target_user_id not in rewarded_referrals:
        referrer_id = referred_users[target_user_id]
        check_and_create_user(referrer_id)
        
        user_wallets[referrer_id] += 3.0 # ለጋባዡ 3 ብር ኮሚሽን አሁን ተጨመረ!
        rewarded_referrals.add(target_user_id) # ምልክት ይደረግበታል (ድጋሚ እንዳይከፈል)
        
        try:
            await bot.send_message(
                chat_id=referrer_id,
                text=f"🎁 <b>የአፍሊየት ኮሚሽን ገቢ!</b> የጋበዙት ሰው (<code>{user_data['name']}</code>) የመጀመሪያ ጨዋታውን ስለተጫወተ <b>3 ብር</b> ዋሌትዎ ላይ በስኬት ተጨምሯል!",
                parse_mode="HTML"
            )
        except Exception:
            pass
    
    # 🎖️ የታማኝነት ጉርሻ (Loyalty)
    loyalty_text = ""
    if user_play_counts[target_user_id] % 5 == 0:
        user_wallets[target_user_id] += 10.0
        loyalty_text = f"\n\n🎁 <b>ልዩ የታማኝነት ስጦታ፦</b> ይህ <code>{user_play_counts[target_user_id]}ኛው</code> ጨዋታዎ ስለሆነ <b>10 ብር</b> ዋሌትዎ ላይ ተጨምሯል!"
    
    back_to_group_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃‍♂️ ወደ ግሩፑ ተመለስ", url=GROUP_LINK)]
    ])
    
    await bot.send_message(
        chat_id=target_user_id, 
        text=f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {selected_num}</b> በ{info['name']} ተመዝግቧል።{loyalty_text}", 
        reply_markup=back_to_group_kb,
        parse_mode="HTML"
    )
    
    current_count = len(active_games[room_id])
    
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID, 
            text=f"📣 <b>የደስታ ዜና!</b>\n👤 <b>{user_data['name']}</b> በ{info['name']} ቁጥር <b>{selected_num}</b>ን በይፋ ገዝቷል።\n📊 የተሸጡ ትኬቶች፦ <b>{current_count}/{info['max_players']}</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
        
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption=f"✅ ተፈቅዷል! ቁጥር {selected_num} ተመዝግቧል።", reply_markup=None)
    
    if current_count >= info["max_players"]:
        await start_spinning_effect(ADMIN_CHAT_ID, room_id)

@dp.callback_query(F.data.startswith("adm_rj_"))
async def admin_reject_handler(callback_query: types.CallbackQuery):
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments: return
    await bot.send_message(chat_id=target_user_id, text="❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b>\nየላኩት ስክሪንሾት ትክክለኛ አይደለም።", parse_mode="HTML")
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption="❌ ይህ ክፍያ ውድቅ ተደርጓል።", reply_markup=None)

# --- 🎡 አውቶሜትድ የዕድል እሽከርክሪት ---

async def start_spinning_effect(chat_id: int, room_id: str):
    info = ROOMS[room_id]
    winner_number = str(random.randint(1, info["max_players"]))
    
    msg = await bot.send_message(chat_id=chat_id, text=f"🚨 <b>የ{info['name']} ሁሉም ትኬቶች ተሽጠዋል! የዕድል መንኮራኩሩ አሁን ይጀምራል...</b>", parse_mode="HTML")
    await asyncio.sleep(2)
    await msg.edit_text("🔄 <b>የዕድል መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🎰 SPINNING ]</b>", parse_mode="HTML")
    await asyncio.sleep(2)
    
    players = active_games[room_id]
    winner_user = players.get(winner_number)
    
    if winner_user:
        result_text = (
            f"🎆✨🎉 <b>እጣው በይፋ ወጥቷል! ({info['name']})</b> 🎉✨🎆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎰 <b>የመጣው የዕድል ቁጥር፦</b> <b>ቁጥር {winner_number}</b>\n\n"
            f"👑 <b>የዚህ ዙር ታላቅ ሻምፒዮን፦</b> <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>የ {info['prize']} ብር</b> የሽልማት ገንዘብዎ በቴሌብር ይላክሎታል። እንኳን ደስ አለዎት! 🎁"
        )
    else:
        result_text = f"🎰 ያረፈበት ቁጥር፦ <b>ቁጥር {winner_number}</b> ነበር። ግን ማንም ስላልገዛው አሸናፊ የለም።"
        
    await msg.edit_text(text=result_text, parse_mode="HTML")
    active_games[room_id] = {} 

# --- 💳 ዋሌት እና ሪፈራል እይታ ---

@dp.callback_query(F.data == "view_wallet")
async def view_wallet_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    check_and_create_user(user_id)
    wallet_text = (
        f"💳 <b>የእርስዎ ዲጂታል ዋሌት</b>\n\n"
        f"💰 <b>ያለዎት የሪፈራል ባላንስ፦</b> <code>{user_wallets[user_id]} ETB</code>\n"
        f"🎮 <b>በጠቅላላ የተጫወቱት ብዛት፦</b> <code>{user_play_counts[user_id]} ጊዜ</code>"
    )
    await callback_query.answer()
    await callback_query.message.answer(wallet_text, parse_mode="HTML")

@dp.callback_query(F.data == "view_ref")
async def view_ref_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    bot_info = await bot.get_me()
    total_referred = list(referred_users.values()).count(user_id)
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    
    ref_text = (
        f"🤝 <b>የመጋበዣ (Affiliate) ማዕከል</b>\n\n"
        f"👥 <b>የጋበዟቸው ሰዎች ብዛት፦</b> <code>{total_referred} ሰው</code>\n"
        f"🎁 <b>የግብዣ ስጦታ፦</b> የጋበዙት ሰው መጥቶ <u>የመጀመሪያ ጨዋታውን ሲጫወት</u> <b>3 ብር</b> ያገኛሉ!\n\n"
        f"🔗 <b>የመጋበዣ ሊንክዎ፦</b>\n<code>{ref_link}</code>"
    )
    await callback_query.answer()
    await callback_query.message.answer(ref_text, parse_mode="HTML")

@dp.message()
async def block_other_messages(message: types.Message):
    if message.chat.type == "private":
        await message.reply("⚠️ እባክዎ የክፍያ ስክሪንሾት (የፎቶ ፋይል) ብቻ ይላኩ።")

async def main():
    await bot.set_my_commands([BotCommand(command="start", description="🕹️ ጨዋታውን ይጀምሩ")])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
