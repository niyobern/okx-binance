import json
# API Keys
BINANCE_API_KEY = "J1hIqDkJVj44CvEiOtgMA9VYMF911kV7oq70YLvQNq2EdHZjTDiP33T53vWt9awc"
BINANCE_SECRET_KEY = "lQEkT8dg1efseKMx8ulP7meeHGSmqjm1yxXxpdJBzcCkHpQf5F482IwGhNM94xoL"

OKX_API_KEY = "35f981b7-3c48-46d4-9bc5-bed14ce5b82e"
OKX_SECRET_KEY = "4B5C817A781E7DDA7ED7D82215AB3213"
OKX_PASSPHRASE = "Reform@781"

# Demo API Keys
BINANCE_DEMO_API_KEY = "your_binance_demo_api_key"
BINANCE_DEMO_SECRET_KEY = "your_binance_demo_secret_key"

OKX_DEMO_API_KEY = "your_okx_demo_api_key"
OKX_DEMO_SECRET_KEY = "your_okx_demo_secret_key"
OKX_DEMO_PASSPHRASE = "your_okx_demo_passphrase"

# API URLs
BINANCE_BASE_URL = "https://api.binance.com"
OKX_BASE_URL = "https://www.okx.com/api/v5"

# Demo API URLs
BINANCE_DEMO_BASE_URL = "https://testnet.binance.vision"
OKX_DEMO_BASE_URL = "https://www.okx.com/api/v5"

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

# Load network configurations from sorted_fees.json
try:
    with open('sorted_fees.json', 'r') as f:
        fees_data = json.load(f)
        COIN_NETWORKS = {
            coin: {
                "network": data["network"],
                "withdrawal_fee": data["withdrawal_fee"]
            }
            for coin, data in fees_data["fees"].items()
        }
except Exception as e:
    print(f"Error loading sorted_fees.json: {e}")
    # Fallback to basic configuration if file can't be loaded
    COIN_NETWORKS = {
        "USDT": {
            "network": "TRC20",
            "withdrawal_fee": 1.0
        }
    }

# Add USDT if not present in the fees data
if "USDT" not in COIN_NETWORKS:
    COIN_NETWORKS["USDT"] = {
        "network": "TRC20",
        "withdrawal_fee": 1.0
    }

# Trading Pairs generated from sorted_fees.json
SYMBOLS = [
    "CFXUSDT",
    "CELOUSDT",
    "FLOWUSDT",
    "ICPUSDT",
    "ICXUSDT",
    "FILUSDT",
    "XLMUSDT",
    "ALGOUSDT",
    "ENJUSDT",
    "DGBUSDT",
    "ONEUSDT",
    "GLMRUSDT",
    "IOSTUSDT",
    "RVNUSDT",
    "ZILUSDT",
    "WAXPUSDT",
    "ACEUSDT",
    "LUNAUSDT",
    "EGLDUSDT",
    "GASUSDT",
    "HBARUSDT",
    "EOSUSDT",
    "DYDXUSDT",
    "MOVRUSDT",
    "POLUSDT",
    "WLDUSDT",
    "APTUSDT",
    "IOTAUSDT",
    "DOGSUSDT",
    "XTZUSDT",
    "ZKUSDT",
    "NEARUSDT",
    "LTCUSDT",
    "ATOMUSDT",
    "LUNCUSDT",
    "RDNTUSDT",
    "ARBUSDT",
    "MAGICUSDT",
    "NEOUSDT",
    "USDCUSDT",
    "TONUSDT",
    "XRPUSDT",
    "ETHUSDT",
    "QTUMUSDT",
    "SUIUSDT",
    "GMTUSDT",
    "CATIUSDT",
    "OPUSDT",
    "ETCUSDT",
    "ARUSDT",
    "HMSTRUSDT",
    "FLMUSDT",
    "AVAXUSDT",
    "THETAUSDT",
    "TRXUSDT",
    "ONTUSDT",
    "KSMUSDT",
    "INJUSDT",
    "NOTUSDT",
    "USTCUSDT",
    "GMXUSDT",
    "BCHUSDT",
    "ADAUSDT",
    "FTMUSDT",
    "DOTUSDT",
    "ZROUSDT",
    "ELFUSDT",
    "METISUSDT",
    "MINAUSDT",
    "TIAUSDT",
    "GFTUSDT",
    "JOEUSDT",
    "DOGEUSDT",
    "STRKUSDT",
    "RENDERUSDT",
    "BNBUSDT",
    "FLOKIUSDT",
    "JSTUSDT",
    "TNSRUSDT",
    "WUSDT",
    "JTOUSDT",
    "BONKUSDT",
    "PYTHUSDT",
    "WIFUSDT",
    "JUPUSDT",
    "SOLUSDT",
    "RAYUSDT",
    "BOMEUSDT"
]

# Network Settings
TRANSFER_WAIT_TIME = 30  # seconds to wait for transfer confirmation
WEBSOCKET_RECONNECT_DELAY = 5  # seconds to wait before reconnecting websocket

# Exchange API credentials
BINANCE_CONFIG = {
    'apiKey': 'your_binance_api_key',
    'secret': 'your_binance_secret'
}

OKX_CONFIG = {
    'apiKey': 'your_okx_api_key',
    'secret': 'your_okx_secret',
    'password': 'your_okx_password'
}
