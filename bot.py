import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 1065443252  # ያንተ የቴሌግራም መታወቂያ ቁጥር

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🎰 በጊዜያዊ ሚሞሪ ላይ የሚቀመጥ የጨዋታ መረጃ
active_games = {}     # {group_chat_id: { "ቁጥር": {"user_id":..., "name":...} }}
pending_payments = {} # {user_id: {"num":..., "group_id":..., "name":...}}

def generate_keyboard(group_id: int):
    """የቁጥሮችን ወቅታዊ ሁኔታ ያሳያል"""
    game = active_games.get(group_id, {})
    buttons = []
    row = []
    for i in range(1, 11):
        num_str = str(i)
        if num_str in game:
            text = f"🔴 {i} (ተያዟል)"
            callback_data = f"sold_{i}"
        else:
            text = f"🟢 ቁጥር {i}"
            callback_data = f"buy_{i}_{group_id}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0: 
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    # በግል መስመር ከሆነ መመሪያ ያሳያል
    if message.chat.type == "private":
        help_text = (
            "👋 <b>እንኳን ወደ ዕድል እሽከርክሪት ቦት በሰላም መጡ!</b>\n\n"
            "🎰 ጨዋታውን ለመጫወት መጀመሪያ ቦቱ ወዳለበት <b>የቴሌግራም ግሩፕ</b> ይሂዱ።\n"
            "ግሩፑ ውስጥ ገብተው /game ሲሉ የቁጥር ሰሌዳው ይወጣሎታል።"
        )
        await message.answer(help_text, parse_mode="HTML")
        return

@dp.message(Command("game"))
async def game_command_handler(message: types.Message):
    """ግሩፕ ውስጥ ጨዋታውን መጀሪያ ቁልፍ"""
    group_id = message.chat.id
    if group_id not in active_games:
        active_games[group_id] = {}
        
    current_count = len(active_games[group_id])
    welcome_text = (
        "🎡 <b>የዕድል እሽከርክሪት ጨዋታ ተጀምሯል!</b> 🎡\n\n"
        "💰 <b>የአንድ ትኬት ዋጋ፦</b> <code>30 ብር</code>\n"
        "🏆 <b>የአሸናፊው ሽልማት፦</b> <b>200 ብር በቀጥታ!</b>\n"
        f"📊 <b>የተሸጡ ትኬቶች፦</b> <b>{current_count}/10</b>\n\n"
        "👇 እባክዎ ከታች ካለው ሰሌዳ ላይ አንድ ክፍት የዕድል ቁጥር ይምረጡ፦"
    )
    await message.answer(text=welcome_text, reply_markup=generate_keyboard(group_id), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    selected_num = parts[1]
    group_id = int(parts[2])
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    # ቁጥሩ ድጋሚ መያዙን ቼክ ማድረግ
    if selected_num in active_games.get(group_id, {}):
        await callback_query.answer("❌ ይቅርታ፣ ይህ ቁጥር አሁን በሌላ ሰው ተገዝቷል!", show_alert=True)
        return

    await callback_query.answer()
    
    # ለተጫዋቹ በውስጥ መስመር የክፍያ መመሪያ መላክ
    payment_instruction = (
        f"✨ <b>የክፍያ ማረጋገጫ ፎርም</b> ✨\n\n"
        f"🎯 <b>የመረጡት ቁጥር፦</b> <b>ቁጥር {selected_num}</b>\n"
        f"💰 <b>የሚከፍሉት መጠን፦</b> <code>30 ብር</code>\n"
        f"📱 <b>የቴሌብር ቁጥር፦</b> <code>+251913064239</code>\n\n"
        f"📸 እባክዎ ክፍያውን ፈጽመው ሲጨርሱ <b>የክፍያውን ስክሪንሾት (Screenshot) ፎቶ</b> እዚህ ላይ ይላኩ።"
    )
    
    pending_payments[user_id] = {"num": selected_num, "group_id": group_id, "name": username}
    
    try:
        await bot.send_message(chat_id=user_id, text=payment_instruction, parse_mode="HTML")
        await callback_query.message.answer(f"📩 <b>{username}</b> የክፍያ መመሪያው በውስጥ መስመር (DM) ተልኮልዎታል። እባክዎ ቼክ ያድርጉ!")
    except Exception:
        await callback_query.message.answer(f"⚠️ <b>{username}</b> ቦቱን በመጀመሪያ Start አላደረጉትም። እባክዎ @your_bot_username ላይ ገብተው Start ይበሉ!")

@dp.callback_query(F.data.startswith("sold_"))
async def sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ተሽጧል! እባክዎ ሌላ ይምረጡ።", show_alert=True)

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    if user_id not in pending_payments:
        return
        
    user_data = pending_payments[user_id]
    
    await message.reply("📥 <b>ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ እስኪመዘገብ እባክዎ በትዕግስት ይጠብቁ! 🕒</b>", parse_mode="HTML")
    
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"adm_ap_{user_id}"),
            InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"adm_rj_{user_id}")
        ]
    ])
    
    await bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=message.photo[-1].file_id,
        caption=f"🔔 <b>አዲስ ክፍያ!</b>\n👤 <b>ተጫዋች፦</b> {user_data['name']}\n🔢 <b>ቁጥር፦</b> {user_data['num']}",
        reply_markup=admin_keyboard,
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("adm_ap_"))
async def admin_approve_handler(callback_query: types.CallbackQuery):
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments:
        await callback_query.answer("❌ ይህ ጥያቄ ቀደም ብሎ ምላሽ አግኝቷል።")
        return
        
    user_data = pending_payments[target_user_id]
    group_id = user_data["group_id"]
    selected_num = user_data["num"]
    
    active_games[group_id][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    current_count = len(active_games[group_id])
    
    await bot.send_message(chat_id=target_user_id, text=f"🎉 ክፍያዎ ተረጋግጧል! <b>ቁጥር {selected_num}</b> በስምዎ ተመዝግቧል። መልካም እድል! 🍀", parse_mode="HTML")
    await bot.send_message(chat_id=group_id, text=f"📣 <b>{user_data['name']}</b> ቁጥር <b>{selected_num}</b>ን ገዝቷል!\n📊 የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>", parse_mode="HTML")
    
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption=f"✅ ተፈቅዷል! ቁጥር {selected_num} ተመዝግቧል።", reply_markup=None)
    
    if current_count >= 10:
        await start_spinning_effect(group_id)

