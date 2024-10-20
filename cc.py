import requests
from pyrogram import Client, filters

# Replace these with your actual API ID, API HASH, and BOT TOKEN
API_ID = 24509589
API_HASH = "717cf21d94c4934bcbe1eaa1ad86ae75"
BOT_TOKEN = "7386696229:AAETBUAX4p2QdMQmr6b9NbZc_vOJx4uQOi0"

# Your Telegram ID (owner ID)
OWNER_ID = 7427691214

# Initialize the bot
app = Client("card_checker_bot", bot_token=BOT_TOKEN)

# Function to check card details
def check_cards(card_numbers):
    url = "http://154.12.225.214:1440/check_cards"
    data = {"cards": card_numbers}
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to retrieve data from the server."}

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply("Welcome to the Card Checker Bot! Use /chk followed by your card details.")

@app.on_message(filters.command("chk") & filters.user(OWNER_ID))
def chk(client, message):
    # Check if the user has provided card numbers
    if len(message.command) < 2:
        message.reply("Please enter card numbers in the format: /chk card1|expiry_month|expiry_year|cvv")
        return

    # Prepare the card data from user input
    card_data = message.command[1:]  # Get all arguments after the command
    card_numbers = []

    for card in card_data:
        card_details = card.split('|')
        if len(card_details) == 4:
            card_numbers.append(card)

    if not card_numbers:
        message.reply("Invalid card format. Please use: card_number|expiry_month|expiry_year|cvv")
        return

    # Check the cards
    result = check_cards(card_numbers)

    # Format the response
    response_message = ""
    for card, status in zip(card_numbers, result.get("results", [])):
        card_status = status.get("status", "Unknown")
        message_detail = status.get("message", "No message available")
        
        if card_status.lower() == "approved":
            # Assuming a fixed price for approved cards
            price = "1$"
            response_message += (
                f"┏━━━━━━━⍟\n"
                f"┃# CHARGE {price} ✅\n"
                f"┗━━━━━━━━━━━⊛\n"
                f"CARD: {card}\n"
                f"RESPONSE: {card_status}\n"
                f"MSG: {message_detail}\n\n"
            )
        else:
            response_message += (
                f"┏━━━━━━━⍟\n"
                f"┃# DEAD ❌\n"
                f"┗━━━━━━━━━━━⊛\n"
                f"CARD: {card}\n"
                f"RESPONSE: {card_status}\n"
                f"MSG: {message_detail}\n\n"
            )

    # Send the formatted response
    message.reply(response_message)

# Run the bot
if __name__ == "__main__":
    app.run()
    
