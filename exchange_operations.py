import hmac
import hashlib
import base64
import time
import requests
from decimal import Decimal
from urllib.parse import urlencode
from config import *

class BinanceOperations:
    def __init__(self, mode="demo"):
        self.mode = mode
        if mode == "demo":
            self.api_key = BINANCE_DEMO_API_KEY
            self.api_secret = BINANCE_DEMO_SECRET_KEY
            self.base_url = BINANCE_DEMO_BASE_URL
        else:
            self.api_key = BINANCE_API_KEY
            self.api_secret = BINANCE_SECRET_KEY
            self.base_url = BINANCE_BASE_URL

    def _generate_signature(self, params):
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    async def place_spot_market_buy(self, symbol, quantity):
        """Place a spot market buy order on Binance"""
        endpoint = "/api/v3/order"
        params = {
            'symbol': symbol.replace('-', ''),
            'side': 'BUY',
            'type': 'MARKET',
            'quantity': quantity,
            'timestamp': int(time.time() * 1000)
        }
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.post(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        return response.json()

    async def repay_margin_loan(self, symbol, quantity):
        """Repay margin loan using transferred assets on Binance"""
        endpoint = "/sapi/v1/margin/repay"
        params = {
            'asset': symbol.split('-')[0],  # Get the base currency
            'amount': quantity,
            'timestamp': int(time.time() * 1000)
        }
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.post(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        return response.json()

    async def get_margin_loan_status(self, symbol):
        """Get margin loan status for a specific asset"""
        endpoint = "/sapi/v1/margin/loan"
        params = {
            'asset': symbol.split('-')[0],
            'timestamp': int(time.time() * 1000)
        }
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        return response.json()

    async def transfer_usdt(self, amount, address, network='TRC20'):
        """Transfer USDT back to original platform"""
        endpoint = "/sapi/v1/capital/withdraw/apply"
        params = {
            'coin': 'USDT',
            'amount': amount,
            'address': address,
            'network': network,
            'timestamp': int(time.time() * 1000)
        }
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.post(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        return response.json()

    async def withdraw_crypto(self, coin, quantity, to_exchange):
        """
        Withdraw cryptocurrency to another exchange
        
        Args:
            coin: The cryptocurrency to withdraw (e.g., 'BTC', 'ETH')
            quantity: Amount to withdraw
            to_exchange: Destination exchange ('binance' or 'okx')
        """
        network = COIN_NETWORKS[coin]['network']
        address = COIN_NETWORKS[coin]["addresses"][to_exchange]
        
        endpoint = "/sapi/v1/capital/withdraw/apply"
        params = {
            'coin': coin,
            'amount': quantity,
            'address': address,
            'network': network,
            'timestamp': int(time.time() * 1000)
        }
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.post(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        return response.json()

    async def transfer_usdt(self, amount, to_exchange):
        """Transfer USDT to another exchange using preferred network"""
        network = COIN_NETWORKS['USDT']['network']
        address = COIN_NETWORKS['USDT']['addresses'][to_exchange]
        
        return await self.withdraw_crypto('USDT', amount, to_exchange)

    async def place_margin_market_short(self, symbol, quantity):
        """Place a margin market short order on Binance"""
        endpoint = "/sapi/v1/margin/order"
        params = {
            'symbol': symbol.replace('-', ''),
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': quantity,
            'isIsolated': 'FALSE',  # Using cross margin
            'sideEffectType': 'MARGIN_BUY',  # This will borrow the asset
            'timestamp': int(time.time() * 1000)
        }
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.post(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        return response.json()

    async def verify_deposit(self, coin, amount, txid):
        """Verify that a deposit has been received and confirmed"""
        endpoint = "/sapi/v1/capital/deposit/hisrec"
        params = {
            'coin': coin,
            'status': 1,  # 1 = completed
            'timestamp': int(time.time() * 1000)
        }
        
        signature = self._generate_signature(params)
        params['signature'] = signature
        
        headers = {'X-MBX-APIKEY': self.api_key}
        response = requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            deposits = response.json()
            for deposit in deposits:
                if (deposit['coin'] == coin and 
                    float(deposit['amount']) == float(amount) and
                    deposit['txId'] == txid):
                    return True
        return False

class OKXOperations:
    def __init__(self, mode="demo"):
        self.mode = mode
        if mode == "demo":
            self.api_key = OKX_DEMO_API_KEY
            self.api_secret = OKX_DEMO_SECRET_KEY
            self.passphrase = OKX_DEMO_PASSPHRASE
            self.base_url = OKX_DEMO_BASE_URL
        else:
            self.api_key = OKX_API_KEY
            self.api_secret = OKX_SECRET_KEY
            self.passphrase = OKX_PASSPHRASE
            self.base_url = OKX_BASE_URL

    def _generate_signature(self, timestamp, method, request_path, body=''):
        message = timestamp + method + request_path + (body if body else '')
        mac = hmac.new(
            bytes(self.api_secret, encoding='utf8'),
            bytes(message, encoding='utf-8'),
            digestmod='sha256'
        )
        return base64.b64encode(mac.digest()).decode()

    async def place_margin_market_short(self, symbol, quantity):
        """Place a margin market short order on OKX"""
        endpoint = "/api/v5/trade/order"
        timestamp = str(int(time.time() * 1000))
        
        body = {
            'instId': symbol,
            'tdMode': 'cross',
            'side': 'sell',
            'ordType': 'market',
            'sz': str(quantity)
        }
        
        signature = self._generate_signature(timestamp, 'POST', endpoint, str(body))
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=body,
            headers=headers
        )
        return response.json()

    async def repay_margin_loan(self, symbol, quantity):
        """Repay margin loan using transferred assets"""
        endpoint = "/api/v5/account/repay-debt"
        timestamp = str(int(time.time() * 1000))
        
        body = {
            'ccy': symbol.split('-')[0],  # Get the base currency
            'amt': str(quantity),
            'mgnMode': 'cross'
        }
        
        signature = self._generate_signature(timestamp, 'POST', endpoint, str(body))
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=body,
            headers=headers
        )
        return response.json()

    async def transfer_usdt(self, amount, address, network='TRC20'):
        """Transfer USDT back to original platform"""
        endpoint = "/api/v5/asset/withdrawal"
        timestamp = str(int(time.time() * 1000))
        
        body = {
            'ccy': 'USDT',
            'amt': str(amount),
            'dest': '4',  # 4 for external withdrawal
            'toAddr': address,
            'network': network,
            'fee': '1'  # Standard fee for USDT transfer
        }
        
        signature = self._generate_signature(timestamp, 'POST', endpoint, str(body))
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=body,
            headers=headers
        )
        return response.json()

    async def withdraw_crypto(self, coin, quantity, to_exchange):
        """
        Withdraw cryptocurrency to another exchange
        
        Args:
            coin: The cryptocurrency to withdraw (e.g., 'BTC', 'ETH')
            quantity: Amount to withdraw
            to_exchange: Destination exchange ('binance' or 'okx')
        """
        network = COIN_NETWORKS[coin]['network']
        address = COIN_NETWORKS[coin]['addresses'][to_exchange]
        
        endpoint = "/api/v5/asset/withdrawal"
        timestamp = str(int(time.time() * 1000))
        
        body = {
            'ccy': coin,
            'amt': str(quantity),
            'dest': '4',  # 4 for external withdrawal
            'toAddr': address,
            'network': network,
            'fee': str(COIN_NETWORKS[coin]["withdrawal_fee"])
        }
        
        signature = self._generate_signature(timestamp, 'POST', endpoint, str(body))
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=body,
            headers=headers
        )
        return response.json()

    async def transfer_usdt(self, amount, to_exchange):
        """Transfer USDT to another exchange using preferred network"""
        network = COIN_NETWORKS['USDT']['network']
        address = COIN_NETWORKS['USDT']['addresses'][to_exchange]
        
        return await self.withdraw_crypto('USDT', amount, to_exchange)

    async def place_spot_market_buy(self, symbol, quantity):
        """Place a spot market buy order on OKX"""
        endpoint = "/api/v5/trade/order"
        timestamp = str(int(time.time() * 1000))
        
        body = {
            'instId': symbol,
            'tdMode': 'cash',  # cash for spot trading
            'side': 'buy',
            'ordType': 'market',
            'sz': str(quantity),
            'tgtCcy': 'base_ccy'  # quantity is in base currency units
        }
        
        signature = self._generate_signature(timestamp, 'POST', endpoint, str(body))
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{self.base_url}{endpoint}",
            json=body,
            headers=headers
        )
        return response.json()

    async def verify_deposit(self, coin, amount, txid):
        """Verify that a deposit has been received and confirmed"""
        endpoint = "/api/v5/asset/deposit-history"
        timestamp = str(int(time.time() * 1000))
        
        params = {
            'ccy': coin,
            'state': '2'  # 2 = completed
        }
        
        signature = self._generate_signature(timestamp, 'GET', endpoint)
        
        headers = {
            'OK-ACCESS-KEY': self.api_key,
            'OK-ACCESS-SIGN': signature,
            'OK-ACCESS-TIMESTAMP': timestamp,
            'OK-ACCESS-PASSPHRASE': self.passphrase
        }
        
        response = requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['code'] == '0':
                for deposit in data['data']:
                    if (deposit['ccy'] == coin and 
                        float(deposit['amt']) == float(amount) and
                        deposit['txId'] == txid):
                        return True
        return False
