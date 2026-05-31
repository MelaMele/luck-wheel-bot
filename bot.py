import telebot
from telebot import types
import random
import time
import sys
import os

# 🔒 1. መጀመሪያ ከ GitHub Secrets ለመውሰድ ይሞክራል
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# ⚠️ 2. ከላይ ካጣው፣ እዚህ ጋ ያንተን ቶክን እንደ ባካፕ እንዲጠቀም ቀጥታ እንሰጠዋለን
if not TOKEN or TOKEN == "":
    TOKEN = "8627859146:AAGhkOEo6IgRljqrBveGdJextuoOs1DMSPU"

bot = telebot.TeleBot(TOKEN)

# የ GitHub Pages ሊንክህ (ውጤቱን በ URL Parameter የሚቀበለው)
BASE_WEB_URL = "https://MelaMele.github.io/luck-wheel-bot/"

GAME_POOL = {
    "active_players": {}, 
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
    
    if str(chat_id) in GAME_POOL["active_players"]:
        bot.answer_callback_query(call.id, text="በዚህ ዙር ቀድመው ቁጥር መርጠዋል! ⏳", show_alert=True)
        return

    GAME_POOL["active_players"][str(chat_id)] = selected_num
    current_count = len(GAME_POOL["active_players"])
    
    bot.answer_callback_query(call.id, text=f"ቁጥር {selected_num} ተመርጧል! ✅")
    bot.send_message(chat_id, f"🎯 ቁጥር **{selected_num}** መግባትዎ ተመዝግቧል። አጠቃላይ ተጫዋቾች፦ **{current_count}/10**", parse_mode="Markdown")

    if current_count >= GAME_POOL["max_players"]:
        run_automatic_draw()

def run_automatic_draw():
    players = GAME_POOL["active_players"].copy()
    
    # አሸናፊውን ቁጥር እዚህ መምረጥ
    winning_number = str(random.randint(1, 10))
    
    # 🔗 አሸናፊውን ቁጥር በሊንክ Parameters አያይዞ መላክ (URL Parameter Strategy)
    game_url_with_winner = f"{BASE_WEB_URL}?winner={winning_number}"
    
    for player_id in players.keys():
        try:
            markup = types.InlineKeyboardMarkup()
            web_app_info = types.WebAppInfo(url=game_url_with_winner)
            btn = types.InlineKeyboardButton(text="ቀጥታ ስርጭት እሽክርክሪቱን እይ 🎡", web_app=web_app_info)
            markup.add(btn)
            bot.send_message(int(player_id), "🚨 **10 ተጫዋቾች ሞልተዋል! እሽክርክሪቱ መዞር ጀምሯል!** 🚨\nከታች ያለውን ቁልፍ ተጭነው ጨዋታውን በቀጥታ ይከታተሉ!", reply_markup=markup)
        except Exception as e:
            print(f"ስህተት ለ {player_id}: {e}")
            
    # የ10 ሰከንድ የእሽክርክሪት ጊዜ መጠበቂያ
    time.sleep(10)
    
    winners = [pid for pid, num in players.items() if num == winning_number]
    
    total_pool = 10 * 30
    winner_share = int(total_pool * 0.80)
    our_share = int(total_pool * 0.20)
    
    if winners:
        share_per_winner = winner_share // len(winners)
        winners_text = ", ".join([f"`{w}`" for w in winners])
        result_text = (
            "🎉 **የዕጣው ውጤት በይፋ ወጥቷል!** 🎉\n\n"
            f"🎯 የወጣው ባለዕጣ ቁጥር፦ **{winning_number}**\n"
            f"👑 አሸናፊ(ዎች)፦ {winners_text}\n\n"
            f"💰 ጠቅላላ ገንዳ፦ **{total_pool} ብር**\n"
            f"🎁 ለአሸናፊ(ዎች) የተላከ (80%)፦ **{winner_share} ብር** ({share_per_winner} ብር ለእያንዳንዳቸው)\n"
            f"💼 የባለቤት ድርሻ (20%)፦ **{our_share} ብር**\n\n"
            "አዲስ ዙር ተከፍቷል! ለመሳተፍ ድጋሚ /start ይበሉ!"
        )
    else:
        result_text = (
            "🎉 **የዕጣው ውጤት በይፋ ወጥቷል!** 🎉\n\n"
            f"🎯 የወጣው ባለዕጣ ቁጥር፦ **{winning_number}**\n"
            "🎰 ያሳዝናል! በዚህ ዙር ይህንን ቁጥር የመረጠ ተጫዋች የለም።\n\n"
            f"💰 ጠቅላላ ገንዳው (**{total_pool} ብር**) ለሚቀጥለው ዙር ተላልፏል! 🚀\n\n"
            "አዲስ ዙር ተከፍቷል! ለመሳተፍ ድጋሚ /start ይበሉ!"
        )
    
    for player_id in players.keys():
        try:
            bot.send_message(int(player_id), result_text, parse_mode="Markdown")
        except:
            pass
            
    GAME_POOL["active_players"] = {}

if __name__ == "__main__":
    sys.stdout.flush()
    bot.remove_webhook()
    time.sleep(1)
    print("🎯 ቢዝነስ ቦቱ በሁለቱ አሰላለፍ በተሳካ ሁኔታ ተነስቷል...")
    bot.infinity_polling()
