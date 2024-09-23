import time
import logging
from decimal import Decimal, ROUND_DOWN
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException, BinanceRequestException

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Binance client
api_key = "VOTRE_API_KEY"
api_secret = "VOTRE_SECRET_KEY"
client = Client(api_key, api_secret)

Sell_b = False
Buy_b = False
target_price_top = 63300
target_price_low = 62520
BorS = True
fib_sequence = [0.0001, 0.0002, 0.0003, 0.0005, 0.0008, 0.0013, 0.0021]
fib_index = 0

def check_last_order_and_reset(order_id, btc_price):
    global fib_index, Buy_b, Sell_b, target_price_low, target_price_top
    
    try:
        if order_id != None:
            order = client.get_order(symbol='BTCUSDC', orderId=order_id)
            if order['status'] == 'FILLED':
                logging.info(f"Order {order_id} was filled successfully.")
                order_id = None
                if fib_index < 6:
                    fib_index += 1
                
                if Sell_b == True and Buy_b == False:
                    target_price_low = target_price_top - 810
                    with open('log_bot.txt', 'a') as file:
                        file.write(f'Vente réalisé à : {time.strftime("%Y-%m-%d %H:%M:%S")} de {fib_sequence[fib_index - 1]} BTC ; équivalent à {(target_price_top - 152) * fib_sequence[fib_index - 1]} USDC\n')
                    print("\nNouvelle zone basse à :  ", target_price_low, "  USDC\n")
                
                if Sell_b == False and Buy_b == True:
                    target_price_top = target_price_low + 810
                    with open('log_bot.txt', 'a') as file:
                        file.write(f'Achat réalisé à : {time.strftime("%Y-%m-%d %H:%M:%S")} de {fib_sequence[fib_index - 1]} BTC ; équivalent à {(target_price_low + 152) * fib_sequence[fib_index - 1]} USDC\n')
                    print("\nNouvelle zone haute à :  ", target_price_top, "  USDC\n")
                
                if Sell_b == True and Buy_b == True:
                    if btc_price == target_price_low:
                        target_price_top = target_price_low + 810
                        with open('log_bot.txt', 'a') as file:
                            file.write(f'Vente réalisé à : {time.strftime("%Y-%m-%d %H:%M:%S")} de {fib_sequence[fib_index - 1]} BTC ; équivalent à {(target_price_top - 152) * fib_sequence[fib_index - 1]} USDC\n')
                        print("\nNouvelle zone haute à :  ", target_price_top, "  USDC\n")
                    else:
                        target_price_low = target_price_top - 810
                        with open('log_bot.txt', 'a') as file:
                            file.write(f'Achat réalisé à : {time.strftime("%Y-%m-%d %H:%M:%S")} de {fib_sequence[fib_index - 1]} BTC ; équivalent à {(target_price_low + 152) * fib_sequence[fib_index - 1]} USDC\n')
                        print("\nNouvelle zone basse à :  ", target_price_top, "  USDC\n")
                    
                    print("REINITIALIZATION DU FIB_INDEX\n")
                    Sell_b = False
                    Buy_b = False
                    fib_index = 0
            
    except BinanceAPIException as e:
        logging.error(f"Failed to fetch order {order_id}: {e}")
    
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    return order_id


def visit_order(BorS):
    open_orders = client.get_open_orders(symbol="BTCUSDC")
    if open_orders:
        for order in open_orders:
            if order['side'] == 'SELL' and BorS == True:
                order_id = order['orderId']
                client.cancel_order(symbol="BTCUSDC", orderId=order_id)
                logging.info(f"Canceled existing order: {order_id} SELL")
            if order['side'] == 'BUY' and BorS == False:
                order_id = order['orderId']
                client.cancel_order(symbol="BTCUSDC", orderId=order_id)
                logging.info(f"Canceled existing order: {order_id} BUY")


def push_order(price_to_push, BorS, current_fib_value):
    balance = client.get_asset_balance(asset='BTC')
    if BorS == True and float(balance['free']) >= current_fib_value:
        order = client.create_order(
            symbol="BTCUSDC",
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
            quantity=current_fib_value,
            price=str(price_to_push - 152),
            stopPrice=str(price_to_push - 150),
            timeInForce=Client.TIME_IN_FORCE_GTC
        )
        print("\nSUCESSFULL SELL ORDER : ", current_fib_value, "BTC\n")
        return order['orderId']

    balance = client.get_asset_balance(asset='USDC')
    if BorS == False and float(balance['free']) >= current_fib_value * (price_to_push + 145):
        order = client.create_order(
            symbol="BTCUSDC",
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_STOP_LOSS_LIMIT,
            quantity=current_fib_value,
            price=str(price_to_push + 152),
            stopPrice=str(price_to_push + 150),
            timeInForce=Client.TIME_IN_FORCE_GTC
        )
        print("\nSUCESSFULL BUY ORDER : ", current_fib_value, "BTC ; Equivalent to : ", (float(current_fib_value) * float((price_to_push + 145))), " USDC\n")
        return order['orderId']
    print("\nPAS ASSEZ DE FOND !\n")
    return None


def monitor_price_and_sell():
    global target_price_top, countTurn, target_price_low, Buy_b, Sell_b
    
    order_id = None

    while True:
        try:
            btc_price = float(client.get_symbol_ticker(symbol="BTCUSDC")['price'])
            if btc_price > target_price_top:
                visit_order(True)
                target_price_top = btc_price
                order_id = push_order(btc_price, True, fib_sequence[fib_index])
                Sell_b = True
                
            if btc_price < target_price_low:
                visit_order(False)
                target_price_low = btc_price
                order_id = push_order(btc_price, False, fib_sequence[fib_index])
                Buy_b = True         

            order_id = check_last_order_and_reset(order_id, btc_price)
            
            time.sleep(0.05)

        # Handle network issues
        except BinanceRequestException as e:
            logging.error(f"Network error: {e}. Retrying in 5 seconds.")
            time.sleep(5)
        
        # Handle API rate limits
        except BinanceAPIException as e:
            if e.status_code == 429:
                logging.error(f"Rate limit exceeded: {e}. Waiting 1 minute.")
                time.sleep(60)
            else:
                logging.error(f"Binance API error: {e}")
        
        # Handle order execution issues
        except BinanceOrderException as e:
            logging.error(f"Order failed: {e}")
            time.sleep(5)
        
        # General error handling
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(5)

# Run the monitoring function
monitor_price_and_sell()
