# --- Mock MetaTrader5 Module for Testing ---
"""
Mock implementation of MetaTrader5 for cross-platform testing
This allows development and testing on non-Windows platforms
"""

import random
import datetime
import os
from typing import Optional, List, Any, NamedTuple
from logger_utils import logger

# MT5 Constants - CRITICAL FIX for trading operations
TRADE_RETCODE_DONE = 10009
TRADE_RETCODE_INVALID_ORDER = 10013
TRADE_RETCODE_INVALID_VOLUME = 10014
TRADE_RETCODE_NO_MONEY = 10019
TRADE_RETCODE_MARKET_CLOSED = 10018

# Order Types
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5

# Position Types  
POSITION_TYPE_BUY = 0
POSITION_TYPE_SELL = 1

# Trade Actions
TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_MODIFY = 6
TRADE_ACTION_REMOVE = 7

# Order Time Types
ORDER_TIME_GTC = 0
ORDER_TIME_DAY = 1
ORDER_TIME_SPECIFIED = 2
ORDER_TIME_SPECIFIED_DAY = 3

# Order Filling Types
ORDER_FILLING_FOK = 0
ORDER_FILLING_IOC = 1
ORDER_FILLING_RETURN = 2


class SymbolInfo(NamedTuple):
    name: str
    visible: bool = True
    digits: int = 5
    point: float = 0.00001
    trade_stops_level: int = 10
    trade_mode: int = 4  # SYMBOL_TRADE_MODE_FULL


class TickInfo(NamedTuple):
    time: int
    bid: float
    ask: float
    last: float = 0.0
    volume: int = 100


class AccountInfo(NamedTuple):
    login: int = 12345678
    server: str = "MockServer-Live"
    balance: float = 10000.0
    equity: float = 10000.0
    margin: float = 0.0
    margin_free: float = 10000.0
    margin_level: float = 0.0
    currency: str = "USD"
    trade_allowed: bool = True
    leverage: int = 100
    profit: float = 0.0


class TerminalInfo(NamedTuple):
    name: str = "MetaTrader 5 (Mock)"
    path: str = "/mock/terminal"
    build: int = 4400
    connected: bool = True


class Position(NamedTuple):
    ticket: int
    symbol: str
    type: int  # 0=BUY, 1=SELL
    volume: float
    price_open: float
    price_current: float
    profit: float
    comment: str = "Mock Position"
    tp: float = 0.0  # Take Profit
    sl: float = 0.0  # Stop Loss


# Global state for mock
_connected = False
_symbols_data = {}
_positions = []
_last_error = (0, "No error")

# Global mock state
_mock_positions = []
_mock_orders = []
_daily_order_count = 0


def initialize(path: Optional[str] = None) -> bool:
    """Mock MT5 initialization"""
    global _connected
    _connected = True
    logger("🎯 Mock MT5 initialized successfully")

    # Initialize some default symbols including XAUUSDm for CFD testing
    default_symbols = {
        "EURUSD": {"bid": 1.0850, "ask": 1.0852, "digits": 5, "point": 0.00001},
        "GBPUSD": {"bid": 1.2650, "ask": 1.2652, "digits": 5, "point": 0.00001},
        "USDJPY": {"bid": 149.50, "ask": 149.52, "digits": 3, "point": 0.01},
        "XAUUSD": {"bid": 2020.50, "ask": 2021.00, "digits": 2, "point": 0.01},
        "XAUUSDm": {"bid": 3373.20, "ask": 3373.40, "digits": 2, "point": 0.01},  # Gold CFD  
        "AUDUSD": {"bid": 0.6750, "ask": 0.6752, "digits": 5, "point": 0.00001},
        "USDCAD": {"bid": 1.3450, "ask": 1.3452, "digits": 5, "point": 0.00001}
    }

    for symbol, data in default_symbols.items():
        _symbols_data[symbol] = data

    return True


def shutdown():
    """Mock MT5 shutdown"""
    global _connected
    _connected = False
    logger("🎯 Mock MT5 shutdown")


def terminal_info() -> Optional[TerminalInfo]:
    """Mock terminal info"""
    if not _connected:
        return None
    return TerminalInfo()


def account_info() -> Optional[AccountInfo]:
    """Mock account info"""
    if not _connected:
        return None
    return AccountInfo()


def symbol_info(symbol: str) -> Optional[SymbolInfo]:
    """Mock symbol info"""
    if not _connected or symbol not in _symbols_data:
        return None

    data = _symbols_data[symbol]
    return SymbolInfo(
        name=symbol,
        digits=data["digits"],
        point=data["point"]
    )


def symbol_info_tick(symbol: str) -> Optional[TickInfo]:
    """Mock symbol tick info with realistic price movements"""
    if not _connected or symbol not in _symbols_data:
        return None

    data = _symbols_data[symbol]
    base_bid = data["bid"]
    base_ask = data["ask"]

    # Add small random price movement
    price_change = random.uniform(-0.001, 0.001)  # ±0.1%
    current_bid = base_bid + (base_bid * price_change)
    current_ask = base_ask + (base_ask * price_change)

    # Update stored prices for next call
    data["bid"] = current_bid
    data["ask"] = current_ask

    return TickInfo(
        time=int(datetime.datetime.now().timestamp()),
        bid=round(current_bid, data["digits"]),
        ask=round(current_ask, data["digits"]),
        last=round((current_bid + current_ask) / 2, data["digits"]),
        volume=random.randint(50, 200)
    )


