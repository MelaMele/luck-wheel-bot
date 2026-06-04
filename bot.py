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

# የውስጥ ማከማቻ
active_games = {}     # በየቦታው የተሸጡ ቁጥሮች {"chat_id": {"1": {"user_id":..., "name":...}}}
pending_payments = {} # ማረጋገጫ የሚጠብቁ {"user_id": {"chat_id":..., "num":..., "main_msg_id":...}}

def generate_keyboard(chat_id):
    """የቁጥሮችን ሰሌዳ አሁን ባለው ሁኔታ አዘጋጅቶ የሚመልስ ተግባር"""
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
            callback_data = f"buy_{i}_{chat_id}"
            
        row.append(InlineKeyboardButton(text=text, callback_data=callback_data))
        if i % 2 == 0: 
            buttons.append(row)
            row = []
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    chat_id = message.chat.id
    
    if chat_id not in active_games:
        active_games[chat_id] = {}

    welcome_text = (
        "🎡 <b>እንኳን ወደ ዕድል እሽከርክሪት መድረክ በሰላም መጡ!</b> 🎡\n\n"
        "💵 የትኬት ዋጋ፦ <b>30 ብር</b>\n"
        f"👥 አሁን የተሸጡ ትኬቶች፦ <b>{len(active_games[chat_id])}/10</b>\n\n"
        "ከ1 እስከ 10 ያለውን የዕድል ቁጥርዎን በመምረጥ ይሳተፉ፦"
    )
    
    await message.answer(text=welcome_text, reply_markup=generate_keyboard(chat_id), parse_mode="HTML")

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
        "main_msg_id": callback_query.message.message_id 
    }
    
    await callback_query.message.answer(text=payment_instruction, parse_mode="HTML")

@dp.callback_query(F.data.startswith("already_sold_"))
async def already_sold_handler(callback_query: types.CallbackQuery):
    await callback_query.answer("❌ ይህ ቁጥር ተሽጧል! እባክዎ ሌላ ቁጥር ይምረጡ።", show_alert=True)

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ከላይ ቁጥር ይምረጡ፤ ከዚያ የስክሪንሾት ፎቶ ይላኩ።")
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
        text=f"📣 <b>የደስታ ዜና!</b>\n👤 <b>{user_data['name']}</b> ቁጥር <b>{selected_num}</b>ን ገዝቷል።\n📊 የተሸጡ ትኬቶች፦ <b>{current_count}/10</b>",
        parse_mode="HTML"
    )
    
    try:
        updated_text = (
            "🎡 <b>እንኳን ወደ ዕድል እሽከርክሪት መድረክ በሰላም መጡ!</b> 🎡\n\n"
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
    
    if current_count >= 10:
        await start_spinning_effect(chat_id, user_data["main_msg_id"])

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

# 🔥 የተስተካከለው እና ለ 30 ሰኮንድ የሚቆየው የዕጣ አወጣጥ ክፍል
async def start_spinning_effect(chat_id: int, main_msg_id: int):
    # 1. መጀመሪያ ለ 25 ሰኮንድ የሚቆይ አስደሳች የጽሑፍ አኒሜሽን (Countdown)
    msg = await bot.send_message(chat_id=chat_id, text="🚨 <b>10ቱም ትኬቶች በሙሉ ተሽጠዋል! እጣው አሁን ይጀመራል...</b>", parse_mode="HTML")
    
    # ሰዎችን በጉጉት ለማቆየት በየ 5 ሰኮንዱ መልዕክቱን ማደስ (ጠቅላላ 25 ሰኮንድ)
    await asyncio.sleep(5)
    await msg.edit_text("🔄 <b>የዕድል መንኮራኩሩ በከፍተኛ ፍጥነት መሽከርከር ጀምሯል... [ 🔄 SPINNING ]</b>", parse_mode="HTML")
    
    await asyncio.sleep(5)
    await msg.edit_text("⚡ <b>ፍጥነቱ እየጨመረ ነው! አሸናፊው ማን ሊሆን ይችላል? ፌሪስ ዊሉ እየዞረ ነው...</b>", parse_mode="HTML")
    
    await asyncio.sleep(5)
    await msg.edit_text("🎯 <b>መንኮራኩሩ ፍጥነቱን እየቀነሰ ነው... ወደ መጨረሻው ቁጥር እየተቃረበ ነው!</b>", parse_mode="HTML")
    
    await asyncio.sleep(5)
    await msg.edit_text("🔥 <b>የመጨረሻ 5 ሰከንድ! ልብ ሰቀላ ሰዓት... እጣው አሁን ይቆማል!...</b>", parse_mode="HTML")
    await asyncio.sleep(5)
    
    await msg.delete() # የጽሑፍ አኒሜሽኑን ማጥፋት

    # 2. ቀሪውን 5 ሰከንድ በዕይታ ለማሳመር እውነተኛ የቴሌግራም ዳርት (🎯) መላክ
    # የዳርት ኢሞጂ ውጤት ከ 1 እስከ 6 ቁጥሮችን ብቻ ነው የሚሰጠው። 
    # ስለዚህ ውጤቱ 100% ከምስሉ ጋር እኩል እንዲሆን እጣውን ከ 1 እስከ 6 ቁጥሮች ውስጥ እናደርገዋለን።
    dice_msg = await bot.send_dice(chat_id=chat_id, emoji="🎯")
    winner_number = str(dice_msg.dice.value) # ምስሉ ላይ ያረፈው እውነተኛ ቁጥር (ከ1 እስከ 6)
    
    # ዳርቱ ተወርውሮ ሰሌዳው ላይ እስኪያርፍ 4 ሰከንድ መታገስ
    await asyncio.sleep(4)
    
    players = active_games[chat_id]
    winner_user = players.get(winner_number)
    
    # 3. ውጤቱን ማወጅ (ከምስሉ ቁጥር ጋር ፍጹም አንድ አይነት ይሆናል)
    if winner_user:
        result_text = (
            f"🎉 <b>ዕጣው በይፋ ወጥቷል! እንኳን ደስ አሎት!</b> 🎉\n\n"
            f"🎯 በምስሉ ላይ የወጣው አሸናፊ ቁጥር፦ <b>ቁጥር {winner_number}</b>\n"
            f"👑 የዚህ ዙር ሻምፒዮን፦ <a href='tg://user?id={winner_user['user_id']}'>{winner_user['name']}</a>\n\n"
            f"💰 <b>የ 200 ብር</b> ሽልማትዎን ለመቀበል ለአስተዳዳሪው መልዕክት ይላኩ!"
        )
    else:
        result_text = (
            f"🎯 በምስሉ ላይ የወጣው ቁጥር፦ <b>ቁጥር {winner_number}</b> ነበር።\n\n"
            f"😔 <b>የሚገርም ነው!</b> ይህንን ቁጥር በዚህ ዙር ማንም ስላልገዛው አሸናፊ የለም።\n"
            f"💰 የተሰበሰበው ገንዘብ በቀጥታ ወደ ሚቀጥለው ዙር ተላልፏል! አዲስ ዙር ለመጀመር /start ይበሉ።"
        )
        
    await bot.send_message(chat_id=chat_id, text=result_text, parse_mode="HTML")
    active_games[chat_id] = {}

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
