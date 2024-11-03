import json
import ccxt
import pandas as pd
from typing import List, Dict, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ExchangeAnalyzer:
    def __init__(self, binance_credentials: Dict = None, okx_credentials: Dict = None):
        # Initialize Binance with credentials if provided
        self.binance = ccxt.binance(binance_credentials) if binance_credentials else ccxt.binance()
        
        # Initialize OKX with credentials if provided
        self.okx = ccxt.okx(okx_credentials) if okx_credentials else ccxt.okx()
        
        # Validate that we have API credentials if provided
        if binance_credentials:
            self.binance.check_required_credentials()
        if okx_credentials:
            self.okx.check_required_credentials()

    async def get_common_margin_pairs(self) -> List[str]:
        """Get trading pairs available on both exchanges with margin support"""
        
        # Fetch markets data from both exchanges
        binance_markets = self.binance.load_markets()

        okx_markets = self.okx.load_markets()
        # print(okx_markets)
        
        # Get USDT pairs with margin trading enabled on Binance
        binance_margin_pairs = set()
        for symbol, market in binance_markets.items():
            if '/USDT' in symbol and market.get('margin', False) and market.get('spot', False):
                base = symbol.split('/')[0]
                binance_margin_pairs.add(base)
        
        # Get USDT pairs with margin trading enabled on OKX
        okx_margin_pairs = set()
        for symbol, market in okx_markets.items():
            if '/USDT' in symbol and market.get('margin', False) and market.get('spot', False):
                base = symbol.split('/')[0]
                okx_margin_pairs.add(base)
        
        # Find common pairs
        common_pairs = list(binance_margin_pairs.intersection(okx_margin_pairs))
        return common_pairs

    async def get_withdrawal_info(self, coin: str) -> Dict:
        """Get withdrawal information for a coin from both exchanges"""
        try:
            binance_networks = self.binance.fetch_deposit_withdraw_fees(codes=[coin])
            okx_networks = self.okx.fetch_deposit_withdraw_fees(codes=[coin])
            
            return {
                'coin': coin,
                'binance': binance_networks.get(coin, {}),
                'okx': okx_networks.get(coin, {})
            }
        except Exception as e:
            print(f"Error fetching withdrawal info for {coin}: {str(e)}")
            return None

    def find_best_withdrawal_chain(self, withdrawal_info: Dict) -> Dict:
        """Find the chain with lowest withdrawal fee"""
        if not withdrawal_info:
            return None
            
        coin = withdrawal_info['coin']
        binance_networks = withdrawal_info['binance'].get('networks', {})
        okx_networks = withdrawal_info['okx'].get('networks', {})
        
        best_chain = None
        lowest_max_fee = float('inf')
        
        # Compare fees across all available networks
        for network_id, binance_network in binance_networks.items():
            # Get Binance withdrawal fee
            binance_fee = float(binance_network.get('withdraw', {}).get('fee', float('inf')))
            
            # Find corresponding network on OKX
            okx_network = okx_networks.get(network_id)
            
            if okx_network:
                okx_fee = float(okx_network.get('withdraw', {}).get('fee', float('inf')))
                max_fee = max(binance_fee, okx_fee)
                
                if max_fee < lowest_max_fee:
                    lowest_max_fee = max_fee
                    best_chain = {
                        'coin': coin,
                        'network': network_id,
                        'max_fee': max_fee,
                        'binance_fee': binance_fee,
                        'okx_fee': okx_fee
                    }
        
        return best_chain

    async def analyze_withdrawal_options(self) -> List[Dict]:
        """Main function to analyze and sort withdrawal options"""
        # Get common pairs
        common_pairs = await self.get_common_margin_pairs()
        
        # Fetch withdrawal info for all pairs
        withdrawal_infos = []
        for coin in common_pairs:
            info = await self.get_withdrawal_info(coin)
            if info:
                withdrawal_infos.append(info)
        
        # Find best chains for each coin
        best_chains = []
        for info in withdrawal_infos:
            best_chain = self.find_best_withdrawal_chain(info)
            if best_chain:
                best_chains.append(best_chain)
        
        # Sort by maximum withdrawal fee
        sorted_chains = sorted(best_chains, key=lambda x: x['max_fee'])
        return sorted_chains

async def main():
    # Example credentials structure
    binance_credentials = {
        'apiKey': 'J1hIqDkJVj44CvEiOtgMA9VYMF911kV7oq70YLvQNq2EdHZjTDiP33T53vWt9awc',
        'secret': 'lQEkT8dg1efseKMx8ulP7meeHGSmqjm1yxXxpdJBzcCkHpQf5F482IwGhNM94xoL'
    }
    
    okx_credentials = {
        'apiKey': '35f981b7-3c48-46d4-9bc5-bed14ce5b82e',
        'secret': '4B5C817A781E7DDA7ED7D82215AB3213',
        'password': 'Reform@781'  # OKX specific requirement
    }
    
    analyzer = ExchangeAnalyzer(
        binance_credentials=binance_credentials,
        okx_credentials=okx_credentials
    )
    results = await analyzer.analyze_withdrawal_options()
    
    # Convert to DataFrame for better visualization
    df = pd.DataFrame(results)
    print("\nSorted withdrawal options:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    asyncio.run(main()) 