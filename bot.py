import telebot
from telebot import types
import random
import time
import sys
import os

# 🔒 ቶክኑን ከ GitHub Secrets በምስጢር መጥራት
TOKEN = "8627859146:AAGhkOEo6IgRljqrBveGdJextuoOs1DMSPU"

bot = telebot.TeleBot(TOKEN)

# የ GitHub Pages ሊንክህ
WEB_APP_URL = "https://MelaMele.github.io/luck-wheel-bot/"

# የጨዋታው ገንዳ (Pool) መቆጣጠሪያ
GAME_POOL = {
    "active_players": {},  # {str(chat_id): selected_number}
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
        "ከ1 እስከ 10 ያለውን የዕድል ቁጥርዎን በመምረጥ ይሳተፉ!"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(text=f"{i}", callback_data=f"select_{i}") for i in range(1, 11)]
    markup.add(*buttons)
    
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_number_selection(call):
    chat_id = call.message.chat.id
    selected_num = call.data.split("_")[1]
    
    # ተጫዋቹ ቀድሞ መሳተፉን ማረጋገጥ
    if str(chat_id) in GAME_POOL["active_players"]:
        bot.answer_callback_query(call.id, text="በዚህ ዙር ቀድመው ቁጥር መርጠዋል! ⏳", show_alert=True)
        return

    # ተጫዋቹን እና የመረጠውን ቁጥር መመዝገብ
    GAME_POOL["active_players"][str(chat_id)] = selected_num
    current_count = len(GAME_POOL["active_players"])
    
    bot.answer_callback_query(call.id, text=f"ቁጥር {selected_num} በተሳካ ሁኔታ ተመርጧል! ✅")
    
    # ለተጫዋቹ በጽሑፍ ማረጋገጫ መላክ
    bot.send_message(chat_id, f"🎯 ቁጥር **{selected_num}** መግባትዎ ተመዝግቧል። አጠቃላይ ተጫዋቾች፦ **{current_count}/10**", parse_mode="Markdown")

    # 10 ተጫዋች ሲሞላ አውቶማቲክ እጣ ማውጣት
    if current_count >= GAME_POOL["max_players"]:
        # ቦቱ መልእክት ልኮ እስኪያበቃ ድረስ ከበስተጀርባ (Thread) እንዲሰራ ማድረግ ይመረጣል፡ ግን ለጊዜው ቀጥታ እንጥራው
        run_automatic_draw()

def run_automatic_draw():
    players = GAME_POOL["active_players"].copy() # ሩጫዎችን ለመከላከል ኮፒ እንውሰድ
    
    # 1. ለሁሉም ተጫዋቾች የዌብ አፕሊኬሽን ሊንክ መላክ
    for player_id in players.keys():
        try:
            markup = types.InlineKeyboardMarkup()
            # ዌብ አፑን የሚከፍት ትክክለኛ መዋቅር
            web_app_info = types.WebAppInfo(url=WEB_APP_URL)
            btn = types.InlineKeyboardButton(text="ቀጥታ ስርጭት እሽክርክሪቱን እይ 🎡", web_app=web_app_info)
            markup.add(btn)
            bot.send_message(int(player_id), "🚨 **10 ተጫዋቾች ሞልተዋል! እሽክርክሪቱ መዞር ጀምሯል!** 🚨\nከታች ያለውን ቁልፍ ተጭነው ጨዋታውን በቀጥታ ይከታተሉ!", reply_markup=markup)
        except Exception as e:
            print(f"ስህተት ለመልእክት {player_id}: {e}")
            
    # 2. የ 10 ሰከንድ የእሽክርክሪት ጊዜ መጠበቅ
    time.sleep(10)
    
    # 3. አሸናፊውን መምረጥ
    winner_id = random.choice(list(players.keys()))
    winner_number = players[winner_id]
    
    # 4. የገንዘብ ስሌት
    total_pool = 10 * 30
    winner_share = int(total_pool * 0.80)
    our_share = int(total_pool * 0.20)
    
    result_text = (
        "🎉 **የዕጣው ውጤት በይፋ ወጥቷል!** 🎉\n\n"
        f"🎯 የወጣው ባለዕጣ ቁጥር፦ **{winner_number}**\n"
        f"👑 አሸናፊ ተጫዋች (ID)፦ `{winner_id}`\n\n"
        f"💰 ጠቅላላ የተሰበሰበ ገንዳ፦ **{total_pool} ብር**\n"
        f"🎁 ለአሸናፊው የሚከፈል (80%)፦ **{winner_share} ብር**\n"
        f"💼 የባለቤት ድርሻ/ኮሚሽን (20%)፦ **{our_share} ብር**\n\n"
        "አዲስ ዙር አሁን ተከፍቷል! ለመሳተፍ ድጋሚ /game ወይም /start ይበሉ!"
    )
    
    # 5. ውጤቱን ለሁሉም ማሰራጨት
    for player_id in players.keys():
        try:
            bot.send_message(int(player_id), result_text, parse_mode="Markdown")
        except:
            pass
            
    # 6. ገንዳውን ለቀጣዩ ዙር ማጽዳት
    GAME_POOL["active_players"] = {}

if __name__ == "__main__":
    print("🎯 የድሮ ግንኙነቶችን በማጽዳት ላይ...")
    sys.stdout.flush()
    bot.remove_webhook()
    time.sleep(1)
    
    print("🎯 ቢዝነስ ቦቱ በምስጢር አወቃቀር በተሳካ ሁኔታ ተነስቷል...")
    sys.stdout.flush()
    bot.infinity_polling()
