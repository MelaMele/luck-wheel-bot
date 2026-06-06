import asyncio
import random
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.deep_linking import create_start_link
from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    BotCommand
)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# 🔐 ዋና ዋና መረጃዎች (የራስህን መረጃዎች እዚህ ላይ አስተካክል)
ADMIN_CHAT_ID = 1065443252  
TELEBIRR_NUMBER = "+251913064239" 
GROUP_LINK = "https://t.me/Yechewatamenkurakur" # 🔗 የቴሌግራም ግሩፕህ ሊንክ እዚህ ይግባ

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# የጋራ የውስጥ ማከማቻ (ሁልጊዜ የተመሳሰለ ነው)
# ለአሁኑ ማሳያ የአንድ ግሩፕ መታወቂያ እንጠቀማለን (Multi-group እንዲሆን ከተፈለገ በ ID ይከፋፈላል)
GAME_ROOM_ID = "main_game"
active_games = {GAME_ROOM_ID: {}}     
pending_payments = {} # {"user_id": {"num":..., "name":...}}

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

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # ሴኩሪቲ፦ ይህ ጨዋታ የሚካሄደው በቦቱ የውስጥ መስመር ብቻ ነው
    if message.chat.type != "private":
        bot_info = await bot.get_me()
        # ወደ ቦቱ የሚያስገባ ሊንክ በግሩፑ ላይ ይልካል
        bot_link = f"https://t.me/{bot_info.username}?start=play"
        await message.answer(
            f"🎡 <b>ወደ ዕድል እሽከርክሪት ጨዋታ ለመግባት ከታች ያለውን በተን ይጫኑ፦</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🕹️ አሁኑኑ ተጫወት", url=bot_link)]
            ]),
            parse_mode="HTML"
        )
        return

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

@dp.callback_query(F.data.startswith("buy_num_"))
async def buy_number_handler(callback_query: types.CallbackQuery):
    selected_num = callback_query.data.split("_")[2]
    user_id = callback_query.from_user.id
    username = callback_query.from_user.full_name
    
    # ቼክ 1፦ ቁጥሩ ድጋሚ እንዳይገዛ በቅጽበት ማረጋገጫ
    if selected_num in active_games[GAME_ROOM_ID]:
        await callback_query.answer("❌ ይቅርታ፣ ይህ ቁጥር አሁን በሌላ ሰው ተገዝቷል! እባክዎ ሌላ ይምረጡ።", show_alert=True)
        # ሰሌዳውን በቅጽበት ማደስ
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
    
    pending_payments[user_id] = {
        "num": selected_num,
        "name": username
    }
    
    await callback_query.message.answer(payment_instruction, parse_mode="HTML")

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ቀደም ብሎ ተሽጧል! እባክዎ ሌላ አረንጓዴ ቁጥር ይምረጡ።", show_alert=True)

# ሴኩሪቲ፦ ፎቶ ብቻ ነው የሚቀበለው (ቪዲዮ፣ ፅሁፍ ወይም ሊንክ አይቀበልም)
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
            InlineKeyboardButton(text="✅ አጽдቅ (Approve)", callback_data=f"adm_ap_{user_id}"),
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
    """ሴኩሪቲ፦ ከፎቶ ውጪ የሚላኩ የማይገቡ ጽሑፎችንና ፋይሎችን በሙሉ ውድቅ ማድረጊያ"""
    if message.chat.type == "private":
        await message.reply("⚠️ እባክዎ የክፍያ ስክሪንሾት (የፎቶ ፋይል) ብቻ ይላኩ። ሌላ አይነት ፋይል ወይም ጽሑፍ ሲስተሙ አይቀበልም።")

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
    
    # በዋናው የጋራ ዳታቤዝ ላይ ቁጥሩን መቆለፍ
    active_games[GAME_ROOM_ID][selected_num] = {"user_id": target_user_id, "name": user_data["name"]}
    
    # 🔗 ወደ ግሩፑ መመለሻ በተን ማዘጋጀት
    back_to_group_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏃‍♂️ ወደ ግሩፑ ተመለስ", url=GROUP_LINK)]
    ])
    
    await bot.send_message(
        chat_id=target_user_id, 
        text=f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {selected_num}</b> በስምዎ ተመዝግቧል። አሁኑኑ ወደ ግሩፑ በመመለስ የጨዋታውን ሂደት ይከታተሉ! 🍀", 
        reply_markup=back_to_group_kb,
        parse_mode="HTML"
    )
    
    current_count = len(active_games[GAME_ROOM_ID])
    
    # በዋናው ግሩፕ ላይ ማስታወቂያ መላክ
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID, # ወይም እዚህ ላይ የግሩፕህን ቻት መታወቂያ ማድረግ ትችላለህ
            text=f"📣 <b>የደስታ ዜና!</b>\n👤 <b>{user_data['name']}</b> ቁጥር <b>{selected_num}</b>ን በይፋ ገዝቷል።\n📊 የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>",
            parse_mode="HTML"
        )
    except Exception:
        pass
        
    del pending_payments[target_user_id]
    await callback_query.message.edit_caption(caption=f"✅ ተፈቅዷል! ቁጥር {selected_num} ተመዝግቧል።", reply_markup=None)
    
    if current_count >= 10:
        # እዚህ ላይ የርችት እጣ ማውጫው ተግባር ይቀጥላል
        pass

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

async def main():
    await bot.set_my_commands([
        BotCommand(command="start", description="🕹️ ጨዋታውን ይጀምሩ")
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