def symbols_get() -> Optional[List[SymbolInfo]]:
    """Mock symbols list"""
    if not _connected:
        return None

    symbols = []
    for symbol_name in _symbols_data.keys():
        data = _symbols_data[symbol_name]
        symbols.append(SymbolInfo(
            name=symbol_name,
            digits=data["digits"],
            point=data["point"]
        ))

    return symbols


def symbol_select(symbol: str, enable: bool = True) -> bool:
    """Mock symbol selection"""
    if not _connected:
        return False

    if symbol in _symbols_data:
        logger(f"🎯 Mock: Symbol {symbol} {'enabled' if enable else 'disabled'}")
        return True
    return False


def copy_rates_from_pos(symbol: str, timeframe, start_pos: int, count: int) -> Optional[List]:
    """Mock historical data generation"""
    if not _connected or symbol not in _symbols_data:
        return None

    # Generate realistic OHLC data
    data = _symbols_data[symbol]
    base_price = (data["bid"] + data["ask"]) / 2

    rates = []
    current_price = base_price

    for i in range(count):
        # Generate realistic OHLC with some volatility
        price_change = random.uniform(-0.002, 0.002)  # ±0.2%
        open_price = current_price

        high_offset = random.uniform(0, 0.001)
        low_offset = random.uniform(-0.001, 0)
        close_offset = random.uniform(-0.001, 0.001)

        high_price = open_price + (open_price * high_offset)
        low_price = open_price + (open_price * low_offset)
        close_price = open_price + (open_price * close_offset)

        # Ensure OHLC logic
        high_price = max(open_price, high_price, low_price, close_price)
        low_price = min(open_price, high_price, low_price, close_price)

        rates.append({
            'time': int(datetime.datetime.now().timestamp()) - (count - i) * 60,
            'open': round(open_price, data["digits"]),
            'high': round(high_price, data["digits"]),
            'low': round(low_price, data["digits"]),
            'close': round(close_price, data["digits"]),
            'tick_volume': random.randint(50, 500),
            'real_volume': 0
        })

        current_price = close_price

    return rates


def order_send(request: dict) -> dict:
    """Mock order sending with proper position tracking"""
    global _mock_positions, _mock_orders, _daily_order_count

    try:
        # Simulate order execution
        result = type('MockResult', (), {})()
        result.retcode = TRADE_RETCODE_DONE
        result.order = random.randint(100000, 999999)
        result.deal = result.order
        result.volume = request.get('volume', 0.01)
        result.price = request.get('price', 1.0)

        # Create mock position
        position = type('MockPosition', (), {})()
        position.ticket = result.order
        position.symbol = request.get('symbol', 'EURUSD')
        position.volume = result.volume
        position.type = request.get('type', POSITION_TYPE_BUY)
        position.price_open = result.price
        position.profit = 0.0
        position.sl = request.get('sl', 0.0)
        position.tp = request.get('tp', 0.0)

        # Add to mock positions
        _mock_positions.append(position)
        _daily_order_count += 1

        logger(f"🎯 Mock Order Sent: {request.get('type', 1)} {request.get('symbol', 'UNKNOWN')} {request.get('volume', 0.01)} lots at {request.get('price', 1.0)}")

        return result
    except Exception as e:
        logger(f"❌ Mock order error: {str(e)}")
        return None


def positions_get(symbol: Optional[str] = None) -> Optional[List[Position]]:
    """Mock positions getter"""
    global _mock_positions

    if symbol:
        return [pos for pos in _mock_positions if pos.symbol == symbol]
    return _mock_positions

def position_get(symbol=None):
    """Mock single position getter"""
    positions = positions_get(symbol)
    return positions[0] if positions else None


def orders_get(symbol: Optional[str] = None) -> Optional[List]:
    """Mock pending orders"""
    if not _connected:
        return None

    # Return empty list for mock (no pending orders)
    return []


def last_error() -> tuple:
    """Mock last error"""
    return _last_error


# Timeframe constants
TIMEFRAME_M1 = 1
TIMEFRAME_M5 = 5
TIMEFRAME_M15 = 15
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 60
TIMEFRAME_H4 = 240
TIMEFRAME_D1 = 1440

def positions_get(symbol: Optional[str] = None, ticket: Optional[int] = None) -> Optional[List[Position]]:
    """Mock positions with ticket filtering support"""
    if not _connected:
        return None

    # Filter by ticket if specified
    if ticket:
        return [pos for pos in _positions if pos.ticket == ticket]

    # Filter by symbol if specified
    if symbol:
        return [pos for pos in _positions if pos.symbol == symbol]

    return _positions


def history_deals_get(date_from, date_to, symbol: Optional[str] = None) -> Optional[List]:
    """Mock trade history"""
    if not _connected:
        return None
    return []  # Empty history for mock


def history_orders_get(date_from, date_to, symbol: Optional[str] = None) -> Optional[List]:
    """Mock order history"""
    if not _connected:
        return None
    return []  # Empty history for mock