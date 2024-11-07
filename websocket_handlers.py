import asyncio
import json
import websockets
import ssl
import certifi

class WebSocketHandler:
    def __init__(self, bot):
        self.bot = bot
        self.symbols = bot.SYMBOLS
        
        # Create SSL context
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Create symbol mappings for different exchange formats
        self.okx_symbols = [f"{symbol[:-4]}-{symbol[-4:]}" for symbol in self.symbols]  # Convert BTCUSDT to BTC-USDT
        self.binance_symbols = self.symbols  # Keep original format for Binance

    async def binance_handler(self):
        """Handle Binance WebSocket connection"""
        while True:
            try:
                # Create subscription message for all symbols
                streams = [f"{symbol.lower()}@ticker" for symbol in self.binance_symbols]
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": streams,
                    "id": 1
                }

                print(f"\nConnecting to Binance WebSocket...")
                print(f"Subscribing to {len(streams)} symbol streams")

                async with websockets.connect(
                    self.bot.BINANCE_WS,
                    ssl=self.ssl_context
                ) as websocket:
                    print("Connected to Binance WebSocket")
                    
                    # Send subscription message
                    await websocket.send(json.dumps(subscribe_msg))
                    print("Sent subscription message to Binance")

                    # Wait for subscription confirmation
                    response = await websocket.recv()
                    print(f"Binance subscription response: {response}")

                    # After subscription
                    print(f"✅ Successfully subscribed to {len(self.bot.SYMBOLS)} Binance symbol streams")

                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if 's' in data:  # Price update message
                            symbol = data['s']
                            price = float(data['c'])  # Current price
                            self.bot.binance_prices[symbol] = price
                            await self.bot.check_arbitrage(symbol)

            except Exception as e:
                print(f"❌ Error in Binance WebSocket handler: {e}")
                print("Waiting 5 seconds before reconnecting to Binance...")
                await asyncio.sleep(5)

    async def okx_handler(self):
        """Handle OKX WebSocket connection"""
        while True:
            try:
                # Create subscription message for all symbols with OKX format
                subscribe_msg = {
                    "op": "subscribe",
                    "args": [{
                        "channel": "tickers",
                        "instId": symbol
                    } for symbol in self.okx_symbols]
                }

                print(f"\nConnecting to OKX WebSocket...")
                print(f"Subscribing to {len(self.okx_symbols)} symbol streams")

                async with websockets.connect(
                    self.bot.OKX_WS,
                    ssl=self.ssl_context
                ) as websocket:
                    print("Connected to OKX WebSocket")
                    
                    # Send subscription message
                    await websocket.send(json.dumps(subscribe_msg))
                    print("Sent subscription message to OKX")

                    # Wait for subscription confirmation
                    response = await websocket.recv()
                    print(f"OKX subscription response: {response}")

                    # After subscription
                    print(f"✅ Successfully subscribed to {len(self.bot.SYMBOLS)} OKX symbol streams")

                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        
                        if 'data' in data:
                            for item in data['data']:
                                # Convert OKX symbol format back to standard format
                                symbol = item['instId'].replace('-', '')
                                price = float(item['last'])
                                self.bot.okx_prices[symbol] = price
                                await self.bot.check_arbitrage(symbol)

            except Exception as e:
                print(f"❌ Error in OKX WebSocket handler: {e}")
                print("Waiting 5 seconds before reconnecting to OKX...")
                await asyncio.sleep(5)

    def _convert_to_standard_symbol(self, okx_symbol):
        """Convert OKX symbol format to standard format"""
        return okx_symbol.replace('-', '')

    def _convert_to_okx_symbol(self, standard_symbol):
        """Convert standard symbol format to OKX format"""
        base = standard_symbol[:-4]  # Everything except USDT
        quote = standard_symbol[-4:]  # USDT
        return f"{base}-{quote}"
