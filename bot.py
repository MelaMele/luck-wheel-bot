import asyncio
import random
import os
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = 1065443252
GROUP_CHAT_ID = -1003866369018
TELEBIRR_NUMBER = "0920628769"
TELEBIRR_NAME = "Tsige Tulu"
GROUP_LINK = "https://t.me/Yechewatamenkurakur"

# 🌐 ያንተ ዌብሳይት ሊንክ (የመጨረሻዋ ሰረዝ ግዴታ ናት!)
WEB_APP_URL = "https://melamele.github.io/mela-wheel-app/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

ROOMS = {
    "30": {"name": "🥉 የነሐስ ክፍል (30 ብር)", "price": 30, "max_players": 10, "prize": 250},
    "50": {"name": "🥈 የብር ክፍል (50 ብር)", "price": 50, "max_players": 5, "prize": 200},
    "100": {"name": "🥇 የወርቅ ክፍል (100 ብር)", "price": 100, "max_players": 5, "prize": 400}
}

active_games = {"30": {}, "50": {}, "100": {}}
pending_payments = {}
user_wallets = {}
user_play_counts = {}
referred_users = {}
rewarded_referrals = set()

def check_and_create_user(user_id: int):
    if user_id not in user_wallets: user_wallets[user_id] = 0.0
    if user_id not in user_play_counts: user_play_counts[user_id] = 0

@dp.message(CommandStart())
async def start_handler(message: types.Message):
    if message.chat.type != "private": return
    
    user_id = message.from_user.id
    check_and_create_user(user_id)
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_id = int(args[1].replace("ref_", ""))
        if ref_id != user_id and user_id not in referred_users:
            referred_users[user_id] = ref_id

    # 🕹️ አፑን ለመክፈት አስተማማኙ መንገድ ReplyKeyboardMarkup መጠቀም ነው
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🕹️ ጨዋታውን ክፈት", web_app=WebAppInfo(url=WEB_APP_URL))],
        [KeyboardButton(text="💳 ዋሌት"), KeyboardButton(text="👥 ጋብዝ")]
    ], resize_keyboard=True)

    await message.answer("🎡 <b>እንኳን ወደ ዕድል እሽከርክሪት ማዕከል በሰላም መጡ!</b>\n\nከታች ያለውን አረንጓዴ በተን ተጭነው የሚሽከረከረውን መንኮራኩር ይክፈቱት፦", reply_markup=kb, parse_mode="HTML")

