import asyncio
import json
import ssl
import websockets

class WebSocketHandler:
    def __init__(self, arbitrage_bot):
        self.bot = arbitrage_bot
        self.ssl_context = self._create_ssl_context()

    def _create_ssl_context(self):
        """Create SSL context for WebSocket connections"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context

    async def binance_handler(self):
        """Handle Binance WebSocket connection"""
        while True:
            try:
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": [f"{symbol.lower().replace('-', '')}@ticker" for symbol in self.bot.SYMBOLS],
                    "id": 1
                }
                
                async with websockets.connect(self.bot.BINANCE_DEMO_WS, ssl=self.ssl_context) as websocket:
                    await websocket.send(json.dumps(subscribe_msg))
                    print("Connected to Binance WebSocket")
                    
                    while True:
                        try:
                            response = await websocket.recv()
                            data = json.loads(response)
                            if 'e' in data and data['e'] == '24hrTicker':
                                symbol = data['s'].replace('USDT', '-USDT')
                                if symbol in self.bot.SYMBOLS:
                                    self.bot.binance_prices[symbol] = float(data['c'])
                                    await self.bot.check_arbitrage(symbol)
                        except websockets.exceptions.ConnectionClosed:
                            print("Binance WebSocket connection closed, reconnecting...")
                            break
                        except Exception as e:
                            print(f"Error in Binance WebSocket handler: {e}")
                            break
                            
            except Exception as e:
                print(f"Error connecting to Binance WebSocket: {e}")
            
            print("Waiting 5 seconds before reconnecting to Binance...")
            await asyncio.sleep(5)

    async def okx_handler(self):
        """Handle OKX WebSocket connection"""
        while True:
            try:
                subscribe_msg = {
                    "op": "subscribe",
                    "args": [{"channel": "tickers", "instId": symbol} for symbol in self.bot.SYMBOLS]
                }
                
                async with websockets.connect(self.bot.OKX_DEMO_WS, ssl=self.ssl_context) as websocket:
                    await websocket.send(json.dumps(subscribe_msg))
                    print("Connected to OKX WebSocket")
                    
                    while True:
                        try:
                            response = await websocket.recv()
                            data = json.loads(response)
                            if 'data' in data:
                                for item in data['data']:
                                    symbol = item['instId']
                                    if symbol in self.bot.SYMBOLS:
                                        self.bot.okx_prices[symbol] = float(item['last'])
                                        await self.bot.check_arbitrage(symbol)
                        except websockets.exceptions.ConnectionClosed:
                            print("OKX WebSocket connection closed, reconnecting...")
                            break
                        except Exception as e:
                            print(f"Error in OKX WebSocket handler: {e}")
                            break
                            
            except Exception as e:
                print(f"Error connecting to OKX WebSocket: {e}")
            
            print("Waiting 5 seconds before reconnecting to OKX...")
            await asyncio.sleep(5)
