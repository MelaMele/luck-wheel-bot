import telebot
from telebot import types
import json

TOKEN = "8627859146:AAGhkOEo6IgRljqrBveGdJextuoOs1DMSPU"
bot = telebot.TeleBot(TOKEN)

# ⚠️ ማሳሰቢያ፦ ይህ የ GitHub ገጽህ አድራሻ ነው። index.html ን GitHub Pages ላይ ካበራኸው በኋላ የሚሰጥህ ሊንክ ነው!
# ለጊዜው በሙከራ ሊንክ ተክቼዋለሁ፣ ሪፖዚቶሪህን Pages ካደረግከው በኋላ በራስህ ሊንክ ትተካዋለህ።
WEB_APP_URL = "https://melamele.github.io/luck-wheel-bot//" 

@bot.message_handler(commands=['start', 'spin'])
def send_game(message):
    chat_id = message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    # WebApp ቁልፍ መፍጠር
    web_app_info = types.WebAppInfo(url=WEB_APP_URL)
    btn = types.InlineKeyboardButton(text="ጨዋታውን ጀምር 🎡", web_app=web_app_info)
    markup.add(btn)
    
    bot.send_message(
        chat_id, 
        "🎡 **እንኳን ወደ ዕድል እሽክርክሪት በደህና መጡ!**\n\nከታች ያለውን ቁልፍ በመንካት እውነተኛውን ባለ 3D እሽክርክሪት ያሽከርክሩ!", 
        parse_mode="Markdown", 
        reply_markup=markup
    )

# ተጠቃሚው አሽከርክሮ ሲጨርስ ዌብሳይቱ የሚልከውን ውጤት እዚህ ይቀበላል
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    chat_id = message.chat.id
    data = json.loads(message.web_app_data.data)
    user_prize = data.get("prize", "ምንም")
    
    response_text = (
        "🎉 **እንኳን ደስ አለዎት!** 🎉\n\n"
        f"እሽክርክሪቱ ቆሞ የደረሰዎት ሽልማት፦\n"
        f"➡️ 🏆 **{user_prize}** 🏆\n\n"
        "እንደገና ለመጫወት /spin ይበሉ!"
    )
    bot.send_message(chat_id, response_text, parse_mode="Markdown")

if __name__ == "__main__":
    print("ቦቱ ከWeb App ጋር በተሳካ ሁኔታ ተገናኝቶ ስራ ጀምሯል...")
    bot.infinity_polling()
