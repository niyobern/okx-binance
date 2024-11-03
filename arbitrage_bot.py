import asyncio
import aiohttp
import ssl
from decimal import Decimal
from trading_manager import TradingManager
from websocket_handlers import WebSocketHandler
from exchange_operations import BinanceOperations, OKXOperations
from config import *

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
        
        # Operations with mode
        self.binance_ops = BinanceOperations(mode=mode)
        self.okx_ops = OKXOperations(mode=mode)
        self.ws_handler = WebSocketHandler(self)

    async def execute_arbitrage(self, symbol, binance_price, okx_price):
        """Execute arbitrage trades if conditions are met"""
        try:
            if not self.trading_manager.can_open_position():
                return False

            binance_price = Decimal(str(binance_price))
            okx_price = Decimal(str(okx_price))
            
            # Calculate spread percentage
            avg_price = (binance_price + okx_price) / 2
            spread_percentage = abs(binance_price - okx_price) / avg_price * 100
            
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
            coin = symbol.split('-')[0]
            withdrawal_fee = COIN_NETWORKS[coin]['withdrawal_fee']
            usdt_withdrawal_fee = COIN_NETWORKS['USDT']['withdrawal_fee']
            total_transfer_fees = withdrawal_fee + usdt_withdrawal_fee
            
            trading_fees = Decimal('0.2')  # 0.1% per trade
            total_fee_percentage = trading_fees + (total_transfer_fees / (quantity * buy_price) * 100)
            profit_percentage = spread_percentage - total_fee_percentage
            
            # Calculate quantity based on available capital
            quantity = self.trading_manager.calculate_position_size(buy_price)
            total_cost = quantity * buy_price
            
            if (profit_percentage > self.trading_manager.min_profit_percentage and
                total_cost >= self.min_trade_amount and
                spread_percentage <= self.max_spread_percentage):
                
                print(f"\nExecuting arbitrage for {symbol}")
                print(f"Buy on {buy_exchange.upper()} at {buy_price}")
                print(f"Sell on {sell_exchange.upper()} at {sell_price}")
                print(f"Spread: {spread_percentage:.2f}%")
                print(f"Expected profit after fees: {profit_percentage:.2f}%")
                
                # Execute both orders concurrently
                spot_order, margin_order = await asyncio.gather(
                    spot_buy(symbol, quantity),
                    margin_sell(symbol, quantity)
                )
                
                if self._verify_market_orders(spot_order, margin_order):
                    if self.mode == "demo":
                        # Simulate transfer time and deduct fees in demo mode
                        print(f"\nDemo Mode: Simulating transfers...")
                        print(f"Transfer fees to be deducted: {total_transfer_fees} USDT")
                        
                        # Record the trade with fees
                        self.trading_manager.record_trade(
                            symbol, buy_exchange, sell_exchange,
                            quantity, buy_price, sell_price,
                            total_transfer_fees
                        )
                        
                        # Simulate waiting for transfers
                        await asyncio.sleep(600)  # 10 minutes simulation
                        await self.trading_manager.complete_trade(symbol)
                        
                    else:  # Live trading mode
                        try:
                            # Step 1: Transfer crypto to repay loan
                            print(f"\nInitiating crypto transfer to {to_exchange}...")
                            transfer = await crypto_transfer(coin, quantity, to_exchange)
                            
                            if not isinstance(transfer, dict) or 'txId' not in transfer:
                                print("Failed to initiate transfer or get transaction ID")
                                return False
                                
                            txid = transfer['txId']
                            print(f"Transfer initiated: Transaction ID {txid}")
                            
                            # Wait and verify transfer completion
                            print(f"Waiting for transfer confirmation...")
                            target_exchange_ops = self.okx_ops if to_exchange == 'okx' else self.binance_ops
                            
                            transfer_confirmed = await self._wait_for_deposit(
                                target_exchange_ops, 
                                coin, 
                                quantity, 
                                txid
                            )
                            
                            if not transfer_confirmed:
                                print("Transfer not confirmed after maximum attempts. Manual intervention required.")
                                return False
                            
                            # Step 2: Repay margin loan once transfer is confirmed
                            print(f"Repaying margin loan on {sell_exchange}...")
                            repay = await repay_loan(symbol, quantity)
                            print(f"Loan repayment status: {repay}")
                            
                            if self._verify_loan_repayment(repay):
                                # Step 3: Transfer USDT back only after successful loan repayment
                                print(f"Initiating USDT transfer back to {usdt_return_exchange}...")
                                usdt_return = await usdt_transfer(
                                    sell_price * quantity, 
                                    usdt_return_exchange
                                )
                                print(f"USDT transfer status: {usdt_return}")
                                
                                self.trading_manager.record_trade(
                                    symbol, buy_exchange, sell_exchange,
                                    quantity, buy_price, sell_price,
                                    total_transfer_fees
                                )
                                
                                await self.trading_manager.complete_trade(symbol)
                            else:
                                print("Failed to repay margin loan. Manual intervention required.")
                                
                        except Exception as e:
                            print(f"Error during transfer operations: {e}")
                            print("Manual intervention may be required to resolve positions.")
                    
                    return True
            
            return False
                
        except Exception as e:
            print(f"Error executing arbitrage for {symbol}: {e}")
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
        # Create a custom SSL context that doesn't verify certificates
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        async with aiohttp.ClientSession() as session:
            # Fetch Binance prices
            async with session.get(self.BINANCE_API, ssl=ssl_context) as response:
                binance_data = await response.json()
                for item in binance_data:
                    symbol = item['symbol'].replace('USDT', '-USDT')
                    if symbol in self.SYMBOLS:
                        self.binance_prices[symbol] = float(item['price'])

            # Fetch OKX prices
            params = {'instType': 'SPOT'}
            async with session.get(self.OKX_API, params=params, ssl=ssl_context) as response:
                okx_data = await response.json()
                for item in okx_data['data']:
                    symbol = item['instId']
                    if symbol in self.SYMBOLS:
                        self.okx_prices[symbol] = float(item['last'])

    async def check_arbitrage(self, symbol):
        """Check for arbitrage opportunities"""
        if symbol in self.binance_prices and symbol in self.okx_prices:
            binance_price = self.binance_prices[symbol]
            okx_price = self.okx_prices[symbol]
            
            diff = abs(binance_price - okx_price)
            avg_price = (binance_price + okx_price) / 2
            arb_percentage = (diff / avg_price) * 100

            if arb_percentage > self.trading_manager.min_profit_percentage:
                await self.execute_arbitrage(symbol, binance_price, okx_price)

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
