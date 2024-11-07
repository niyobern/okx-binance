import asyncio
import aiohttp
import ssl
from decimal import Decimal
from trading_manager import TradingManager
from websocket_handlers import WebSocketHandler
from exchange_operations import BinanceOperations, OKXOperations
from config import (
    BINANCE_WS, OKX_WS,
    BINANCE_DEMO_WS, OKX_DEMO_WS,
    BINANCE_BASE_URL, OKX_BASE_URL,
    BINANCE_DEMO_BASE_URL, OKX_DEMO_BASE_URL,
    SYMBOLS, COIN_NETWORKS, TRADING_MODE
)

class ArbitrageBot:
    def __init__(self, mode="demo"):
        if mode == "demo":
            print("\n" + "="*50)
            print("🚨 RUNNING IN DEMO MODE 🚨")
            print("="*50 + "\n")
        # Constants
        self.mode = mode
        if mode == "demo":
            self.BINANCE_WS = BINANCE_DEMO_WS
            self.OKX_WS = OKX_DEMO_WS
            self.BINANCE_API = f"{BINANCE_DEMO_BASE_URL}/api/v3/ticker/price"
            self.OKX_API = f"{OKX_DEMO_BASE_URL}/market/tickers"
        else:
            self.BINANCE_WS = BINANCE_WS
            self.OKX_WS = OKX_WS
            self.BINANCE_API = f"{BINANCE_BASE_URL}/api/v3/ticker/price"
            self.OKX_API = f"{OKX_BASE_URL}/market/tickers"

        # Instance variables
        self.binance_prices = {}
        self.okx_prices = {}
        self.trading_manager = TradingManager(initial_capital=2000)
        self.min_trade_amount = 100
        self.max_spread_percentage = Decimal('5')
        self.SYMBOLS = SYMBOLS
        
        # Operations with mode
        self.binance_ops = BinanceOperations(mode=mode)
        self.okx_ops = OKXOperations(mode=mode)
        self.ws_handler = WebSocketHandler(self)

    async def execute_arbitrage(self, symbol, binance_price, okx_price):
        """Execute arbitrage trades if conditions are met"""
        try:
            if not self.trading_manager.can_open_position():
                return False

            # Convert prices to Decimal for precise calculations
            try:
                binance_price = Decimal(str(binance_price))
                okx_price = Decimal(str(okx_price))
            except Exception as e:
                print(f"Error converting prices to Decimal for {symbol}: {e}")
                print(f"Binance price: {binance_price}, OKX price: {okx_price}")
                return False
                
            # Calculate spread percentage
            avg_price = (binance_price + okx_price) / 2
            spread_percentage = abs(binance_price - okx_price) / avg_price * 100

            # Extract base currency from symbol (e.g., "BTC" from "BTCUSDT")
            try:
                coin = symbol[:-4]  # Remove 'USDT' from the end
                if coin not in COIN_NETWORKS:
                    print(f"Warning: {coin} not found in COIN_NETWORKS configuration")
                    return False
            except Exception as e:
                print(f"Error extracting coin from symbol {symbol}: {e}")
                return False
            
            # Calculate quantity based on available capital
            try:
                quantity = self.trading_manager.calculate_position_size(buy_price)
                total_cost = quantity * buy_price
                
                if total_cost < self.min_trade_amount:
                    print(f"Trade amount {total_cost} below minimum {self.min_trade_amount} for {symbol}")
                    return False
            except Exception as e:
                print(f"Error calculating position size for {symbol}: {e}")
                return False

            # Determine which exchange has better prices for buying and selling
            if binance_price < okx_price:
                buy_exchange = 'binance'
                sell_exchange = 'okx'
                buy_price = binance_price
                sell_price = okx_price
                
                # Order execution functions for this direction
                spot_buy = self.binance_ops.place_spot_market_buy
                margin_sell = self.okx_ops.place_margin_market_short
                
                if self.mode == "live":
                    crypto_transfer = self.binance_ops.withdraw_crypto
                    repay_loan = self.okx_ops.repay_margin_loan
                    usdt_transfer = self.okx_ops.transfer_usdt
                
                to_exchange = 'okx'
                usdt_return_exchange = 'binance'
                
            else:
                buy_exchange = 'okx'
                sell_exchange = 'binance'
                buy_price = okx_price
                sell_price = binance_price
                
                # Order execution functions for this direction
                spot_buy = self.okx_ops.place_spot_market_buy
                margin_sell = self.binance_ops.place_margin_market_short
                
                if self.mode == "live":
                    crypto_transfer = self.okx_ops.withdraw_crypto
                    repay_loan = self.binance_ops.repay_margin_loan
                    usdt_transfer = self.binance_ops.transfer_usdt
                
                to_exchange = 'binance'
                usdt_return_exchange = 'okx'

            # Calculate fees and potential profit
            withdrawal_fee = COIN_NETWORKS[coin]['withdrawal_fee']
            usdt_withdrawal_fee = COIN_NETWORKS['USDT']['withdrawal_fee']
            total_transfer_fees = withdrawal_fee + usdt_withdrawal_fee
            
            trading_fees = Decimal('0.2')  # 0.1% per trade
            total_fee_percentage = trading_fees + (total_transfer_fees / (quantity * buy_price) * 100)
            profit_percentage = spread_percentage - total_fee_percentage
            
            if (profit_percentage > self.trading_manager.min_profit_percentage and
                spread_percentage <= self.max_spread_percentage):
                
                print(f"\nExecuting arbitrage for {symbol}")
                print(f"Buy on {buy_exchange.upper()} at {buy_price}")
                print(f"Sell on {sell_exchange.upper()} at {sell_price}")
                print(f"Spread: {spread_percentage:.2f}%")
                print(f"Expected profit after fees: {profit_percentage:.2f}%")
                
                try:
                    # Execute both orders concurrently
                    spot_order, margin_order = await asyncio.gather(
                        spot_buy(symbol, quantity),
                        margin_sell(symbol, quantity)
                    )
                    
                    if not self._verify_market_orders(spot_order, margin_order):
                        print(f"Market orders failed verification for {symbol}")
                        return False
                        
                    # Rest of the execution logic...
                    return True
                    
                except Exception as e:
                    print(f"Error executing orders for {symbol}: {e}")
                    return False
                    
            return False
                
        except Exception as e:
            print(f"Error in execute_arbitrage for {symbol}: {e}")
            print(f"Full error details: {str(e)}")
            return False

    def _verify_market_orders(self, spot_order, margin_order):
        """Verify that both market orders were filled successfully"""
        try:
            # Adjust these conditions based on actual API responses
            spot_filled = spot_order.get('status') == 'FILLED'
            margin_filled = margin_order.get('status') == 'FILLED'
            
            if not spot_filled:
                print("Spot market order failed to fill!")
            if not margin_filled:
                print("Margin market order failed to fill!")
                
            return spot_filled and margin_filled
        except Exception as e:
            print(f"Error verifying market orders: {e}")
            return False

    async def fetch_initial_prices(self):
        """Fetch initial prices from both exchanges"""
        try:
            # Create SSL context that skips verification
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                # Binance prices
                binance_url = "https://api.binance.com/api/v3/ticker/price"
                async with session.get(binance_url) as response:
                    binance_data = await response.json()
                    self.binance_prices = {item['symbol']: float(item['price']) for item in binance_data}

                # OKX prices
                okx_url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
                async with session.get(okx_url) as response:
                    okx_data = await response.json()
                    # Process OKX data
                    if okx_data.get('code') == '0':  # Check if request was successful
                        self.okx_prices = {
                            item['instId'].replace('-', ''): float(item['last'])
                            for item in okx_data.get('data', [])
                        }
                    else:
                        print(f"Error fetching OKX prices: {okx_data}")

            print("✅ Initial prices fetched successfully")
            
        except Exception as e:
            print(f"❌ Error fetching initial prices: {str(e)}")
            raise

    def _validate_symbol(self, symbol):
        """Validate that a symbol is properly formatted and supported"""
        try:
            if not isinstance(symbol, str):
                return False
                
            if len(symbol) < 5:  # Minimum length for any valid symbol
                return False
                
            if not symbol.endswith('USDT'):
                return False
                
            base_currency = symbol[:-4]
            if base_currency not in COIN_NETWORKS:
                return False
                
            return True
        except Exception as e:
            print(f"Error validating symbol {symbol}: {e}")
            return False

    async def check_arbitrage(self, symbol):
        """Check for arbitrage opportunities"""
        try:
            # Validate symbol first
            if not self._validate_symbol(symbol):
                return
                
            # Ensure we're using the standard format (without hyphen)
            standard_symbol = symbol.replace('-', '')
            
            if standard_symbol in self.binance_prices and standard_symbol in self.okx_prices:
                binance_price = self.binance_prices[standard_symbol]
                okx_price = self.okx_prices[standard_symbol]
                
                if not (binance_price and okx_price):  # Check for valid prices
                    return
                    
                diff = abs(binance_price - okx_price)
                avg_price = (binance_price + okx_price) / 2
                spread_percentage = (diff / avg_price) * 100

                # Calculate basic fees
                trading_fees = 0.2  # 0.1% per trade
                coin = standard_symbol[:-4]
                
                if coin in COIN_NETWORKS:
                    withdrawal_fee = COIN_NETWORKS[coin]['withdrawal_fee']
                    usdt_withdrawal_fee = COIN_NETWORKS['USDT']['withdrawal_fee']
                    total_transfer_fees = withdrawal_fee + usdt_withdrawal_fee
                    
                    # Estimate fee impact based on a standard trade size of 1000 USDT
                    fee_impact = (total_transfer_fees / 1000) * 100
                    total_fee_percentage = trading_fees + fee_impact
                    potential_profit = spread_percentage - total_fee_percentage

                    # Log all spreads above 0.1%
                    if spread_percentage >= 0.1:
                        print(f"\nPotential arbitrage for {standard_symbol}:")
                        print(f"Binance: {binance_price:.8f}")
                        print(f"OKX: {okx_price:.8f}")
                        print(f"Spread: {spread_percentage:.3f}%")
                        print(f"Est. fees: {total_fee_percentage:.3f}%")
                        print(f"Potential profit: {potential_profit:.3f}%")
                        
                        if potential_profit > self.trading_manager.min_profit_percentage:
                            print("🚀 EXECUTING ARBITRAGE!")
                            await self.execute_arbitrage(standard_symbol, binance_price, okx_price)
                        else:
                            print("❌ Spread too small after fees")

        except Exception as e:
            print(f"Error checking arbitrage for {symbol}: {e}")

    async def run(self):
        """Start the arbitrage bot"""
        await self.fetch_initial_prices()
        await asyncio.gather(
            self.ws_handler.binance_handler(),
            self.ws_handler.okx_handler()
        )

    def _verify_loan_repayment(self, repay_response):
        """Verify that the margin loan was successfully repaid"""
        try:
            # Adjust these conditions based on actual API responses
            if isinstance(repay_response, dict):
                # For Binance
                if 'status' in repay_response:
                    return repay_response['status'] == 'SUCCESS'
                # For OKX
                elif 'code' in repay_response:
                    return repay_response['code'] == '0'
            return False
        except Exception as e:
            print(f"Error verifying loan repayment: {e}")
            return False

    async def _wait_for_deposit(self, exchange_ops, coin, amount, txid, max_attempts=30):
        """Wait for deposit to be confirmed with timeout"""
        for attempt in range(max_attempts):
            try:
                is_confirmed = await exchange_ops.verify_deposit(coin, amount, txid)
                if is_confirmed:
                    print(f"Deposit of {amount} {coin} confirmed!")
                    return True
                print(f"Waiting for deposit confirmation... Attempt {attempt + 1}/{max_attempts}")
                await asyncio.sleep(60)  # Check every 60 seconds
            except Exception as e:
                print(f"Error verifying deposit: {e}")
        return False

if __name__ == "__main__":
    # Get trading mode from config or override here
    trading_mode = TRADING_MODE  # "demo" or "live"
    bot = ArbitrageBot(mode=trading_mode)
    asyncio.run(bot.run())