@dp.callback_query(F.data.startswith("adm_rj_"))
async def admin_reject_handler(callback_query: types.CallbackQuery):
    target_user_id = int(callback_query.data.split("_")[2])
    if target_user_id not in pending_payments:
        return
    await bot.send_message(chat_id=target_user_id, text="❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b> እባክዎ ትክክለኛውን ስክሪንሾት እንደገና ይላኩ።", parse_mode="HTML")
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption="❌ ይህ ክፍያ ውድቅ ተደርጓል።", reply_markup=None)

async def start_spinning_effect(group_chat_id: int):
    """የርችት ድምቀት ያለው አውቶሜትድ እጣ ማውጫ"""
    winner_number = str(random.randint(1, 10))
    large_numbers = {"1": "️⃣1️⃣", "2": "️⃣2️⃣", "3": "️⃣3️⃣", "4": "️⃣4️⃣", "5": "️⃣5️⃣", "6": "️⃣6️⃣", "7": "️⃣7️⃣", "8": "️⃣8️⃣", "9": "️⃣9️⃣", "10": "🔟"}
    big_num = large_numbers.get(winner_number, winner_number)

    msg = await bot.send_message(chat_id=group_chat_id, text="🚨 <b>10ቱም ትኬቶች ተሽጠዋል! የዕድል መንኮራኩሩ አሁን ይጀምራል...</b>", parse_mode="HTML")
    await asyncio.sleep(3)
    await msg.edit_text("🔄 <b>የዕድል መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🎰 SPINNING ]</b>", parse_mode="HTML")
    await asyncio.sleep(3)
    await msg.edit_text("🎡 <b>መንኮራኩሩ ፍጥነቱን ቀስ በቀስ እየቀነሰ ነው... 👀</b>", parse_mode="HTML")
    await asyncio.sleep(3)
    
    players = active_games.get(group_chat_id, {})
    winner_user = players.get(winner_number)
    
    if winner_user:
        result_text = (
            f"🎆✨🎉 <b>እጣው በይፋ ወጥቷል!</b> 🎉✨🎆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎰 <b>የመጣው የዕድል ቁጥር፦</b>\n"
            f"👇 👇 👇 👇 👇 👇 👇\n"
            f"✨✨✨✨✨✨✨✨✨\n"
            f"⚡️⚡️  <b>{big_num}</b>  ⚡️⚡️\n"
            f"✨✨✨✨✨✨✨✨✨\n\n"
            f"👑 <b>የዚህ ዙር ታላቅ ሻምፒዮን፦</b> <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>የ 200 ብር</b> የሽልማት ገንዘብዎ በቀጥታ ይላክሎታል። እንኳን ደስ አለዎት! 🎁"
        )
    else:
        result_text = f"🎰 ያረፈበት ቁጥር፦ <b>{big_num}</b> ነበር። ግን ማንም ስላልገዛው አሸናፊ የለም።"
        
    await msg.edit_text(text=result_text, parse_mode="HTML")
    active_games[group_chat_id] = {}

async def main():
    await bot.set_my_commands([BotCommand(command="game", description="🎰 ጨዋታውን ይጀምሩ")])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
