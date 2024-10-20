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
        return [{"card": card, "status": "ERROR", "message": "FAILED TO RETRIEVE DATA FROM THE SERVER."} for card in card_numbers]

@app.on_message(filters.command("start"))
def start(client, message):
    message.reply("WELCOME TO THE CARD CHECKER BOT! USE /CHK FOR A SINGLE CARD OR /MCHK FOR MULTIPLE CARDS.")

@app.on_message(filters.command("chk") & filters.user(OWNER_ID))
def chk(client, message):
    # Check if the user has provided a card number
    if len(message.command) < 2:
        message.reply("PLEASE ENTER A CARD NUMBER IN THE FORMAT: /CHK CARD_NUMBER|EXPIRY_MONTH|EXPIRY_YEAR|CVV")
        return

    card_data = message.command[1:]  # Get the card data after the command
    card_numbers = []

    for card in card_data:
        card_details = card.split('|')
        if len(card_details) == 4:
            card_numbers.append(card)

    if not card_numbers:
        message.reply("INVALID CARD FORMAT. PLEASE USE: CARD_NUMBER|EXPIRY_MONTH|EXPIRY_YEAR|CVV")
        return

    # Check the card
    result = check_cards(card_numbers)

    # Format the response
    response_message = ""

    # Process the result for a single card
    if isinstance(result, list):
        for status in result:  # Assuming we get one card status in the list
            card = status.get("card", "UNKNOWN CARD").upper()
            card_status = status.get("status", "UNKNOWN").upper()
            message_detail = status.get("message", "NO MESSAGE AVAILABLE").upper()

            # Append the appropriate emoji based on the card status
            if card_status == "APPROVED":
                card_status += " ✅"
            elif card_status == "DECLINED":
                card_status += " ❌"

            # Format each message in bold
            response_message += (
                f"**CARD: {card}**\n"
                f"**RESPONSE: {card_status}**\n"
                f"**MSG: {message_detail}**\n\n"
            )
    else:
        message.reply("UNEXPECTED RESPONSE FORMAT FROM THE SERVER.")

    # Send the formatted response
    if response_message:  # Only send if there is a message to send
        message.reply(response_message)

@app.on_message(filters.command("mchk") & filters.user(OWNER_ID))
def mchk(client, message):
    # Check if the user has provided card numbers
    if len(message.command) < 2:
        message.reply("PLEASE ENTER UP TO 25 CARD NUMBERS IN THE FORMAT: /MCHK CARD1|EXPIRY_MONTH|EXPIRY_YEAR|CVV")
        return

    # Prepare the card data from user input, limiting to 25 cards
    card_data = message.command[1:]  # Get all arguments after the command
    card_numbers = []

    for card in card_data:
        card_details = card.split('|')
        if len(card_details) == 4:
            card_numbers.append(card)

    if not card_numbers:
        message.reply("INVALID CARD FORMAT. PLEASE USE: CARD_NUMBER|EXPIRY_MONTH|EXPIRY_YEAR|CVV")
        return

    # Limit to 25 cards
    if len(card_numbers) > 25:
        message.reply("YOU CAN ONLY CHECK UP TO 25 CARDS AT A TIME.")
        return

    # Check the cards
    result = check_cards(card_numbers)

    # Format the response
    response_message = ""

    # Check if result is a list
    if isinstance(result, list):
        for status in result:  # Iterate over each card status
            card = status.get("card", "UNKNOWN CARD").upper()
            card_status = status.get("status", "UNKNOWN").upper()

            # Append the appropriate emoji based on the card status
            if card_status == "APPROVED":
                card_status += " ✅"
            elif card_status == "DECLINED":
                card_status += " ❌"

            # Format each message in bold
            response_message += (
                f"**CARD: {card}**\n"
                f"**RESPONSE: {card_status}**\n\n"
            )
    else:
        # Handle case where result is not a list, maybe log the error
        message.reply("UNEXPECTED RESPONSE FORMAT FROM THE SERVER.")

    # Send the formatted response
    if response_message:  # Only send if there is a message to send
        message.reply(response_message)

# Run the bot
if __name__ == "__main__":
    app.run()
    