@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    user_id = message.from_user.id
    try:
        data = json.loads(message.web_app_data.data)
        room_id, num = str(data['room']), str(data['number'])
        info = ROOMS[room_id]

        if num in active_games[room_id]:
            await message.answer("❌ ይቅርታ፣ ይህ ቁጥር በሌላ ሰው ተይዟል። እባክዎ ድጋሚ አፑን ከፍተው ሌላ ቁጥር ይምረጡ።")
            return

        if user_id in pending_payments:
            await message.answer("⚠️ ቀደም ሲል የላኩት ክፍያ በአስተዳዳሪው እይታ ላይ ነው። እሱ እስኪጸድቅ እባክዎ ይጠብቁ።")
            return

        pending_payments[user_id] = {"num": num, "room": room_id, "name": message.from_user.full_name}
        
        pay_msg = (f"✨ <b>የክክፍያ ማረጋገጫ ፎርም</b> ✨\n\n🎪 <b>ክፍል፦</b> {info['name']}\n🎯 <b>የመረጡት ቁጥር፦</b> <b>ቁጥር {num}</b>\n"
                   f"💰 <b>የሚከፍሉት መጠን፦</b> <code>{info['price']} ብር</code>\n\n📱 <b>የቴሌብር ቁጥር፦</b> <code>{TELEBIRR_NUMBER}</code>\n"
                   f"👤 <b>ስም፦</b> {TELEBIRR_NAME}\n\n📸 እባክዎ ክፍያውን ፈጽመው ሲጨርሱ <b>የክፍያውን ስክሪንሾት (Screenshot) ፎቶ</b> ብቻ እዚህ ላይ ይላኩ።")
        await message.answer(pay_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Error: {e}")

@dp.message(F.photo)
async def screenshot_receiver(message: types.Message):
    uid = message.from_user.id
    if uid not in pending_payments:
        await message.reply("⚠️ እባክዎ መጀመሪያ ከጨዋታው መተግበሪያ ውስጥ ቁጥር ይምረጡ።")
        return
    
    u_data = pending_payments[uid]
    await message.reply("📥 <b>የክፍያ ስክሪንሾትዎ ደርሶናል። በአስተዳዳሪው ተረጋግጦ ቁጥሩ እስኪመዘገብ እባክዎ ይጠብቁ! 🕒</b>", parse_mode="HTML")
    
    adm_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ አጽድቅ (Approve)", callback_data=f"adm_ap_{uid}"), InlineKeyboardButton(text="❌ ውድቅ አድርግ (Reject)", callback_data=f"adm_rj_{uid}")]])
    await bot.send_photo(ADMIN_CHAT_ID, message.photo[-1].file_id, caption=f"🔔 <b>አዲስ ክፍያ!</b>\n\n👤 <b>ተጫዋች፦</b> {u_data['name']}\n🔢 <b>ቁጥር፦</b> <b>ቁጥር {u_data['num']}</b>", reply_markup=adm_kb, parse_mode="HTML")

@dp.callback_query(F.data.startswith("adm_ap_"))
async def admin_approve_handler(cb: types.CallbackQuery):
    uid = int(cb.data.split("_")[2])
    if uid not in pending_payments: return
    
    d = pending_payments[uid]
    rid, num = d['room'], d['num']
    info = ROOMS[rid]
    
    active_games[rid][num] = {"user_id": uid, "name": d['name']}
    check_and_create_user(uid)
    user_play_counts[uid] += 1
    
    # 👥 የሪፈራል ኮሚሽን (3 ብር)
    if uid in referred_users and uid not in rewarded_referrals:
        ref_id = referred_users[uid]
        check_and_create_user(ref_id)
        user_wallets[ref_id] += 3.0
        rewarded_referrals.add(uid)
        try: await bot.send_message(ref_id, f"🎁 <b>የአፍሊየት ኮሚሽን ገቢ!</b> የጋበዙት ሰው የመጀመሪያ ጨዋታውን ስለተጫወተ <b>3 ብር</b> ዋሌትዎ ላይ ተጨምሯል!", parse_mode="HTML")
        except: pass

    # 🎖️ የታማኝነት ጉርሻ
    loyalty_text = ""
    if user_play_counts[uid] % 5 == 0:
        user_wallets[uid] += 10.0
        loyalty_text = f"\n\n🎁 <b>ልዩ የታማኝነት ስጦታ፦</b> ይህ {user_play_counts[uid]}ኛው ጨዋታዎ ስለሆነ <b>10 ብር</b> ተጨምሯል!"

    await bot.send_message(uid, f"🎉 <b>ክፍያዎ ተረጋግጧል!</b>\n🔢 <b>ቁጥር {num}</b> በ{info['name']} ተመዝግቧል።{loyalty_text}", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏃‍♂️ ወደ ግሩፑ ተመለስ", url=GROUP_LINK)]]), parse_mode="HTML")
    
    count = len(active_games[rid])
    try: await bot.send_message(GROUP_CHAT_ID, f"📣 <b>አዲስ ተሳታፊ ተመዝግቧል!</b>\n━━━━━━━━━━━━━━━━━━━━━━\n👤 <b>ተጫዋች፦</b> {d['name']}\n🎪 <b>ክፍል፦</b> {info['name']}\n🔢 <b>የመረጡት ቁጥር፦</b> <b>ቁጥር {num}</b>\n📊 <b>የተሸጡ ትኬቶች፦</b> <b>{count}/{info['max_players']}</b>\n━━━━━━━━━━━━━━━━━━━━━━\n🕹️ <i>ለመሳተፍ ቦቱን በውስጥ መስመር ያናግሩት!</i>", parse_mode="HTML")
    except: pass
    
    try: await cb.message.edit_caption(caption="✅ ተፈቅዷል!", reply_markup=None)
    except: pass
    
    del pending_payments[uid]
    if count >= info["max_players"]: await start_spinning_effect(GROUP_CHAT_ID, rid)

@dp.callback_query(F.data.startswith("adm_rj_"))
async def admin_reject_handler(cb: types.CallbackQuery):
    uid = int(cb.data.split("_")[2])
    if uid not in pending_payments: return
    await bot.send_message(uid, "❌ <b>ክፍያዎ ውድቅ ተደርጓል!</b>\nየላኩት ስክሪንሾት ትክክለኛ አይደለም።", parse_mode="HTML")
    del pending_payments[uid]
    await cb.message.edit_caption(caption="❌ ውድቅ ተደርጓል።", reply_markup=None)

async def start_spinning_effect(chat_id, rid):
    info = ROOMS[rid]
    winner_num = str(random.randint(1, info["max_players"]))
    msg = await bot.send_message(chat_id, f"🚨 <b>የ{info['name']} ሁሉም ትኬቶች ተሽጠዋል! የዕድል መንኮራኩሩ አሁን ይጀምራል...</b>", parse_mode="HTML")
    await asyncio.sleep(3)
    await msg.edit_text("🔄 <b>የዕድል መንኮራኩሩ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... [ 🎰 SPINNING ]</b>", parse_mode="HTML")
    await asyncio.sleep(3)
    
    winner = active_games[rid].get(winner_num)
    if winner:
        txt = (f"🎆✨🎉 <b>እጣው በይፋ ወጥቷል! ({info['name']})</b> 🎉✨🎆\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
               f"🎰 <b>የመጣው የዕድል ቁጥር፦</b> <b>ቁጥር {winner_num}</b>\n\n"
               f"👑 <b>የዚህ ዙር ታላቅ ሻምፒዮን፦</b> <a href='tg://user?id={winner['user_id']}'>{winner['name']}</a>\n\n"
               f"━━━━━━━━━━━━━━━━━━━━━━\n💰 <b>የ {info['prize']} ብር</b> ሽልማት በቴሌብር ይላክሎታል። እንኳን ደስ አለዎት! 🎁")
    else: txt = f"🎰 ያረፈበት ቁጥር <b>ቁጥር {winner_num}</b> ነበር። ግን ማንም ስላልገዛው አሸናፊ የለም።"
    await msg.edit_text(txt, parse_mode="HTML")
    active_games[rid] = {}

@dp.message(F.text == "💳 ዋሌት")
async def wallet(msg: types.Message):
    uid = msg.from_user.id
    check_and_create_user(uid)
    await msg.answer(f"💳 <b>የእርስዎ ዲጂታል ዋሌት</b>\n\n💰 <b>ባላንስ፦</b> <code>{user_wallets[uid]} ETB</code>\n🎮 <b>የተጫወቱት ብዛት፦</b> <code>{user_play_counts[uid]} ጊዜ</code>", parse_mode="HTML")

@dp.message(F.text == "👥 ጋብዝ")
async def invite(msg: types.Message):
    uid = msg.from_user.id
    b_info = await bot.get_me()
    total = list(referred_users.values()).count(uid)
    await msg.answer(f"🤝 <b>የመጋበዣ ማዕከል</b>\n\n👥 <b>የጋበዟቸው ሰዎች፦</b> <code>{total} ሰው</code>\n🎁 <b>ስጦታ፦</b> የመጡት ሰው መጀመሪያ ሲጫወት <b>3 ብር</b> ያገኛሉ!\n\n🔗 <b>ሊንክዎ፦</b>\n<code>https://t.me/{b_info.username}?start=ref_{uid}</code>", parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
