import telebot
from telebot import types
import random
import time

TOKEN = "8627859146:AAGhkOEo6IgRljqrBveGdJextuoOs1DMSPU"
bot = telebot.TeleBot(TOKEN)

WEB_APP_URL = "https://MelaMele.github.io/luck-wheel-bot/"

# የጨዋታው ሁኔታዎችን መቆጣጠሪያ (Database ፈንታ ጊዜያዊ ሚሞሪ)
GAME_POOL = {
    "active_players": {}, # {chat_id: selected_number}
    "ticket_price": 30,
    "max_players": 10
}

@bot.message_handler(commands=['start', 'game'])
def welcome_game(message):
    chat_id = message.chat.id
    current_count = len(GAME_POOL["active_players"])
    
    welcome_text = (
        "🎡 **እንኳን ወደ ህዝባዊ የዕድል እሽክርክሪት መድረክ መጡ!** 🎡\n\n"
        f"💵 የትኬት ዋጋ፦ **{GAME_POOL['ticket_price']} ብር**\n"
        f"👥 አሁን ያሉ ተጫዋቾች፦ **{current_count}/{GAME_POOL['max_players']}**\n\n"
        "የእድል ቁጥርዎን (ከ1 እስከ 10) በመምረጥ ይሳተፉ። 10 ተጫዋች ሲሞላ ጨዋታው በራሱ ይጀምራል!"
    )
    
    # ከ1 እስከ 10 ቁጥሮችን በቁልፍ ማሳየት
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(text=f"🔢 {i}", callback_data=f"select_{i}") for i in range(1, 11)]
    markup.add(*buttons)
    
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_number_selection(call):
    chat_id = call.message.chat.id
    selected_num = call.data.split("_")[1]
    
    if chat_id in GAME_POOL["active_players"]:
        bot.answer_callback_query(call.id, text="ቀድመው ቁጥር መርጠዋል! የሌሎችን መሙላት ይጠብቁ። ⏳", show_alert=True)
        return

    # ተጫዋቹን መመዝገብ (እዚህ ጋ እውነተኛ ክፍያ ሲኖር Verify ይደረጋል)
    GAME_POOL["active_players"][chat_id] = selected_num
    current_count = len(GAME_POOL["active_players"])
    
    bot.answer_callback_query(call.id, text=f"ቁጥር {selected_num}ን መርጠዋል። የ30 ብር ክፍያ ተመዝግቧል! ✅")
    
    # ሁሉንም ተጫዋቾች አሁን ስላለው ሁኔታ ማሳወቅ
    for player_id in GAME_POOL["active_players"].keys():
        try:
            bot.send_message(player_id, f"🔔 አዲስ ተጫዋች ገብቷል! አጠቃላይ ተጫዋቾች፦ **{current_count}/10**", parse_mode="Markdown")
        except:
            pass

    # 10 ተጫዋች ከሞላ አውቶማቲክ እሽክርክሪቱን ማስጀመር
    if current_count >= GAME_POOL["max_players"]:
        run_automatic_draw()

def run_automatic_draw():
    players = GAME_POOL["active_players"]
    
    # 1. ለሁሉም ተጫዋቾች እሽክርክሪቱ መጀመሩን ማብሰር
    for player_id in players.keys():
        try:
            markup = types.InlineKeyboardMarkup()
            web_app_info = types.WebAppInfo(url=WEB_APP_URL)
            btn = types.InlineKeyboardButton(text="ቀጥታ ስርጭት እሽክርክሪቱን እይ 🎡", web_app=web_app_info)
            markup.add(btn)
            bot.send_message(player_id, "🚨 **10 ተጫዋቾች ሞልተዋል! እሽክርክሪቱ አሁን ለ10 ሰከንድ ይሽከረከራል!** 🚨\nከታች ያለውን ቁልፍ ተጭነው ቀጥታ ስርጭቱን ይከታተሉ!", parse_mode="Markdown", reply_markup=markup)
        except:
            pass
            
    # 2. የ10 ሰከንድ ጥበቃ (የእሽክርክሪት ጊዜ)
    time.sleep(10)
    
    # 3. አሸናፊውን በዘፈቀደ መምረጥ
    winner_id = random.choice(list(players.keys()))
    winner_number = players[winner_id]
    
    # 4. የገንዘብ ስሌት
    total_pool = 10 * 30  # 300 ብር
    winner_share = int(total_pool * 0.80)  # 240 ብር
    our_share = int(total_pool * 0.20)  # 60 ብር
    
    result_text = (
        "🎉 🔴 **የዕጣው ውጤት ወጥቷል!** 🔴 🎉\n\n"
        f"🎯 የወጣው ባለዕጣ ቁጥር፦ **{winner_number}**\n"
        f"👑 አሸናፊ፦ የቴሌግራም መለያው `{winner_id}` የሆነው ተጫዋች ነው!\n\n"
        f"💰 ጠቅላላ የተሰበሰበ ገንዳ፦ **{total_pool} ብር**\n"
        f"🎁 ለአሸናፊው የሚላክ (80%)፦ **{winner_share} ብር**\n"
        f"💼 የኤጀንሲያችን የተጣራ ትርፍ (20%)፦ **{our_share} ብር**\n\n"
        "ቀጣዩ ዙር አሁን ተከፍቷል! ለመሳተፍ ድጋሚ /game ይበሉ!"
    )
    
    # 5. ውጤቱን ለሁሉም ማሰራጨት
    for player_id in players.keys():
        try:
            bot.send_message(player_id, result_text, parse_mode="Markdown")
        except:
            pass
            
    # 6. ገንዳውን ለቀጣዩ ዙር ባዶ ማድረግ
    GAME_POOL["active_players"] = {}
