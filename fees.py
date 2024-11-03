import json

with open('withdrawal_infos.json', 'r') as f:
    data = json.load(f)

    COIN_NETWORKS = {
    "BTC": {
        "network": "BTC",  # Bitcoin native network
        "addresses": {
            "binance": "your_binance_btc_address",
            "okx": "your_okx_btc_address"
        },
        "withdrawal_fee": 0  # BTC
    }}

    # Find lowest fee network available on both exchanges

    for coin_info in data:
        lowest_fee = float('inf')
        best_network = None
        coin = coin_info['coin']
        binance_networks = coin_info['binance'].get('networks', {})
        okx_networks = coin_info['okx'].get('networks', {})
        
        # Compare fees across networks available on both exchanges
        for key, value in binance_networks.items():
            network_id = key
            binance_fee = float(value["withdraw"].get('fee', float('inf')))
            
            # Find matching network on OKX
            okx_net = next(
                (value for key, value in okx_networks.items() if key == network_id), 
                None
            )
            
            if okx_net:
                okx_fee = float(okx_net["withdraw"].get('fee', float('inf')))
                max_fee = max(binance_fee, okx_fee)
                
                if max_fee < lowest_fee:
                    lowest_fee = max_fee
                    best_network = network_id
        if best_network == None:
            print(f"No network found for {coin}")
        else:
            COIN_NETWORKS[coin] = {
                "network": best_network,
                "withdrawal_fee": lowest_fee
            }

    with open("fees.json", "w") as fp:
        json.dump(COIN_NETWORKS, fp)
