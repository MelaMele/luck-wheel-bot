import telebot
from telebot import types
import random
import time
import sys

TOKEN = "8627859146:AAGhkOEo6IgRljqrBveGdJextuoOs1DMSPU"
bot = telebot.TeleBot(TOKEN)

# ⚠️ ይህ ሊንክ ትክክል መሆኑን በደንብ አረጋግጥ
WEB_APP_URL = "https://MelaMele.github.io/luck-wheel-bot/"

GAME_POOL = {
    "active_players": {}, 
    "ticket_price": 30,
    "max_players": 10
}

# ግልጽ ለማድረግ መጀመሪያ ቀላል የጽሑፍ ምላሽ መሞከሪያ
@bot.message_handler(commands=['start', 'game'])
def welcome_game(message):
    chat_id = message.chat.id
    current_count = len(GAME_POOL["active_players"])
    
    print(f"--- የ/start ትዕዛዝ ከ chat_id: {chat_id} ደርሷል ---") # በGitHub መዝገብ ላይ ለማየት
    
    welcome_text = (
        "🎡 **እንኳን ወደ ህዝባዊ የዕድል እሽክርክሪት መድረክ መጡ!** 🎡\n\n"
        f"💵 የትኬት ዋጋ፦ **{GAME_POOL['ticket_price']} ብር**\n"
        f"👥 አሁን ያሉ ተጫዋቾች፦ **{current_count}/{GAME_POOL['max_players']}**\n\n"
        "ከ1 እስከ 10 ያለውን የዕድል ቁጥርዎን በመምረጥ ይሳተፉ!"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(text=f"{i}", callback_data=f"select_{i}") for i in range(1, 11)]
    markup.add(*buttons)
    
    # try/except አውጥተነዋል ስህተት ካለ በግልጽ GitHub Actions ላይ እንዲያሳየን!
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_number_selection(call):
    chat_id = call.message.chat.id
    selected_num = call.data.split("_")[1]
    
    if chat_id in GAME_POOL["active_players"]:
        bot.answer_callback_query(call.id, text="ቀድመው ቁጥር መርጠዋል! ⏳", show_alert=True)
        return

    GAME_POOL["active_players"][chat_id] = selected_num
    current_count = len(GAME_POOL["active_players"])
    
    bot.answer_callback_query(call.id, text=f"ቁጥር {selected_num} ተመርጧል! ✅")
    
    # ለተጫዋቹ ማረጋገጫ መላክ
    bot.send_message(chat_id, f"🎯 ቁጥር **{selected_num}** መግባትዎ ተመዝግቧል። አጠቃላይ ተጫዋቾች፦ **{current_count}/10**", parse_mode="Markdown")

    if current_count >= GAME_POOL["max_players"]:
        run_automatic_draw()

def run_automatic_draw():
    players = GAME_POOL["active_players"]
    
    for player_id in players.keys():
        try:
            markup = types.InlineKeyboardMarkup()
            web_app_info = types.WebAppInfo(url=WEB_APP_URL)
            btn = types.InlineKeyboardButton(text="ቀጥታ ስርጭት እሽክርክሪቱን እይ 🎡", web_app=web_app_info)
            markup.add(btn)
            bot.send_message(player_id, "🚨 10 ተጫዋቾች ሞልተዋል! ከታች ባለው ቁልፍ እሽክርክሪቱን ይመልከቱ!", reply_markup=markup)
        except Exception as e:
            print(f"መልእክት ለመላክ አልተቻለም ለ {player_id}: {e}")
            
    time.sleep(10)
    
    winner_id = random.choice(list(players.keys()))
    winner_number = players[winner_id]
    
    result_text = (
        "🎉 **የዕጣው ውጤት ወጥቷል!** 🎉\n\n"
        f"🎯 የወጣው ባለዕጣ ቁጥር፦ **{winner_number}**\n"
        f"👑 አሸናፊ፦ `{winner_id}`\n\n"
        "ለማስታወቂያ ክፍያ እና ሽልማት አሰጣጥ በቅርቡ ይገናኙ!"
    )
    
    for player_id in players.keys():
        try:
            bot.send_message(player_id, result_text, parse_mode="Markdown")
        except:
            pass
            
    GAME_POOL["active_players"] = {}

if __name__ == "__main__":
    print("🎯 ቦቱ በዝግጅት ላይ ነው...")
    sys.stdout.flush()
    bot.infinity_polling()
