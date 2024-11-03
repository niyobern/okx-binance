import ccxt
import pandas as pd
from typing import List, Dict, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ExchangeAnalyzer:
    def __init__(self):
        self.binance = ccxt.binance()
        self.okx = ccxt.okx()
        
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
        for network in binance_networks:
            network_id = network['network']
            binance_fee = float(network.get('withdrawFee', float('inf')))
            
            # Find corresponding network on OKX
            okx_network = next(
                (n for n in okx_networks if n['network'] == network_id),
                None
            )
            
            if okx_network:
                okx_fee = float(okx_network.get('withdrawFee', float('inf')))
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
    analyzer = ExchangeAnalyzer()
    results = await analyzer.analyze_withdrawal_options()
    
    # Convert to DataFrame for better visualization
    df = pd.DataFrame(results)
    print("\nSorted withdrawal options:")
    print(df.to_string(index=False))

if __name__ == "__main__":
    asyncio.run(main()) 