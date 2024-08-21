import requests
import time
import json
from flask import Flask, request

app = Flask(__name__)

@app.route('/charge', methods=['GET'])
def charge():
    start_time = time.time()

    # Retrieve query parameters
    card = request.args.get('lista', '')
    mode = request.args.get('mode', 'cvv')
    amount = int(request.args.get('amount', 1))
    currency = request.args.get('currency', 'usd')
    description = request.args.get('description', 'Charge for product/service')

    if not card:
        return "Please enter a card number", 400

    split = card.split('|')
    cc = split[0] if len(split) > 0 else ''
    mes = split[1] if len(split) > 1 else ''
    ano = split[2] if len(split) > 2 else ''
    cvv = split[3] if len(split) > 3 else ''

    if not all([cc, mes, ano, cvv]):
        return "Invalid card details", 400

    pk = 'pk_live_51NMaIoB3ax5X6jqufvt3PIUdq1R5tZN3zBahVcAblhqSNYDmmTocFYfwc5AfRrFR0iBUZ16UrPe6AKccfAdcvt3700CotHbQDY'
    sk = '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'

    # Create token
    token_data = {
        'card[number]': cc,
        'card[exp_month]': mes,
        'card[exp_year]': ano,
        'card[cvc]': cvv
    }
    
    token_response = requests.post(
        'https://api.stripe.com/v1/tokens',
        data=token_data,
        headers={'Authorization': f'Bearer {pk}', 'Content-Type': 'application/x-www-form-urlencoded'}
    )

    if token_response.status_code != 200:
        return f"Error: {token_response.text}", 500

    token_data = token_response.json()
    if 'error' in token_data:
        return f"Error: {token_data['error']['message']}", 400

    token_id = token_data.get('id')
    if not token_id:
        return "Token creation failed", 500

    # Prepare charge data
    charge_data = {
        'amount': amount * 100,
        'currency': currency,
        'source': token_id,
        'description': description,
        'metadata[integration_check]': 'accept_a_payment'
    }

    # Create charge
    charge_response = requests.post(
        'https://api.stripe.com/v1/charges',
        data=charge_data,
        headers={'Authorization': f'Bearer {sk}', 'Content-Type': 'application/x-www-form-urlencoded'}
    )

    charge_data = charge_response.json()
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)

    # Handle response
    if charge_response.status_code == 200 and charge_data.get('status') == 'succeeded':
        response_text = "#𝗖𝗛𝗔𝗥𝗚𝗘 $1 ✅"
        message = "𝗣𝗔𝗬𝗠𝗘𝗡𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗙𝗨𝗟 ✅"
    elif 'error' in charge_data:
        error_message = charge_data['error'].get('message', 'UNKNOWN ERROR').upper()
        if "Your card's security code is incorrect." in error_message:
            response_text = "#𝗔𝗣𝗣𝗥𝗢𝗩𝗘𝗗 1$ ✅"
            message = "𝗖𝗖𝗡 𝗟𝗜𝗩𝗘 ✅"
        elif 'insufficient funds' in error_message:
            response_text = "#𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 1$ ✅"
            message = "𝗜𝗡𝗦𝗨𝗙𝗙𝗜𝗖𝗜𝗘𝗡𝗧 𝗙𝗨𝗡𝗗𝗦 ❎"
        elif 'card does not support this purchase' in error_message:
            response_text = "#𝗔𝗽𝗽𝗿𝗼𝘃𝗲𝗱 1$ ✅"
            message = "𝗖𝗔𝗥𝗗 𝗗𝗢𝗘𝗦𝗡'𝗧 𝗦𝗨𝗣𝗣𝗢𝗥𝗧 𝗣𝗨𝗥𝗖𝗛𝗔𝗦𝗘 ❎"
        else:
            response_text = "𝗗𝗘𝗖𝗟𝗜𝗡𝗘𝗗 ❌️"
            message = error_message
    else:
        response_text = "Unknown response"
        message = "Unknown error occurred"

    result = f"┏━━━━━━━⍟\n┃{response_text}\n┗━━━━━━━━━━━⊛\n𝗖𝗔𝗥𝗗:- {card}\n𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘:- {message}\n𝗚𝗔𝗧𝗘:- ＣＶＶ ＣＨＡＲ𝗚𝗘 \n"
    result += f"𝗧𝗶𝗺𝗲: {elapsed_time} seconds\n"

    log_response(card, response_text, message, elapsed_time, description, check_card_issuer(cc))

    return result

def log_response(card, response, msg, time, description, issuer):
    log_data = {
        'card': card,
        'response': response,
        'message': msg,
        'execution_time': time,
        'description': description,
        'issuer': issuer,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    with open('enhanced_log.txt', 'a') as log_file:
        log_file.write(json.dumps(log_data) + '\n')

def check_card_issuer(cc):
    issuers = {
        '4': 'Visa',
        '5': 'MasterCard',
        '3': 'American Express',
        '6': 'Discover'
    }
    return issuers.get(cc[0], 'Unknown')

def validate_card_format(cc):
    return len(cc) == 16 and cc.isdigit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1490)
