# API Keys
BINANCE_API_KEY = "your_binance_api_key"
BINANCE_SECRET_KEY = "your_binance_secret_key"

OKX_API_KEY = "your_okx_api_key"
OKX_SECRET_KEY = "your_okx_secret_key"
OKX_PASSPHRASE = "your_okx_passphrase"

# Demo API Keys
BINANCE_DEMO_API_KEY = "your_binance_demo_api_key"
BINANCE_DEMO_SECRET_KEY = "your_binance_demo_secret_key"

OKX_DEMO_API_KEY = "your_okx_demo_api_key"
OKX_DEMO_SECRET_KEY = "your_okx_demo_secret_key"
OKX_DEMO_PASSPHRASE = "your_okx_demo_passphrase"

# API URLs
BINANCE_BASE_URL = "https://api.binance.com"
OKX_BASE_URL = "https://www.okx.com"

# Demo API URLs
BINANCE_DEMO_BASE_URL = "https://testnet.binance.vision"
OKX_DEMO_BASE_URL = "https://www.okx.com/api/v5/mock-trading"

# WebSocket URLs
BINANCE_WS = "wss://stream.binance.com:9443/ws"
OKX_WS = "wss://ws.okx.com:8443/ws/v5/public"

# Demo WebSocket URLs
BINANCE_DEMO_WS = "wss://testnet.binance.vision/ws"
OKX_DEMO_WS = "wss://wspap.okx.com:8443/ws/v5/public?brokerId=9999"

# Trading Parameters
INITIAL_CAPITAL = 2000  # USDT
MIN_TRADE_AMOUNT = 100  # USDT
MAX_SPREAD_PERCENTAGE = 5  # %
MIN_PROFIT_PERCENTAGE = 0.5  # %
TRANSFER_FEE = 2  # USDT (fixed fee for transfers)
TRADING_FEE = 0.001  # 0.1% trading fee

# Trading Mode
TRADING_MODE = "demo"  # Can be "demo" or "live"

# Wallet Addresses and Network Settings
COIN_NETWORKS = {
    "BTC": {
        "network": "BTC",  # Bitcoin native network
        "addresses": {
            "binance": "your_binance_btc_address",
            "okx": "your_okx_btc_address"
        },
        "withdrawal_fee": 0.0005  # BTC
    },
    "ETH": {
        "network": "Arbitrum",  # Arbitrum network for lower fees
        "addresses": {
            "binance": "your_binance_eth_arbitrum_address",
            "okx": "your_okx_eth_arbitrum_address"
        },
        "withdrawal_fee": 0.0003  # ETH
    },
    "XRP": {
        "network": "XRP",  # XRP native network
        "addresses": {
            "binance": "your_binance_xrp_address",
            "okx": "your_okx_xrp_address"
        },
        "withdrawal_fee": 0.2  # XRP
    },
    "USDT": {
        "network": "TRC20",  # Tron network for USDT (lowest fees)
        "addresses": {
            "binance": "your_binance_usdt_trc20_address",
            "okx": "your_okx_usdt_trc20_address"
        },
        "withdrawal_fee": 1.0  # USDT
    }
}

# Trading Pairs
SYMBOLS = [
    "BTC-USDT",
    "ETH-USDT",
    "XRP-USDT",
    # Add more trading pairs here
]

# Network Settings
TRANSFER_WAIT_TIME = 30  # seconds to wait for transfer confirmation
WEBSOCKET_RECONNECT_DELAY = 5  # seconds to wait before reconnecting websocket
