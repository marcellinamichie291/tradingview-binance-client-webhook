import json, config, requests
from math import floor
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET)

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print(f"sending order {order_type} - {side} {quantity} {symbol}")

        #example order (not futures)
        """ order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity) """

        #client.futures_change_margin_type(symbol=symbol, marginType='CROSSED')
        #client.futures_change_leverage(symbol=symbol, leverage=10)
        order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']
    symbol = data['ticker']
    stratname = data['stratname']
    
    price = data['strategy']['order_price']

    fixsymbol = str.replace(symbol, "PERP", '')
    #fixprice = floor(price)

    order_response = order(side, quantity, fixsymbol)

    indexopen = data['bar']['open']
    indexclose = data['bar']['close']
    indexhigh = data['bar']['high']
    indexvol = data['bar']['volume']
    membership = data['membership']

    # if a DISCORD URL is set in the config file, we will post to the discord webhook
    if config.DISCORD_WEBHOOK_URL:
        chat_message = {
        "embeds": [
            {      
            "title": f"{fixsymbol} {side} @ {price}",
            "color": 486113,
            "description": f"open: {indexopen}\nhigh: {indexhigh}\nlow: {indexvol}\nclose: {indexclose}\nvolume: {indexvol}\n @everyone",
            "fields": [
                    {
                    "name": "From",
                                "value": f"***{stratname}***"
                    }
                ]
            }
        ]
    }
        if membership == 'pro':
            requests.post(config.DISCORDPRO_WEBHOOK_URL, json=chat_message)
        else:
            requests.post(config.DISCORD_WEBHOOK_URL, json=chat_message)

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }

    