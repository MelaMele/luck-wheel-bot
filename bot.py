import telebot
from telebot import types
import random
import time

# 1. ቦቱን ማስተዋወቅ (የሰጠኸኝ ቶክን እና የምስል መለያ እዚህ ገብቷል)
TOKEN = "8627859146:AAGhkOEo6IgRljqrBveGdJextuoOs1DMSPU"
bot = telebot.TeleBot(TOKEN)

WHEEL_IMAGE_ID = "AgACAgQAAxkBAAMDahtKKDB4AR4SqoimhwrzA63daUQAAucQaxtlndlQskmYjyvvVOsBAAMCAAN5AAM7BA"

# 2. የጨዋታው ውጤቶች ዝርዝር (እንደ ፍላጎትህ ማሻሻል ትችላለህ)
PRIZES = [
    "🎁 50 ነጥብ አሸንፈሃል!",
    "🎁 100 ነጥብ አሸንፈሃል!",
    "🎁 500 ነጥብ አሸንፈሃል!",
    "💥 ዛሬ አልቀናህም! በሚቀጥለው ይሞክሩ!",
    "🎁 🏆 ታላቁን ሽልማት አሸንፈሃል!"
]

# 3. ተጠቃሚው /start ወይም /spin ሲል ጨዋታው በምስል ይጀምራል
@bot.message_handler(commands=['start', 'spin'])
def send_wheel_game(message):
    chat_id = message.chat.id
    
    caption_text = (
        "🎡 **የዕድል እሽክርክሪት ጨዋታ** 🎡\n\n"
        "እሽክርክሪቱ በከፍተኛ ፍጥነት እየተሽከረከረ ነው... 🔄\n"
        "እባክህ ከታች ያለውን ቁልፍ በመጫን ውጤትህን እይ!"
    )
    
    # የውጤት ማያ ቁልፍ ማዘጋጀት
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton(text="ውጤቱን እይ 🎁", callback_data="check_result")
    markup.add(btn)
    
    try:
        # ምስሉን እና ጽሑፉን በአንድ ላይ ይልካል
        bot.send_photo(
            chat_id=chat_id, 
            photo=WHEEL_IMAGE_ID, 
            caption=caption_text, 
            parse_mode="Markdown",
            reply_markup=markup
        )
    except Exception as e:
        # በምክንያት ምስሉ ባይሰራ እንኳ ቦቱ እንዳይቆም በጽሑፍ ብቻ ይልካል
        bot.send_message(chat_id, caption_text, parse_mode="Markdown", reply_markup=markup)

# 4. ተጠቃሚው "ውጤቱን እይ" የሚለውን ቁልፍ ሲጫን የሚፈጸም ተግባር
@bot.callback_query_handler(func=lambda call: call.data == "check_result")
def process_result(call):
    chat_id = call.message.chat.id
    
    # መጀመሪያ ተጠቃሚው ላይ "እየተሽከረከረ ነው..." የሚል ማሳወቂያ በቴሌግራም ላይ ያሳያል
    bot.answer_callback_query(call.id, text="እባክህ ትንሽ ታገስ... ውጤትህ እየመጣ ነው! ⏳", show_alert=False)
    
    # በዘፈቀደ (Random) አንድ ውጤት መምረጥ
    selected_prize = random.choice(PRIZES)
    
    # አዲስ ጽሑፍ ማዘጋጀት
    result_text = (
        "🎉 **ውጤትህ ደርሷል!** 🎉\n\n"
        f"የደረሰህ ሽልማት፦\n➡️ **{selected_prize}**\n\n"
        "እንደገና ለመጫወት /spin ይበሉ!"
    )
    
    # የድሮውን መልእክት በመቀየር አዲሱን ውጤት ያሳያል
    bot.edit_message_caption(
        chat_id=chat_id,
        message_id=call.message.message_id,
        caption=result_text,
        parse_mode="Markdown"
    )

# 5. ቦቱን ማለቂያ በሌለው ሁኔታ ማሰራት (Polling)
if __name__ == "__main__":
    print("🎯 የዕድል እሽክርክሪት ቦት በተሳካ ሁኔታ ተነስቷል...")
    bot.infinity_polling()
