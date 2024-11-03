from decimal import Decimal, ROUND_DOWN
from datetime import datetime

class TradingManager:
    def __init__(self, initial_capital=2000):
        self.initial_capital = Decimal(str(initial_capital))
        self.available_capital = Decimal(str(initial_capital))
        self.positions = {}
        self.min_profit_percentage = Decimal('0.5')
        self.is_trading = False

    def calculate_position_size(self, price):
        """Calculate the maximum quantity we can trade with our capital"""
        quantity = (self.available_capital / Decimal(str(price))).quantize(Decimal('0.00001'), rounding=ROUND_DOWN)
        return quantity

    def can_open_position(self):
        """Check if we can open a new position"""
        return (
            not self.is_trading and
            self.available_capital >= self.initial_capital
        )

    def record_trade(self, symbol, buy_exchange, sell_exchange, quantity, buy_price, sell_price, transfer_fees):
        """Record the arbitrage trade details"""
        self.positions[symbol] = {
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'qty': quantity,
            'buy_price': Decimal(str(buy_price)),
            'sell_price': Decimal(str(sell_price)),
            'transfer_fees': Decimal(str(transfer_fees)),
            'timestamp': datetime.now(),
            'status': 'active'
        }
        
        self.available_capital -= (quantity * Decimal(str(buy_price)) + Decimal(str(transfer_fees)))
        self.is_trading = True
        
        self._print_trade_summary(symbol, quantity, buy_exchange, sell_exchange, buy_price, sell_price, transfer_fees)

    def _print_trade_summary(self, symbol, quantity, buy_exchange, sell_exchange, buy_price, sell_price, transfer_fees):
        """Print trade execution summary"""
        gross_profit = quantity * (Decimal(str(sell_price)) - Decimal(str(buy_price)))
        fees = (quantity * Decimal(str(buy_price)) * Decimal('0.001') +  # Spot trading fee
               quantity * Decimal(str(sell_price)) * Decimal('0.001') +  # Margin trading fee
               2)    # Transfer fee
        net_profit = gross_profit - fees
        
        print(f"\nArbitrage trade executed for {symbol}")
        print(f"Buy on {buy_exchange}: Quantity {quantity} @ {buy_price}")
        print(f"Short on {sell_exchange}: Quantity {quantity} @ {sell_price}")
        print(f"Gross profit: ${gross_profit:.2f}")
        print(f"Fees: ${fees:.2f}")
        print(f"Net profit: ${net_profit:.2f}")
        print(f"Remaining capital: ${self.available_capital:.2f}")

    async def complete_trade(self, symbol):
        """Mark trade as completed and restore capital"""
        if symbol in self.positions:
            self.positions[symbol]['status'] = 'completed'
            self.available_capital = self.initial_capital
            self.is_trading = False
            print(f"\nTrade cycle completed for {symbol}")
            print(f"Capital restored to ${self.available_capital:.2f}")
            print("Ready for next trade")
