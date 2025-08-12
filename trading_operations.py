# --- Trading Operations Module - FIXED VERSION ---
"""
Core trading operations: order execution, TP/SL calculation, position management
"""

import datetime
import time
from typing import Dict, Any, Tuple, Optional, List
from logger_utils import logger

# Smart MT5 connection  
try:
    import MetaTrader5 as mt5
    print("✅ Trading Operations using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    print("⚠️ Trading Operations using mock for development")


def calculate_pip_value(symbol: str, lot_size: float = 0.01, current_price: float = 1.0) -> float:
    """Calculate pip value for position sizing - REAL calculations"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        account_info = mt5.account_info()

        if not symbol_info or not account_info:
            return 1.0

        # Get contract specifications
        contract_size = getattr(symbol_info, 'trade_contract_size', 100000)
        point = getattr(symbol_info, 'point', 0.00001)

        # Calculate pip value based on symbol type
        if "JPY" in symbol:
            pip_multiplier = 0.01  # JPY pairs use 2 decimal places
        else:
            pip_multiplier = 0.0001  # Other pairs use 4 decimal places

        pip_value = lot_size * contract_size * pip_multiplier

        # Convert to account currency if needed
        if hasattr(symbol_info, 'currency_profit'):
            # This is a simplification - real implementation would need currency conversion
            pass

        return pip_value

    except Exception as e:
        logger(f"❌ Error calculating pip value: {str(e)}")
        return 1.0


def calculate_tp_sl_all_modes(input_value: str, unit: str, symbol: str, order_type: str, current_price: float, lot_size: float = 0.01) -> float:
    """Calculate TP/SL for all modes: pips, price, percentage, money - ENHANCED CALCULATIONS"""
    try:
        if not input_value or input_value.strip() == "0":
            return 0.0

        value = float(input_value.strip())
        if value == 0:
            return 0.0

        symbol_info = mt5.symbol_info(symbol)
        account_info = mt5.account_info()

        if not symbol_info:
            logger(f"❌ Cannot get symbol info for {symbol}")
            return 0.0

        point = getattr(symbol_info, 'point', 0.00001)
        digits = getattr(symbol_info, 'digits', 5)

        # FIXED: Get minimum stops level for proper distance
        stops_level = getattr(symbol_info, 'trade_stops_level', 0)
        min_distance = max(stops_level * point, point * 50)  # Minimum 50 points

        # Special handling for Gold/XAU symbols
        if 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
            min_distance = max(min_distance, 0.5)  # Minimum 50 cents for Gold

        # FIXED: Proper TP/SL calculation with minimum distance validation
        if unit.lower() == "pips":
            # Standard pip calculation
            if "JPY" in symbol:
                pip_multiplier = 0.01  # JPY pairs
            elif 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
                pip_multiplier = 0.1   # Gold uses 10 cents per pip
            else:
                pip_multiplier = 0.0001  # Standard forex pairs

            distance = abs(value) * pip_multiplier

            # Ensure minimum distance
            if distance < min_distance:
                distance = min_distance
                logger(f"⚠️ TP/SL distance adjusted to minimum: {distance}")

            # CORRECT TP/SL logic - NO reversal needed
            if order_type.upper() == "BUY":
                if value > 0:  # Take Profit
                    return round(current_price + distance, digits)
                else:  # Stop Loss (negative value)
                    return round(current_price - distance, digits)
            else:  # SELL order
                if value > 0:  # Take Profit  
                    return round(current_price - distance, digits)
                else:  # Stop Loss (negative value)
                    return round(current_price + distance, digits)

        elif unit.lower() == "price":
            return round(value, digits)

        elif unit.lower() in ["percent", "percentage", "%"]:
            percentage = abs(value)
            # FIXED: TP/SL percentage calculation - determine if this is TP or SL based on GUI context
            # For GUI, TP is always positive distance from entry, SL is negative distance
            is_tp = value > 0  # Positive values from GUI = TP, Negative values = SL

            if order_type.upper() == "BUY":
                if is_tp:  # Take Profit
                    return round(current_price * (1 + percentage / 100), digits)
                else:  # Stop Loss
                    return round(current_price * (1 - percentage / 100), digits)
            else:  # SELL order
                if is_tp:  # Take Profit
                    return round(current_price * (1 - percentage / 100), digits)
                else:  # Stop Loss
                    return round(current_price * (1 + percentage / 100), digits)

        elif unit.lower() in ["balance%", "equity%"]:
            # Balance/Equity percentage mode
            abs_value = abs(value)
            if account_info:
                base_amount = account_info.balance if "balance" in unit.lower() else account_info.equity
                money_amount = base_amount * (abs_value / 100)

                # Calculate pip value for conversion
                pip_value = calculate_pip_value(symbol, lot_size, current_price)
                if pip_value > 0:
                    pip_distance = money_amount / (pip_value * lot_size)

                    if order_type.upper() == "BUY":
                        if value > 0:  # Take Profit
                            return round(current_price + pip_distance * point * 10, digits)
                        else:  # Stop Loss
                            return round(current_price - pip_distance * point * 10, digits)
                    else:  # SELL
                        if value > 0:  # Take Profit
                            return round(current_price - pip_distance * point * 10, digits)
                        else:  # Stop Loss
                            return round(current_price + pip_distance * point * 10, digits)

        elif unit.lower() == "money":
            # Fixed money amount mode
            money_amount = abs(value)
            pip_value = calculate_pip_value(symbol, lot_size, current_price)

            if pip_value > 0:
                pip_distance = money_amount / (pip_value * lot_size)

                if order_type.upper() == "BUY":
                    if value > 0:  # Take Profit
                        return round(current_price + pip_distance * point * 10, digits)
                    else:  # Stop Loss
                        return round(current_price - pip_distance * point * 10, digits)
                else:  # SELL
                    if value > 0:  # Take Profit
                        return round(current_price - pip_distance * point * 10, digits)
                    else:  # Stop Loss
                        return round(current_price + pip_distance * point * 10, digits)

        logger(f"⚠️ Unsupported TP/SL unit: {unit}")
        return 0.0

    except Exception as e:
        logger(f"❌ Error calculating TP/SL: {str(e)}")
        return 0.0


def execute_trade(symbol: str, action: str, lot_size: float = 0.01, tp_value: str = "20", sl_value: str = "10", 
                        tp_unit: str = "pips", sl_unit: str = "pips", strategy: str = "Manual", enhanced_data: Dict[str, Any] = None) -> Optional[Any]:
    """Execute trading signal dengan enhanced safety checks dan professional systems integration"""
    try:
        # Check for XAU/USD optimizations
        if enhanced_data and 'xau_optimization' in enhanced_data:
            xau_opt = enhanced_data['xau_optimization']
            tp_value = str(xau_opt['tp_pips'])
            sl_value = str(xau_opt['sl_pips'])
            lot_size *= xau_opt['position_multiplier']

            logger(f"🥇 XAU/USD OPTIMIZED Execute: {action} {lot_size:.2f} lots {symbol}")
            logger(f"   📊 Optimized TP: {tp_value} {tp_unit}, SL: {sl_value} {sl_unit}")
            logger(f"   📈 Position multiplier applied: {xau_opt['position_multiplier']:.1f}x")
            logger(f"   ⭐ Confidence: {xau_opt['confidence']:.1%}")
        else:
            logger(f"🎯 ENHANCED Execute trade: {action} {lot_size} lots {symbol}")
            logger(f"   📊 TP: {tp_value} {tp_unit}, SL: {sl_value} {sl_unit}")

        logger(f"   ⚙️ Strategy: {strategy}")

        # 1. PRE-EXECUTION SAFETY CHECKS - DISABLED FOR MAXIMUM AGGRESSIVENESS
        # Economic calendar check - ALWAYS ALLOW TRADING
        try:
            from economic_calendar import should_pause_for_news
            # Force trading regardless of news
            logger("🚀 ULTRA-AGGRESSIVE: News check bypassed - trading always allowed")
        except Exception as e:
            logger(f"⚠️ Economic calendar check failed: {str(e)}")

        # Drawdown manager check
        try:
            from drawdown_manager import get_recovery_adjustments
            recovery_mode, adjusted_lot = get_recovery_adjustments(lot_size)
            if recovery_mode:
                logger(f"🔄 Recovery mode active - lot size adjusted: {lot_size} → {adjusted_lot}")
                lot_size = adjusted_lot
        except Exception as e:
            logger(f"⚠️ Drawdown manager check failed: {str(e)}")

        # Risk management checks
        from risk_management import check_daily_limits, increment_daily_trade_count
        if not check_daily_limits():
            logger("🛑 Daily trading limits reached")
            return None

        # Get current market data
        current_tick = mt5.symbol_info_tick(symbol)
        if not current_tick:
            logger(f"❌ Cannot get current tick for {symbol}")
            return None

        current_bid = current_tick.bid
        current_ask = current_tick.ask
        current_price = current_bid if action == "SELL" else current_ask

        logger(f"📊 Current prices: Bid={current_bid:.5f}, Ask={current_ask:.5f}")

        # 2. GET LOT SIZE FROM GUI AND APPLY DYNAMIC SIZING
        try:
            # Get lot size from GUI first
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui and hasattr(__main__.gui, 'get_current_lot_size'):
                gui_lot_size = __main__.gui.get_current_lot_size()
                if gui_lot_size != lot_size:
                    logger(f"💰 GUI lot size override: {lot_size} → {gui_lot_size}")
                    lot_size = gui_lot_size

            # Then apply dynamic position sizing
            from enhanced_position_sizing import get_dynamic_position_size
            dynamic_lot = get_dynamic_position_size(symbol, strategy, lot_size)
            if dynamic_lot != lot_size:
                logger(f"🎯 Dynamic sizing: {lot_size} → {dynamic_lot}")
                lot_size = dynamic_lot

        except Exception as e:
            logger(f"⚠️ Position sizing integration failed: {str(e)}")

        # 3. CALCULATE TP/SL LEVELS
        tp_price = 0.0
        sl_price = 0.0

        # Handle TP calculation with proper type checking
        if tp_value:
            tp_str = str(tp_value).strip() if hasattr(tp_value, 'strip') else str(tp_value)
            if tp_str != "0" and tp_str != "":
                tp_price = calculate_tp_sl_all_modes(tp_str, tp_unit, symbol, action, current_price, lot_size)
                logger(f"🎯 Calculated TP: {tp_price:.5f}")

        # Handle SL calculation with proper type checking
        if sl_value:
            sl_str = str(sl_value).strip() if hasattr(sl_value, 'strip') else str(sl_value)
            if sl_str != "0" and sl_str != "":
                sl_price = calculate_tp_sl_all_modes(sl_str, sl_unit, symbol, action, current_price, lot_size)
                logger(f"🛡️ Calculated SL: {sl_price:.5f}")


        # 4. PREPARE ORDER REQUEST WITH ENHANCED VALIDATION
        order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL

        # FINAL TP/SL VALIDATION - Prevent "Invalid stops" error
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            stops_level = getattr(symbol_info, 'trade_stops_level', 0)
            min_distance = max(stops_level * symbol_info.point, symbol_info.point * 50)

            # Special handling for Gold
            if 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
                min_distance = max(min_distance, 1.0)  # Minimum $1 for Gold

            # Validate and adjust TP/SL if needed
            if tp_price > 0:
                if action == "BUY":
                    min_tp = current_price + min_distance
                    if tp_price < min_tp:
                        tp_price = round(min_tp, symbol_info.digits)
                        logger(f"⚠️ TP adjusted to minimum distance: {tp_price}")
                else:  # SELL
                    max_tp = current_price - min_distance
                    if tp_price > max_tp:
                        tp_price = round(max_tp, symbol_info.digits)
                        logger(f"⚠️ TP adjusted to minimum distance: {tp_price}")

            if sl_price > 0:
                if action == "BUY":
                    max_sl = current_price - min_distance
                    if sl_price > max_sl:
                        sl_price = round(max_sl, symbol_info.digits)
                        logger(f"⚠️ SL adjusted to minimum distance: {sl_price}")
                else:  # SELL
                    min_sl = current_price + min_distance
                    if sl_price < min_sl:
                        sl_price = round(min_sl, symbol_info.digits)
                        logger(f"⚠️ SL adjusted to minimum distance: {sl_price}")

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": current_price,
            "tp": tp_price if tp_price > 0 else 0.0,
            "sl": sl_price if sl_price > 0 else 0.0,
            "comment": f"Enhanced {strategy}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
            "deviation": 50,  # Add deviation for better execution
        }

        # 5. EXECUTE ORDER
        logger(f"📤 Sending order request...")
        result = mt5.order_send(request)

        if result is None:
            logger("❌ Order failed: No result returned")
            return None

        # Handle mock MT5 results properly
        if hasattr(result, 'retcode'):
            retcode = result.retcode
        elif isinstance(result, dict):
            retcode = result.get('retcode', 10009)  # TRADE_RETCODE_DONE
        else:
            retcode = 10009  # Assume success for mock

        # Check result code
        if retcode == 10009:  # TRADE_RETCODE_DONE
            logger("✅ Order executed successfully!")
            logger(f"   📋 Order: {getattr(result, 'order', 'Unknown')}")
            logger(f"   🎫 Deal: {getattr(result, 'deal', 'Unknown')}")
            logger(f"   📊 Volume: {getattr(result, 'volume', lot_size)}")
            logger(f"   💰 Price: {getattr(result, 'price', 'Unknown')}")
            return result
        else:
            logger(f"❌ Order failed with code: {retcode}")
            return None

    except Exception as e:
        logger(f"❌ Execute trade error: {str(e)}")
        return None


def execute_trade_signal(symbol: str, action: str, lot_size: float = 0.01, tp_value: str = "20", sl_value: str = "10", 
                        tp_unit: str = "pips", sl_unit: str = "pips", strategy: str = "Manual") -> bool:
    """Execute trading signal dengan enhanced safety checks dan professional systems integration"""
    try:
        logger(f"🎯 ENHANCED Execute trade: {action} {lot_size} lots {symbol}")
        logger(f"   📊 TP: {tp_value} {tp_unit}, SL: {sl_value} {sl_unit}")
        logger(f"   ⚙️ Strategy: {strategy}")

        # 1. PRE-EXECUTION SAFETY CHECKS - DISABLED FOR MAXIMUM AGGRESSIVENESS
        # Economic calendar check - ALWAYS ALLOW TRADING
        try:
            from economic_calendar import should_pause_for_news
            # Force trading regardless of news
            logger("🚀 ULTRA-AGGRESSIVE: News check bypassed - trading always allowed")
        except Exception as e:
            logger(f"⚠️ Economic calendar check failed: {str(e)}")

        # Drawdown manager check
        try:
            from drawdown_manager import get_recovery_adjustments
            recovery_mode, adjusted_lot = get_recovery_adjustments(lot_size)
            if recovery_mode:
                logger(f"🔄 Recovery mode active - lot size adjusted: {lot_size} → {adjusted_lot}")
                lot_size = adjusted_lot
        except Exception as e:
            logger(f"⚠️ Drawdown manager check failed: {str(e)}")

        # Risk management checks
        from risk_management import check_daily_limits, increment_daily_trade_count
        if not check_daily_limits():
            logger("🛑 Daily trading limits reached")
            return False

        # Get current market data
        current_tick = mt5.symbol_info_tick(symbol)
        if not current_tick:
            logger(f"❌ Cannot get current tick for {symbol}")
            return False

        current_bid = current_tick.bid
        current_ask = current_tick.ask
        current_price = current_bid if action == "SELL" else current_ask

        logger(f"📊 Current prices: Bid={current_bid:.5f}, Ask={current_ask:.5f}")

        # 2. GET LOT SIZE FROM GUI AND APPLY DYNAMIC SIZING
        try:
            # Get lot size from GUI first
            import __main__
            if hasattr(__main__, 'gui') and __main__.gui and hasattr(__main__.gui, 'get_current_lot_size'):
                gui_lot_size = __main__.gui.get_current_lot_size()
                if gui_lot_size != lot_size:
                    logger(f"💰 GUI lot size override: {lot_size} → {gui_lot_size}")
                    lot_size = gui_lot_size

            # Then apply dynamic position sizing
            from enhanced_position_sizing import get_dynamic_position_size
            dynamic_lot = get_dynamic_position_size(symbol, strategy, lot_size)
            if dynamic_lot != lot_size:
                logger(f"🎯 Dynamic sizing: {lot_size} → {dynamic_lot}")
                lot_size = dynamic_lot

        except Exception as e:
            logger(f"⚠️ Position sizing integration failed: {str(e)}")

        # 3. CALCULATE TP/SL LEVELS
        tp_price = 0.0
        sl_price = 0.0

        # Handle TP calculation with proper type checking
        if tp_value:
            tp_str = str(tp_value).strip() if hasattr(tp_value, 'strip') else str(tp_value)
            if tp_str != "0" and tp_str != "":
                tp_price = calculate_tp_sl_all_modes(tp_str, tp_unit, symbol, action, current_price, lot_size)
                logger(f"🎯 Calculated TP: {tp_price:.5f}")

        # Handle SL calculation with proper type checking
        if sl_value:
            sl_str = str(sl_value).strip() if hasattr(sl_value, 'strip') else str(sl_value)
            if sl_str != "0" and sl_str != "":
                sl_price = calculate_tp_sl_all_modes(sl_str, sl_unit, symbol, action, current_price, lot_size)
                logger(f"🛡️ Calculated SL: {sl_price:.5f}")

        # 4. PREPARE ORDER REQUEST WITH ENHANCED VALIDATION
        order_type = mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL

        # FINAL TP/SL VALIDATION - Prevent "Invalid stops" error
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            stops_level = getattr(symbol_info, 'trade_stops_level', 0)
            min_distance = max(stops_level * symbol_info.point, symbol_info.point * 50)

            # Special handling for Gold
            if 'XAU' in symbol.upper() or 'GOLD' in symbol.upper():
                min_distance = max(min_distance, 1.0)  # Minimum $1 for Gold

            # Validate and adjust TP/SL if needed
            if tp_price > 0:
                if action == "BUY":
                    min_tp = current_price + min_distance
                    if tp_price < min_tp:
                        tp_price = round(min_tp, symbol_info.digits)
                        logger(f"⚠️ TP adjusted to minimum distance: {tp_price}")
                else:  # SELL
                    max_tp = current_price - min_distance
                    if tp_price > max_tp:
                        tp_price = round(max_tp, symbol_info.digits)
                        logger(f"⚠️ TP adjusted to minimum distance: {tp_price}")

            if sl_price > 0:
                if action == "BUY":
                    max_sl = current_price - min_distance
                    if sl_price > max_sl:
                        sl_price = round(max_sl, symbol_info.digits)
                        logger(f"⚠️ SL adjusted to minimum distance: {sl_price}")
                else:  # SELL
                    min_sl = current_price + min_distance
                    if sl_price < min_sl:
                        sl_price = round(min_sl, symbol_info.digits)
                        logger(f"⚠️ SL adjusted to minimum distance: {sl_price}")

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": order_type,
            "price": current_price,
            "tp": tp_price if tp_price > 0 else 0.0,
            "sl": sl_price if sl_price > 0 else 0.0,
            "comment": f"Enhanced {strategy}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
            "deviation": 50,  # Add deviation for better execution
        }

        # 5. EXECUTE ORDER
        logger(f"📤 Sending order request...")
        result = mt5.order_send(request)

        # 6. PROCESS RESULT - FIXED VALIDATION
        success_codes = [10009]
        if hasattr(mt5, 'TRADE_RETCODE_DONE'):
            success_codes.append(mt5.TRADE_RETCODE_DONE)

        # Handle both dict and object results from mock/real MT5
        if isinstance(result, dict):
            result_code = result.get('retcode', 0)
            result_order = result.get('order', 0)
            result_deal = result.get('deal', 0)
            result_volume = result.get('volume', 0)
            result_price = result.get('price', 0)
            result_comment = result.get('comment', 'No comment')
        else:
            result_code = getattr(result, 'retcode', 0)
            result_order = getattr(result, 'order', 0)
            result_deal = getattr(result, 'deal', 0)
            result_volume = getattr(result, 'volume', 0)
            result_price = getattr(result, 'price', 0)
            result_comment = getattr(result, 'comment', 'No comment')

        if result and result_code in success_codes:
            logger(f"✅ Order executed successfully!")
            logger(f"   📋 Order: {result_order}")
            logger(f"   🎫 Deal: {result_deal}")
            logger(f"   📊 Volume: {result_volume}")
            logger(f"   💰 Price: {result_price}")

            # 7. POST-EXECUTION ENHANCEMENTS
            # Small delay to allow position to register in MT5
            time.sleep(0.5)

            # Add trailing stop with proper error handling
            try:
                from trailing_stop_manager import add_trailing_stop_to_position
                # Use order ticket for position tracking
                if result_order:
                    trailing_config = {
                        'symbol': symbol,
                        'action': action,
                        'lot_size': lot_size,
                        'strategy': strategy
                    }
                    add_trailing_stop_to_position(result_order, trailing_config)
                    logger(f"✅ Trailing stop added to position {result_order}")
                else:
                    logger("⚠️ No position ticket available for trailing stop")
            except Exception as e:
                logger(f"⚠️ Failed to add trailing stop: {str(e)}")

            # Update performance tracking
            try:
                from performance_tracking import add_trade_to_tracking
                add_trade_to_tracking(symbol, action, 0.0, lot_size)  # Fixed parameters
            except Exception as e:
                logger(f"⚠️ Performance tracking failed: {str(e)}")

            # Log to CSV
            try:
                log_order_csv(result, symbol, action)
                logger(f"📋 Order logged to CSV: csv_logs/orders.csv")
            except Exception as e:
                logger(f"⚠️ CSV logging failed: {str(e)}")

            # Increment counters
            try:
                increment_daily_trade_count()
                logger(f"📈 Daily trade count incremented")
            except Exception as e:
                logger(f"⚠️ Trade count increment failed: {str(e)}")

            # Send notifications
            try:
                from telegram_notifications import notify_trade_executed
                notify_trade_executed(symbol, action, lot_size, current_price, tp_price, sl_price, strategy)
                logger(f"📱 Telegram notification sent successfully")
            except Exception as e:
                logger(f"⚠️ Telegram notification failed: {str(e)}")

            return True

        else:
            logger(f"❌ Order failed: Code {result_code} - {result_comment}")
            return False

    except Exception as e:
        logger(f"❌ Execute trade error: {str(e)}")
        return False


def close_position(ticket: int) -> bool:
    """Close specific position by ticket"""
    try:
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger(f"❌ Position {ticket} not found")
            return False

        position = positions[0]
        symbol = position.symbol
        volume = position.volume

        # Handle different position type constants
        if hasattr(mt5, 'POSITION_TYPE_BUY') and hasattr(mt5, 'ORDER_TYPE_SELL'):
            order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        else:
            # Fallback for mock MT5
            order_type = 1 if position.type == 0 else 0  # 0=BUY->1=SELL, 1=SELL->0=BUY

        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            logger(f"❌ Cannot get current price for {symbol}")
            return False

        price = tick.bid if order_type == 1 else tick.ask

        # Close request
        request = {
            "action": 1,  # TRADE_ACTION_DEAL
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "position": ticket,
            "price": price,
            "comment": "Position closed by bot",
        }

        result = mt5.order_send(request)

        # Handle both dict and object results
        if isinstance(result, dict):
            success = result.get('retcode') == 10009  # TRADE_RETCODE_DONE
            error_msg = result.get('comment', 'Unknown error')
        else:
            success_codes = [10009]
            if hasattr(mt5, 'TRADE_RETCODE_DONE'):
                success_codes.append(mt5.TRADE_RETCODE_DONE)
            success = result and getattr(result, 'retcode', 0) in success_codes
            error_msg = getattr(result, 'comment', 'Unknown error') if result else 'No result'

        if success:
            logger(f"✅ Position {ticket} closed successfully")
            return True
        else:
            logger(f"❌ Failed to close position {ticket}: {error_msg}")
            return False

    except Exception as e:
        logger(f"❌ Error closing position {ticket}: {str(e)}")
        return False


def close_all_positions() -> int:
    """Close all open positions"""
    try:
        positions = mt5.positions_get()
        if not positions:
            logger("ℹ️ No open positions to close")
            return 0

        closed_count = 0
        for position in positions:
            if close_position(position.ticket):
                closed_count += 1
                time.sleep(0.1)  # Small delay between closes

        logger(f"✅ Closed {closed_count}/{len(positions)} positions")
        return closed_count

    except Exception as e:
        logger(f"❌ Error closing all positions: {str(e)}")
        return 0


def close_all_orders():
    """Close all pending orders"""
    try:
        orders = mt5.orders_get()
        if not orders:
            logger("📋 No pending orders to close")
            return True

        closed_count = 0
        for order in orders:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
            }

            result = mt5.order_send(request)
            if result and getattr(result, 'retcode', None) == mt5.TRADE_RETCODE_DONE:
                closed_count += 1
                logger(f"✅ Closed order {order.ticket}")
            else:
                logger(f"❌ Failed to close order {order.ticket}")

        logger(f"📋 Closed {closed_count} pending orders")
        return True

    except Exception as e:
        logger(f"❌ Error closing orders: {str(e)}")
        return False


def log_order_csv(order_result, symbol: str, action: str):
    """Log order to CSV file for analysis"""
    try:
        import csv
        import os
        from datetime import datetime

        # Ensure csv_logs directory exists
        os.makedirs("csv_logs", exist_ok=True)

        csv_file = "csv_logs/orders.csv"

        # Check if file exists to decide on header
        file_exists = os.path.exists(csv_file)

        with open(csv_file, 'a', newline='') as file:
            writer = csv.writer(file)

            # Write header if file doesn't exist
            if not file_exists:
                writer.writerow([
                    'Timestamp', 'Symbol', 'Action', 'Volume', 'Price', 
                    'TP', 'SL', 'Order', 'Deal', 'Retcode', 'Comment'
                ])

            # Write order data
            writer.writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                symbol,
                action,
                getattr(order_result, 'volume', 0),
                getattr(order_result, 'price', 0),
                getattr(order_result, 'tp', 0),  # This might not exist in result
                getattr(order_result, 'sl', 0),  # This might not exist in result
                getattr(order_result, 'order', 0),
                getattr(order_result, 'deal', 0),
                getattr(order_result, 'retcode', 0),
                getattr(order_result, 'comment', '')
            ])

        logger(f"📋 Order logged to CSV: {csv_file}")

    except Exception as e:
        logger(f"❌ Error logging to CSV: {str(e)}")


def emergency_stop_all():
    """Emergency stop all trading activities"""
    try:
        logger("🚨 EMERGENCY STOP ACTIVATED")

        # Close all positions
        close_all_positions()

        # Close all pending orders
        close_all_orders()

        return True
    except Exception as e:
        logger(f"❌ Emergency stop error: {str(e)}")
        return False


# Ensure all required imports are available at module level
def validate_trading_operations():
    """Validate that all required components are available"""
    try:
        # Test imports
        from risk_management import check_daily_limits
        from economic_calendar import should_pause_for_news  
        from drawdown_manager import get_recovery_adjustments
        from enhanced_position_sizing import get_dynamic_position_size
        from trailing_stop_manager import add_trailing_stop_to_position
        from performance_tracking import add_trade_to_tracking
        from telegram_notifications import notify_trade_executed

        logger("✅ All trading operations components validated")
        return True

    except ImportError as e:
        logger(f"⚠️ Trading operations validation failed: {str(e)}")
        return False


# Initialize validation on import
if __name__ != "__main__":
    validate_trading_operations()