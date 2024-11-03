import json
import requests
from typing import Dict
from datetime import datetime

def fetch_binance_prices() -> Dict[str, float]:
    """Fetch current prices for all tokens against USDT from Binance API"""
    try:
        # Get all USDT trading pairs prices from Binance
        response = requests.get('https://api.binance.com/api/v3/ticker/price')
        if response.status_code != 200:
            raise Exception(f"Binance API error: {response.status_code}")
            
        prices_data = response.json()
        
        # Create a dictionary of token prices in USDT
        prices = {}
        for item in prices_data:
            symbol = item['symbol']
            if symbol.endswith('USDT'):
                token = symbol[:-4]  # Remove 'USDT' from the end
                prices[token] = float(item['price'])
        
        return prices
        
    except Exception as e:
        print(f"Error fetching prices from Binance: {e}")
        return {}

def convert_fees_to_usdt():
    # Load the fees.json file
    with open('fees.json', 'r') as f:
        fees_data = json.load(f)
    
    # Fetch current prices
    prices = fetch_binance_prices()
    
    # Create new dictionary with USDT values
    fees_in_usdt = {}
    timestamp = datetime.utcnow().isoformat()
    
    for token, data in fees_data.items():
        try:
            price = prices.get(token)
            if price:
                usdt_fee = data['withdrawal_fee'] * price
                fees_in_usdt[token] = {
                    "network": data['network'],
                    "withdrawal_fee": data['withdrawal_fee'],
                    "withdrawal_fee_usdt": round(usdt_fee, 2),
                    "price_usdt": price
                }
            else:
                fees_in_usdt[token] = {
                    "network": data['network'],
                    "withdrawal_fee": data['withdrawal_fee'],
                    "withdrawal_fee_usdt": None,
                    "price_usdt": None
                }
        except Exception as e:
            print(f"Error processing {token}: {e}")
    
    # Save to new file with timestamp
    output = {
        "timestamp": timestamp,
        "fees": fees_in_usdt
    }
    
    with open('fees_usdt.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    available_prices = sum(1 for token in fees_in_usdt if fees_in_usdt[token]["price_usdt"] is not None)
    print(f"Processed {len(fees_in_usdt)} tokens")
    print(f"Found prices for {available_prices} tokens")
    print(f"Missing prices for {len(fees_in_usdt) - available_prices} tokens")

if __name__ == "__main__":
    convert_fees_to_usdt() 