import requests
from pyrogram import Client, filters

# Your API ID and Hash
API_ID = 24509589
API_HASH = "717cf21d94c4934bcbe1eaa1ad86ae75"
BOT_TOKEN = "7386696229:AAETBUAX4p2QdMQmr6b9NbZc_vOJx4uQOi0"

# Your Telegram ID (owner ID)
OWNER_ID = 7427691214

# Initialize the bot with API ID and Hash
app = Client("card_checker_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Function to check card details
def check_cards(card_numbers):
    url = "http://154.12.225.214:1440/check_cards"
    data = {"cards": card_numbers}
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()  # This should return the response JSON
    else:
        return [{"card": card, "status": "error", "message": "Failed to retrieve data from the server."} for card in card_numbers]

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply("Welcome to the Card Checker Bot! Use /mchk followed by your card details.")

@app.on_message(filters.command("mchk") & filters.user(OWNER_ID))
def mchk(client, message):
    # Check if the user has provided card numbers
    if len(message.command) < 2:
        message.reply("Please enter up to 25 card numbers in the format: /mchk card1|expiry_month|expiry_year|cvv")
        return

    # Prepare the card data from user input, limiting to 25 cards
    card_data = message.command[1:]  # Get all arguments after the command
    card_numbers = []

    for card in card_data:
        card_details = card.split('|')
        if len(card_details) == 4:
            card_numbers.append(card)

    if not card_numbers:
        message.reply("Invalid card format. Please use: card_number|expiry_month|expiry_year|cvv")
        return

    # Limit to 25 cards
    if len(card_numbers) > 25:
        message.reply("You can only check up to 25 cards at a time.")
        return

    # Check the cards
    result = check_cards(card_numbers)

    # Format the response
    response_message = ""

    # Check if result is a list
    if isinstance(result, list):
        for status in result:  # Iterate over each card status
            card = status.get("card", "Unknown Card")
            card_status = status.get("status", "Unknown")

            # Format each message in bold
            response_message += (
                f"**CARD: {card}**\n"
                f"**RESPONSE: {card_status}**\n\n"
            )
    else:
        # Handle case where result is not a list, maybe log the error
        message.reply("Unexpected response format from the server.")

    # Send the formatted response
    if response_message:  # Only send if there is a message to send
        message.reply(response_message)

# Run the bot
if __name__ == "__main__":
    app.run()
    
