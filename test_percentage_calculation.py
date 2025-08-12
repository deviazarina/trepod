
#!/usr/bin/env python3
"""
Test Percentage TP/SL Calculation - Verify percentage-based TP/SL calculations are correct
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_operations import calculate_tp_sl_all_modes
from logger_utils import logger

def test_percentage_calculations():
    """Test percentage-based TP/SL calculations"""
    logger("🧪 Testing Percentage TP/SL Calculations...")
    
    # Test parameters
    symbol = "EURUSD"
    current_price = 1.10000
    lot_size = 0.01
    
    # Test BUY order with percentage TP/SL
    logger("\n📊 Testing BUY Order with Percentage:")
    
    # BUY - TP 2% (should be 1.10000 * 1.02 = 1.12200)
    tp_buy = calculate_tp_sl_all_modes("2", "percent", symbol, "BUY", current_price, lot_size)
    expected_tp_buy = 1.12200
    logger(f"BUY TP 2%: {tp_buy:.5f} (Expected: {expected_tp_buy:.5f}) - {'✅' if abs(tp_buy - expected_tp_buy) < 0.00001 else '❌'}")
    
    # BUY - SL -1% (should be 1.10000 * 0.99 = 1.08900)
    sl_buy = calculate_tp_sl_all_modes("-1", "percent", symbol, "BUY", current_price, lot_size)
    expected_sl_buy = 1.08900
    logger(f"BUY SL -1%: {sl_buy:.5f} (Expected: {expected_sl_buy:.5f}) - {'✅' if abs(sl_buy - expected_sl_buy) < 0.00001 else '❌'}")
    
    # Test SELL order with percentage TP/SL
    logger("\n📊 Testing SELL Order with Percentage:")
    
    # SELL - TP 2% (should be 1.10000 * 0.98 = 1.07800)
    tp_sell = calculate_tp_sl_all_modes("2", "percent", symbol, "SELL", current_price, lot_size)
    expected_tp_sell = 1.07800
    logger(f"SELL TP 2%: {tp_sell:.5f} (Expected: {expected_tp_sell:.5f}) - {'✅' if abs(tp_sell - expected_tp_sell) < 0.00001 else '❌'}")
    
    # SELL - SL -1% (should be 1.10000 * 1.01 = 1.11100)
    sl_sell = calculate_tp_sl_all_modes("-1", "percent", symbol, "SELL", current_price, lot_size)
    expected_sl_sell = 1.11100
    logger(f"SELL SL -1%: {sl_sell:.5f} (Expected: {expected_sl_sell:.5f}) - {'✅' if abs(sl_sell - expected_sl_sell) < 0.00001 else '❌'}")
    
    # Test XAU/USD (Gold) with percentage
    logger("\n📊 Testing XAUUSD with Percentage:")
    gold_price = 2000.00
    
    # BUY Gold - TP 1% (should be 2000.00 * 1.01 = 2020.00)
    tp_gold_buy = calculate_tp_sl_all_modes("1", "percent", "XAUUSD", "BUY", gold_price, lot_size)
    expected_tp_gold = 2020.00
    logger(f"GOLD BUY TP 1%: {tp_gold_buy:.2f} (Expected: {expected_tp_gold:.2f}) - {'✅' if abs(tp_gold_buy - expected_tp_gold) < 0.01 else '❌'}")
    
    # SELL Gold - SL -0.5% (should be 2000.00 * 1.005 = 2010.00)
    sl_gold_sell = calculate_tp_sl_all_modes("-0.5", "percent", "XAUUSD", "SELL", gold_price, lot_size)
    expected_sl_gold = 2010.00
    logger(f"GOLD SELL SL -0.5%: {sl_gold_sell:.2f} (Expected: {expected_sl_gold:.2f}) - {'✅' if abs(sl_gold_sell - expected_sl_gold) < 0.01 else '❌'}")
    
    logger("\n✅ Percentage calculation tests completed!")

if __name__ == "__main__":
    test_percentage_calculations()
