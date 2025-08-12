#!/usr/bin/env python3
"""
XAUUSD/BTCUSD ULTRA-AGGRESSIVE SCALPING ENGINE
Professional-grade enhancement for 2 billion monthly profit trader
Enhanced market adaptability with real-time candle analysis
"""

import datetime
from typing import Dict, Any, List, Optional, Tuple
from logger_utils import logger

# SMART MT5 Connection
try:
    import MetaTrader5 as mt5
    logger("✅ XAUUSD Ultra-Scalper using REAL MT5")
except ImportError:
    import mt5_mock as mt5
    logger("⚠️ XAUUSD Ultra-Scalper using mock for development")

class XAUUSDUltraScalper:
    """Ultra-aggressive scalping engine specifically for XAUUSD/BTCUSD"""

    def __init__(self):
        self.target_symbols = ['XAUUSDm', 'XAUUSDc', 'XAUUSD', 'BTCUSDm', 'BTCUSDc', 'BTCUSD']
        self.ultra_aggressive_mode = True
        self.real_time_adaptation = True

        # Ultra-aggressive parameters
        self.xauusd_params = {
            'min_tp_pips': 6,   # Reduced for more aggressive
            'max_tp_pips': 12,  # Reduced for faster profits
            'min_sl_pips': 3,   # Tighter stops
            'max_sl_pips': 6,   # Maximum risk
            'confidence_threshold': 0.25,  # Lower threshold = more trades
            'lot_multiplier': 2.0,  # Aggressive position sizing
            'scalp_frequency': 30,  # Seconds between scans
            'news_ignore': True,    # Trade through news
            'session_boost': {
                'LONDON': 1.5,
                'NEW_YORK': 2.0,
                'OVERLAP': 2.2
            }
        }

        self.btcusd_params = {
            'min_tp_pips': 10,
            'max_tp_pips': 20,
            'min_sl_pips': 5,
            'max_sl_pips': 10,
            'confidence_threshold': 0.30,
            'lot_multiplier': 2.5,
            'scalp_frequency': 45,
            'news_ignore': True,
            'session_boost': {
                'LONDON': 1.3,
                'NEW_YORK': 2.0,
                'OVERLAP': 2.5
            }
        }

        logger("🚀 XAUUSD/BTCUSD Ultra-Scalper initialized")
        logger(f"🎯 Target symbols: {', '.join(self.target_symbols)}")


    def enhanced_candle_analysis(self, symbol: str, timeframe: int = 1) -> Dict[str, Any]:
        """
        Real-time candle analysis with news adaptation
        Analyzes current candle formation for ultra-precise entry
        """
        try:
            # Get recent candles for pattern analysis
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 10)
            if not rates or len(rates) < 5:
                return {'signal': None, 'confidence': 0.0, 'reason': 'Insufficient data'}

            current_candle = rates[-1]
            prev_candles = rates[-5:-1]

            # Real-time candle formation analysis
            open_price = current_candle[1]  # Open
            high_price = current_candle[2]  # High
            low_price = current_candle[3]   # Low
            close_price = current_candle[4] # Close
            volume = current_candle[5] if len(current_candle) > 5 else 0

            # Calculate candle properties
            body_size = abs(close_price - open_price)
            upper_shadow = high_price - max(open_price, close_price)
            lower_shadow = min(open_price, close_price) - low_price
            total_range = high_price - low_price

            # Determine candle type and strength
            is_bullish = close_price > open_price
            body_ratio = body_size / total_range if total_range > 0 else 0

            # Enhanced pattern recognition
            signal_strength = 0.0
            signal_type = None
            reasons = []

            # 1. Strong directional candle (body > 70% of range)
            if body_ratio > 0.7:
                signal_strength += 0.3
                signal_type = 'BUY' if is_bullish else 'SELL'
                reasons.append(f"Strong {'bullish' if is_bullish else 'bearish'} candle")

            # 2. Momentum continuation (3 consecutive same-direction candles)
            consecutive_count = 1
            last_direction = is_bullish
            for candle in reversed(prev_candles[-3:]):
                candle_bullish = candle[4] > candle[1]  # close > open
                if candle_bullish == last_direction:
                    consecutive_count += 1
                else:
                    break

            if consecutive_count >= 3:
                signal_strength += 0.25
                reasons.append(f"Momentum continuation ({consecutive_count} candles)")

            # 3. Volume confirmation (if available)
            if volume > 0:
                # Check if current volume is higher than average
                avg_volume = sum([c[5] if len(c) > 5 else 0 for c in prev_candles]) / len(prev_candles)
                if volume > avg_volume * 1.2:
                    signal_strength += 0.15
                    reasons.append("High volume confirmation")

            # 4. Shadow analysis for rejection/continuation
            if upper_shadow < body_size * 0.2 and lower_shadow < body_size * 0.2:
                # Marubozu-like candle = strong direction
                signal_strength += 0.2
                reasons.append("Strong directional candle (minimal shadows)")

            # 5. Gap analysis (price gaps from previous close)
            prev_close = prev_candles[-1][4]
            gap_size = abs(open_price - prev_close)
            avg_body = sum([abs(c[4] - c[1]) for c in prev_candles]) / len(prev_candles)

            if gap_size > avg_body * 0.5:
                signal_strength += 0.1
                gap_direction = 'up' if open_price > prev_close else 'down'
                reasons.append(f"Price gap {gap_direction}")

            # Ultra-aggressive mode adjustments
            if self.ultra_aggressive_mode:
                signal_strength *= 1.3  # Boost all signals
                if signal_strength > 0.25:  # Lower threshold for ultra mode
                    if not signal_type:
                        signal_type = 'BUY' if is_bullish else 'SELL'

            return {
                'signal': signal_type,
                'confidence': min(signal_strength, 1.0),
                'reasons': reasons,
                'candle_data': {
                    'body_ratio': body_ratio,
                    'is_bullish': is_bullish,
                    'consecutive_candles': consecutive_count,
                    'volume_ratio': volume / avg_volume if volume > 0 and avg_volume > 0 else 0,
                    'gap_size': gap_size
                }
            }

        except Exception as e:
            logger(f"❌ Enhanced candle analysis error for {symbol}: {str(e)}")
            return {'signal': None, 'confidence': 0.0, 'reason': f'Analysis error: {str(e)}'}


    def market_condition_detector(self, symbol: str) -> Dict[str, Any]:
        """
        Detect current market conditions for optimal scalping
        Adapts to trending, ranging, volatile conditions
        """
        try:
            # Get different timeframe data for condition analysis
            rates_m1 = mt5.copy_rates_from_pos(symbol, 1, 0, 20)   # 1-minute
            rates_m5 = mt5.copy_rates_from_pos(symbol, 5, 0, 12)   # 5-minute
            rates_m15 = mt5.copy_rates_from_pos(symbol, 15, 0, 8)  # 15-minute

            if not all([rates_m1, rates_m5, rates_m15]):
                return {'condition': 'UNKNOWN', 'scalping_suitability': 0.5}

            # Calculate volatility across timeframes
            volatility_m1 = self._calculate_volatility(rates_m1)
            volatility_m5 = self._calculate_volatility(rates_m5)
            volatility_m15 = self._calculate_volatility(rates_m15)

            # Determine trending vs ranging
            trend_strength = self._calculate_trend_strength(rates_m5)

            # Market session analysis
            current_session = self._get_current_session()
            session_multiplier = self.xauusd_params['session_boost'].get(current_session, 1.0)

            # Determine market condition
            if volatility_m1 > 0.0015 and trend_strength > 0.6:
                condition = 'TRENDING_VOLATILE'
                scalping_suitability = 0.9 * session_multiplier
            elif volatility_m1 > 0.001 and trend_strength < 0.4:
                condition = 'RANGING_VOLATILE'
                scalping_suitability = 0.8 * session_multiplier
            elif trend_strength > 0.7:
                condition = 'STRONG_TREND'
                scalping_suitability = 0.85 * session_multiplier
            elif volatility_m1 < 0.0005:
                condition = 'LOW_VOLATILITY'
                scalping_suitability = 0.3 * session_multiplier
            else:
                condition = 'NORMAL_MARKET'
                scalping_suitability = 0.7 * session_multiplier

            return {
                'condition': condition,
                'scalping_suitability': min(scalping_suitability, 1.0),
                'volatility': {
                    'm1': volatility_m1,
                    'm5': volatility_m5,
                    'm15': volatility_m15
                },
                'trend_strength': trend_strength,
                'session': current_session,
                'session_multiplier': session_multiplier
            }

        except Exception as e:
            logger(f"❌ Market condition detection error: {str(e)}")
            return {'condition': 'ERROR', 'scalping_suitability': 0.5}


    def _calculate_volatility(self, rates) -> float:
        """Calculate volatility from price data"""
        try:
            if len(rates) < 2:
                return 0.0

            returns = []
            for i in range(1, len(rates)):
                prev_close = rates[i-1][4]  # Previous close
                curr_close = rates[i][4]    # Current close
                if prev_close > 0:
                    returns.append((curr_close - prev_close) / prev_close)

            if not returns:
                return 0.0

            # Calculate standard deviation of returns
            mean_return = sum(returns) / len(returns)
            variance = sum([(r - mean_return) ** 2 for r in returns]) / len(returns)
            volatility = variance ** 0.5

            return volatility

        except Exception:
            return 0.001  # Default moderate volatility


    def _calculate_trend_strength(self, rates) -> float:
        """Calculate trend strength (0 = ranging, 1 = strong trend)"""
        try:
            if len(rates) < 5:
                return 0.0

            closes = [r[4] for r in rates]

            # Simple linear regression slope
            n = len(closes)
            x_mean = (n - 1) / 2
            y_mean = sum(closes) / n

            numerator = sum([(i - x_mean) * (closes[i] - y_mean) for i in range(n)])
            denominator = sum([(i - x_mean) ** 2 for i in range(n)])

            if denominator == 0:
                return 0.0

            slope = numerator / denominator

            # Normalize slope to 0-1 range
            price_range = max(closes) - min(closes)
            if price_range == 0:
                return 0.0

            normalized_slope = abs(slope) / price_range * n
            return min(normalized_slope, 1.0)

        except Exception:
            return 0.5  # Default moderate trend


    def _get_current_session(self) -> str:
        """Determine current trading session"""
        try:
            utc_hour = datetime.datetime.utcnow().hour

            if 0 <= utc_hour <= 9:
                return 'ASIAN'
            elif 8 <= utc_hour <= 17:
                return 'LONDON'
            elif 13 <= utc_hour <= 22:
                return 'NEW_YORK'
            elif (8 <= utc_hour <= 17) and (13 <= utc_hour <= 17):
                return 'OVERLAP'  # London-NY overlap
            else:
                return 'OFF_HOURS'

        except Exception:
            return 'UNKNOWN'


    def generate_ultra_scalping_signal(self, symbol: str) -> Dict[str, Any]:
        """
        Generate ultra-aggressive scalping signals
        Combines candle analysis with market conditions
        """
        try:
            # Get symbol parameters
            if 'XAU' in symbol or 'GOLD' in symbol:
                params = self.xauusd_params
            elif 'BTC' in symbol:
                params = self.btcusd_params
            else:
                params = self.xauusd_params  # Default to XAUUSD

            # Enhanced candle analysis
            candle_analysis = self.enhanced_candle_analysis(symbol)

            # Market condition detection
            market_condition = self.market_condition_detector(symbol)

            # Combine signals
            base_confidence = candle_analysis.get('confidence', 0.0)
            scalping_suitability = market_condition.get('scalping_suitability', 0.5)

            # Ultra-aggressive adjustments
            final_confidence = base_confidence * scalping_suitability

            if self.ultra_aggressive_mode:
                final_confidence *= 1.5  # Boost for ultra mode
                # Lower threshold for ultra-aggressive trading
                threshold = params['confidence_threshold'] * 0.7
            else:
                threshold = params['confidence_threshold']

            # Generate signal
            signal = None
            if final_confidence >= threshold:
                signal = candle_analysis.get('signal')

            # Calculate dynamic TP/SL based on market conditions
            volatility_factor = market_condition.get('volatility', {}).get('m1', 0.001)

            if signal:
                if volatility_factor > 0.002:  # High volatility
                    tp_pips = params['max_tp_pips']
                    sl_pips = params['max_sl_pips']
                else:  # Low volatility
                    tp_pips = params['min_tp_pips']
                    sl_pips = params['min_sl_pips']

                # Session boost for lot size
                session_boost = market_condition.get('session_multiplier', 1.0)
                lot_multiplier = params['lot_multiplier'] * session_boost
            else:
                tp_pips = sl_pips = lot_multiplier = 0

            return {
                'signal': signal,
                'confidence': final_confidence,
                'symbol': symbol,
                'tp_pips': tp_pips,
                'sl_pips': sl_pips,
                'lot_multiplier': lot_multiplier,
                'market_condition': market_condition['condition'],
                'scalping_suitability': scalping_suitability,
                'candle_reasons': candle_analysis.get('reasons', []),
                'ultra_mode': self.ultra_aggressive_mode,
                'session': market_condition.get('session', 'UNKNOWN')
            }

        except Exception as e:
            logger(f"❌ Ultra-scalping signal error for {symbol}: {str(e)}")
            return {
                'signal': None,
                'confidence': 0.0,
                'symbol': symbol,
                'error': str(e)
            }


# Global instance
ultra_scalper = XAUUSDUltraScalper()


def run_ultra_scalping_analysis(symbol: str) -> Dict[str, Any]:
    """Main function to run ultra-scalping analysis"""
    return ultra_scalper.generate_ultra_scalping_signal(symbol)


def get_scalping_symbols() -> List[str]:
    """Get list of ultra-scalping target symbols"""
    return ultra_scalper.target_symbols


if __name__ == "__main__":
    # Test the ultra-scalper
    for symbol in ['XAUUSDm', 'BTCUSDm']:
        result = run_ultra_scalping_analysis(symbol)
        logger(f"🎯 {symbol} Ultra-Scalping: {result}")