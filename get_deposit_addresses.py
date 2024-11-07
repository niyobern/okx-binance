import json
import ccxt.async_support as ccxt
import asyncio
from typing import Dict, Optional
from config import *

class DepositAddressManager:
    def __init__(self):
        # Initialize exchanges with async versions
        self.binance = ccxt.binance({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_SECRET_KEY,
            'enableRateLimit': True
        })
        
        self.okx = ccxt.okx({
            'apiKey': OKX_API_KEY,
            'secret': OKX_SECRET_KEY,
            'password': OKX_PASSPHRASE,
            'enableRateLimit': True
        })

    async def get_deposit_address(self, exchange: ccxt.Exchange, coin: str, network: Optional[str] = None) -> Dict:
        try:
            params = {'network': network} if network else {}
            address_info = await exchange.fetch_deposit_address(coin, params)
            return {
                'address': address_info.get('address'),
                'tag': address_info.get('tag'),
                'network': network or address_info.get('network'),
                'error': None
            }
        except Exception as e:
            print(f"Error getting {coin} address on {exchange.id}: {str(e)}")
            return {
                'address': None,
                'tag': None,
                'network': network,
                'error': str(e)
            }

    async def get_all_deposit_addresses(self):
        with open('sorted_fees.json', 'r') as f:
            data = json.load(f)
            fees = data['fees']

        deposit_addresses = {}

        try:
            for coin, info in fees.items():
                network = info['network']
                deposit_addresses[coin] = {
                    'binance': {},
                    'okx': {}
                }

                # Try to get addresses for both exchanges using the network info
                binance_address = await self.get_deposit_address(self.binance, coin, network)
                okx_address = await self.get_deposit_address(self.okx, coin, network)
                
                # Store the addresses
                if binance_address['address']:
                    deposit_addresses[coin]['binance'][network] = binance_address
                if okx_address['address']:
                    deposit_addresses[coin]['okx'][network] = okx_address

            return deposit_addresses
        finally:
            # Important: Close the exchange connections
            await self.binance.close()
            await self.okx.close()

    async def save_addresses(self, addresses: Dict):
        output = {
            'timestamp': self.binance.iso8601(self.binance.milliseconds()),
            'addresses': addresses
        }
        
        with open('deposit_addresses.json', 'w') as f:
            json.dump(output, f, indent=4)

async def main():
    manager = DepositAddressManager()
    addresses = await manager.get_all_deposit_addresses()
    await manager.save_addresses(addresses)

if __name__ == "__main__":
    asyncio.run(main())