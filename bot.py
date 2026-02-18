import logging
import requests
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# --- তোর ডিটেইলস ---
TELEGRAM_BOT_TOKEN = '8503164235:AAGAI07Z8uqeTLpytbM-Zl3lF2vZM2cGJkk'
ADMIN_ID = 8517732618
IMGBB_API_KEY = 'Ec5ec8130dbd171fd343bcc4ad6abdcc' 

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ফাইল সেভ করার পাথ রেন্ডারের জন্য সহজ করে দেওয়া হয়েছে
USERS_FILE = "users.txt"
COUNT_FILE = "order_count.txt"

def get_total_orders():
    if not os.path.exists(COUNT_FILE):
        return 0
    with open(COUNT_FILE, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return 0

def increment_order():
    count = get_total_orders() + 1
    with open(COUNT_FILE, "w") as f:
        f.write(str(count))
    return count

def save_user(user_id):
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f: f.write("")
    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(f"{user_id}\n")
        return True
    return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_new = save_user(user.id)
    
    # নতুন ইউজার জয়েন করলে অ্যাডমিনকে জানানো
    if is_new:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID, 
                text=f"🔔 **নতুন ইউজার অ্যালার্ট!**\n\nনাম: {user.first_name}\nআইডি: `{user.id}`\nসিস্টেমে নতুন ইউজার যুক্ত হয়েছে।"
            )
        except Exception as e:
            logging.error(f"Admin notification failed: {e}")
    
    welcome_text = (
        f"স্বাগতম {user.first_name}! 🌟\n\n"
        "আপনার যেকোনো ছবিকে সরাসরি হোস্টিং লিংকে পরিবর্তন করতে আমাকে পাঠিয়ে দিন। এটি একটি **ফ্রি ইমেজ হোস্টিং বট**।\n\n"
        "**কীভাবে ছবি পাঠাবেন?**\n"
        "১. নিচের 'Attachment' (📎) আইকনে ক্লিক করুন।\n"
        "২. গ্যালারি থেকে ছবিটি সিলেক্ট করুন।\n"
        "৩. তারপর 'Send' বাটনে চাপ দিন।\n\n"
        "ব্যাস! আমি সাথে সাথে আপনাকে ছবির ডিরেক্ট লিংক দিয়ে দেব। শুরু করতে এখনই একটি ছবি পাঠান। 📸"
    )

    if user.id == ADMIN_ID:
        keyboard = [['/broadcast']]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"হ্যালো বস!\n\n{welcome_text}", reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def upload_to_imgbb(image_bytes):
    url = "https://api.imgbb.com/1/upload"
    payload = {"key": IMGBB_API_KEY}
    files = {"image": image_bytes}
    try:
        response = requests.post(url, payload, files=files)
        data = response.json()
        if data['status'] == 200:
            return data['data']['url']
        return None
    except Exception:
        return None

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = await update.message.reply_text("📡 **UPLOADING TO SERVER... ⏳**")
    
    # লোডিং অ্যানিমেশন
    animations = ["📡 **UPLOADING: [■■□□□□] 30%**", "📡 **UPLOADING: [■■■■■□] 80%**", "⚡ **FINALIZING...**"]
    for frame in animations:
        await asyncio.sleep(0.5)
        try: await msg.edit_text(frame)
        except: pass

    try:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        hosting_link = await upload_to_imgbb(image_bytes)

        if hosting_link:
            # অর্ডার কাউন্ট বাড়ানো
            total_orders = increment_order()
            
            # অ্যাডমিনকে সাকসেস নোটিফিকেশন পাঠানো
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📦 **নতুন অর্ডার সফল!**\n\nইউজার: {user.first_name}\nআইডি: `{user.id}`\nলিংক: {hosting_link}\n\n📊 **মোট সফল হোস্টিং:** {total_orders}টি"
            )

            response_msg = (
                f"✅ **HOSTING SUCCESSFUL!**\n\n"
                f"🔗 **IMAGE LINK:**\n"
                f"`{hosting_link}`\n\n"
                f"👆 **লিংকটি কপি করতে উপরের লিংকের ওপর আলতো করে চাপ দিন।**\n\n"
                f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                f"📱 **বন্ধুদের সাথে শেয়ার করুন:**\n"
                f"কপি করা লিংকটি আপনি এখন WhatsApp, Messenger, Facebook, IMO বা যেকোনো সোশ্যাল মিডিয়ায় শেয়ার করতে পারবেন।\n\n"
                f"🌍 **ছবি দেখতে:**\n"
                f"লিংকটি কপি করে আপনার ফোনের ব্রাউজারে বা গুগল সার্চে পেস্ট করলেই ছবিটি দেখতে পাবেন।\n"
                f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
                f"👤 **Developer:** Black Herix\n"
                f"🚀 **Powered By:** Mirzapur Cyber Venom"
            )
            keyboard = [[InlineKeyboardButton("👁‍🗨 View Image", url=hosting_link)]]
            await msg.edit_text(response_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            await msg.edit_text("❌ **ERROR!** আপলোড ব্যর্থ হয়েছে।")
    except Exception as e:
        logging.error(f"Handling photo failed: {e}")
        await msg.edit_text("⚠️ **CRITICAL ERROR...**")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        context.user_data['is_broadcasting'] = True
        await update.message.reply_text("📡 **Enter Broadcast Message:**", reply_markup=ReplyKeyboardRemove())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID and context.user_data.get('is_broadcasting'):
        msg_text = update.message.text
        context.user_data['is_broadcasting'] = False
        with open(USERS_FILE, "r") as f:
            users = f.read().splitlines()
        sent = 0
        for uid in users:
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 **BROADCAST:**\n\n{msg_text}", parse_mode='Markdown')
                sent += 1
            except: pass
        await update.message.reply_text(f"✅ **SUCCESS:** {sent} জনকে পাঠানো হয়েছে।")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    print("বট চলছে... সিস্টেম অনলাইন।")
    app.run_polling()
