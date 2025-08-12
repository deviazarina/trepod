
# --- XAU/USD Scalping Optimizer ---
"""
Dedicated scalping optimizer untuk XAUUSDm dan XAUUSDc
Focus pada 90%+ win rate dengan ultra-aggressive profitable strategies
"""

import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, List, Optional, Tuple
from logger_utils import logger

# Smart MT5 connection
try:
    import MetaTrader5 as mt5
    USING_REAL_MT5 = True
except ImportError:
    import mt5_mock as mt5
    USING_REAL_MT5 = False


class XAUUSDScalpingOptimizer:
    """Ultra-optimized scalping engine khusus untuk XAU/USD pairs"""
    
    def __init__(self):
        # XAU/USD specific symbols
        self.symbols = ["XAUUSDm", "XAUUSDc"]
        
        # Ultra-aggressive confidence thresholds untuk lebih banyak opportunities
        self.confidence_thresholds = {
            'ultra_high': 0.85,    # 85%+ - maximum position
            'very_high': 0.75,     # 75%+ - high position  
            'high': 0.65,          # 65%+ - normal position
            'moderate': 0.55,      # 55%+ - reduced position
            'minimum': 0.45        # 45%+ - minimal position (very aggressive)
        }
        
        # XAU/USD specific trading parameters
        self.xau_config = {
            'optimal_spread_usd': 5.0,     # Maximum spread in USD
            'min_volatility_pips': 150,    # Minimum pip movement for entry
            'max_volatility_pips': 600,    # Maximum safe volatility
            'session_multipliers': {
                'LONDON': 1.3,     # London session boost
                'NEW_YORK': 1.5,   # NY session highest
                'OVERLAP': 1.8,    # London-NY overlap maximum
                'ASIAN': 0.7       # Asian session reduced
            },
            'news_impact_levels': {
                'USD': 1.5,        # USD news impact multiplier
                'FED': 2.0,        # Federal Reserve events
                'INFLATION': 1.8,   # Inflation data
                'EMPLOYMENT': 1.6   # Employment data
            }
        }
        
        # Advanced signal components with XAU/USD weighting
        self.signal_weights = {
            'price_action': 0.25,      # 25% - XAU/USD responds well to PA
            'volume_profile': 0.20,    # 20% - Volume crucial for gold
            'institutional_flow': 0.20, # 20% - Smart money tracking
            'technical_confluence': 0.15, # 15% - Multi-indicator
            'session_alignment': 0.10,  # 10% - Session-based
            'volatility_filter': 0.10   # 10% - Volatility assessment
        }

    def analyze_xauusd_scalping_signal(self, symbol: str) -> Dict[str, Any]:
        """Generate ultra-high confidence XAU/USD scalping signal"""
        try:
            if symbol not in self.symbols:
                return {'signal': None, 'confidence': 0, 'reason': 'Unsupported symbol'}
            
            logger(f"🔍 XAU/USD SCALPING ANALYSIS: {symbol}")
            
            # Get comprehensive market data
            m1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
            m5_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
            
            if not m1_data or not m5_data or len(m1_data) < 20:
                return {'signal': None, 'confidence': 0, 'reason': 'Insufficient data'}
            
            m1_df = pd.DataFrame(m1_data)
            m5_df = pd.DataFrame(m5_data)
            
            # Initialize analysis result
            analysis_result = {
                'signal': None,
                'confidence': 0,
                'components': {},
                'entry_price': 0,
                'tp_pips': 15,
                'sl_pips': 8,
                'position_size_multiplier': 1.0,
                'reasons': []
            }
            
            # Component 1: Advanced Price Action Analysis
            pa_analysis = self._analyze_xau_price_action(m1_df, m5_df)
            analysis_result['components']['price_action'] = pa_analysis
            
            # Component 2: Volume Profile Analysis
            volume_analysis = self._analyze_xau_volume_profile(m1_df)
            analysis_result['components']['volume_profile'] = volume_analysis
            
            # Component 3: Institutional Flow Detection
            institutional_analysis = self._analyze_institutional_flow(m1_df, m5_df)
            analysis_result['components']['institutional_flow'] = institutional_analysis
            
            # Component 4: Technical Confluence
            technical_analysis = self._analyze_technical_confluence(m1_df, m5_df)
            analysis_result['components']['technical_confluence'] = technical_analysis
            
            # Component 5: Session Alignment
            session_analysis = self._analyze_session_alignment(symbol)
            analysis_result['components']['session_alignment'] = session_analysis
            
            # Component 6: Volatility Filter
            volatility_analysis = self._analyze_volatility_filter(m1_df)
            analysis_result['components']['volatility_filter'] = volatility_analysis
            
            # Calculate weighted confidence
            total_confidence = 0
            signal_direction = None
            signal_strength = 0
            
            for component, weight in self.signal_weights.items():
                comp_data = analysis_result['components'].get(component, {})
                if comp_data.get('valid', False):
                    comp_confidence = comp_data.get('confidence', 0)
                    comp_signal = comp_data.get('signal')
                    
                    total_confidence += comp_confidence * weight
                    
                    if comp_signal in ['BUY', 'SELL']:
                        if signal_direction is None:
                            signal_direction = comp_signal
                            signal_strength = comp_confidence
                        elif signal_direction == comp_signal:
                            signal_strength += comp_confidence * 0.5
                        else:
                            signal_strength -= comp_confidence * 0.3  # Conflict penalty
            
            # Determine final signal
            if signal_direction and signal_strength > 2.0 and total_confidence >= self.confidence_thresholds['minimum']:
                analysis_result['signal'] = signal_direction
                analysis_result['confidence'] = min(0.98, total_confidence)
                
                # Optimize TP/SL based on confidence
                tp_sl = self._optimize_tp_sl(analysis_result['confidence'], volatility_analysis)
                analysis_result['tp_pips'] = tp_sl['tp']
                analysis_result['sl_pips'] = tp_sl['sl']
                
                # Calculate position size multiplier
                analysis_result['position_size_multiplier'] = self._calculate_position_multiplier(
                    analysis_result['confidence'], session_analysis
                )
                
                analysis_result['reasons'] = self._generate_signal_reasons(analysis_result['components'])
                
                logger(f"✅ XAU/USD SIGNAL: {signal_direction} with {total_confidence:.1%} confidence")
            else:
                analysis_result['reason'] = f"Insufficient signal strength: {signal_strength:.1f} or confidence: {total_confidence:.1%}"
                logger(f"❌ XAU/USD: No signal - {analysis_result['reason']}")
            
            return analysis_result
            
        except Exception as e:
            logger(f"❌ XAU/USD scalping analysis error: {str(e)}")
            return {'signal': None, 'confidence': 0, 'reason': f'Analysis error: {str(e)}'}

    def _analyze_xau_price_action(self, m1_df: pd.DataFrame, m5_df: pd.DataFrame) -> Dict[str, Any]:
        """Advanced price action analysis untuk XAU/USD"""
        try:
            if len(m1_df) < 20 or len(m5_df) < 10:
                return {'valid': False}
            
            # Convert to float
            for col in ['open', 'high', 'low', 'close']:
                m1_df[col] = m1_df[col].astype(float)
                m5_df[col] = m5_df[col].astype(float)
            
            pa_analysis = {
                'valid': True,
                'signal': None,
                'confidence': 0,
                'patterns': []
            }
            
            # 1. Engulfing patterns detection
            engulfing_score = 0
            for i in range(1, min(5, len(m1_df))):
                current = m1_df.iloc[-i]
                previous = m1_df.iloc[-i-1]
                
                # Bullish engulfing
                if (current['close'] > current['open'] and 
                    previous['close'] < previous['open'] and
                    current['open'] < previous['close'] and
                    current['close'] > previous['open']):
                    engulfing_score += 2
                    pa_analysis['patterns'].append('Bullish Engulfing')
                
                # Bearish engulfing
                elif (current['close'] < current['open'] and 
                      previous['close'] > previous['open'] and
                      current['open'] > previous['close'] and
                      current['close'] < previous['open']):
                    engulfing_score -= 2
                    pa_analysis['patterns'].append('Bearish Engulfing')
            
            # 2. Pin bar detection
            pin_bar_score = 0
            for i in range(3):
                candle = m1_df.iloc[-(i+1)]
                body_size = abs(candle['close'] - candle['open'])
                total_size = candle['high'] - candle['low']
                
                if total_size > 0:
                    upper_wick = candle['high'] - max(candle['open'], candle['close'])
                    lower_wick = min(candle['open'], candle['close']) - candle['low']
                    
                    # Bullish pin bar (long lower wick)
                    if lower_wick > body_size * 2 and lower_wick > upper_wick * 2:
                        pin_bar_score += 1.5
                        pa_analysis['patterns'].append('Bullish Pin Bar')
                    
                    # Bearish pin bar (long upper wick)
                    elif upper_wick > body_size * 2 and upper_wick > lower_wick * 2:
                        pin_bar_score -= 1.5
                        pa_analysis['patterns'].append('Bearish Pin Bar')
            
            # 3. Support/Resistance breaks
            sr_score = 0
            recent_highs = m5_df['high'].tail(10).max()
            recent_lows = m5_df['low'].tail(10).min()
            current_price = m1_df['close'].iloc[-1]
            
            # Resistance break (bullish)
            if current_price > recent_highs * 1.0005:  # 0.05% break
                sr_score += 2
                pa_analysis['patterns'].append('Resistance Break')
            
            # Support break (bearish)
            elif current_price < recent_lows * 0.9995:  # 0.05% break
                sr_score -= 2
                pa_analysis['patterns'].append('Support Break')
            
            # Calculate final score and signal
            total_score = engulfing_score + pin_bar_score + sr_score
            
            if total_score >= 3:
                pa_analysis['signal'] = 'BUY'
                pa_analysis['confidence'] = min(0.9, (total_score / 6) * 0.9)
            elif total_score <= -3:
                pa_analysis['signal'] = 'SELL'
                pa_analysis['confidence'] = min(0.9, (abs(total_score) / 6) * 0.9)
            else:
                pa_analysis['confidence'] = 0.3  # Neutral
            
            return pa_analysis
            
        except Exception as e:
            logger(f"❌ Price action analysis error: {str(e)}")
            return {'valid': False}

    def _analyze_xau_volume_profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Volume profile analysis untuk XAU/USD"""
        try:
            if len(df) < 20:
                return {'valid': False}
            
            volume_analysis = {
                'valid': True,
                'signal': None,
                'confidence': 0,
                'volume_trend': 'NEUTRAL'
            }
            
            # Calculate volume metrics
            recent_volume = df['tick_volume'].tail(5).mean()
            avg_volume = df['tick_volume'].tail(20).mean()
            
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # Price-volume relationship
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]
            
            # Volume confirmation scoring
            if volume_ratio > 1.5:  # High volume
                if price_change > 0.001:  # Price up with volume
                    volume_analysis['signal'] = 'BUY'
                    volume_analysis['confidence'] = 0.8
                    volume_analysis['volume_trend'] = 'BULLISH_SURGE'
                elif price_change < -0.001:  # Price down with volume
                    volume_analysis['signal'] = 'SELL'
                    volume_analysis['confidence'] = 0.8
                    volume_analysis['volume_trend'] = 'BEARISH_SURGE'
            elif volume_ratio > 1.2:  # Moderate volume
                volume_analysis['confidence'] = 0.6
                volume_analysis['volume_trend'] = 'ACTIVE'
            else:  # Low volume
                volume_analysis['confidence'] = 0.3
                volume_analysis['volume_trend'] = 'QUIET'
            
            return volume_analysis
            
        except Exception as e:
            logger(f"❌ Volume analysis error: {str(e)}")
            return {'valid': False}

    def _analyze_institutional_flow(self, m1_df: pd.DataFrame, m5_df: pd.DataFrame) -> Dict[str, Any]:
        """Institutional flow analysis"""
        try:
            institutional_analysis = {
                'valid': True,
                'signal': None,
                'confidence': 0,
                'flow_type': 'NEUTRAL'
            }
            
            # Look for institutional characteristics
            institutional_signals = 0
            
            # Large volume with narrow spread (accumulation/distribution)
            for i in range(1, min(6, len(m1_df))):
                candle = m1_df.iloc[-i]
                volume_ratio = candle.get('tick_volume', 1000) / m1_df['tick_volume'].mean()
                spread_ratio = (candle['high'] - candle['low']) / candle['close']
                
                if volume_ratio > 1.8 and spread_ratio < 0.002:  # High vol, low spread
                    if candle['close'] > candle['open']:
                        institutional_signals += 1  # Bullish accumulation
                        institutional_analysis['flow_type'] = 'ACCUMULATION'
                    else:
                        institutional_signals -= 1  # Bearish distribution
                        institutional_analysis['flow_type'] = 'DISTRIBUTION'
            
            # Determine signal and confidence
            if institutional_signals >= 2:
                institutional_analysis['signal'] = 'BUY'
                institutional_analysis['confidence'] = 0.75
            elif institutional_signals <= -2:
                institutional_analysis['signal'] = 'SELL'
                institutional_analysis['confidence'] = 0.75
            else:
                institutional_analysis['confidence'] = 0.4
            
            return institutional_analysis
            
        except Exception as e:
            logger(f"❌ Institutional flow error: {str(e)}")
            return {'valid': False}

    def _analyze_technical_confluence(self, m1_df: pd.DataFrame, m5_df: pd.DataFrame) -> Dict[str, Any]:
        """Technical confluence analysis"""
        try:
            # Calculate basic indicators
            from indicators import calculate_indicators
            
            m1_df = calculate_indicators(m1_df)
            m5_df = calculate_indicators(m5_df)
            
            if m1_df is None or m5_df is None:
                return {'valid': False}
            
            technical_analysis = {
                'valid': True,
                'signal': None,
                'confidence': 0,
                'indicators': []
            }
            
            last_m1 = m1_df.iloc[-1]
            last_m5 = m5_df.iloc[-1]
            
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI analysis
            if 'RSI' in m1_df.columns:
                rsi_m1 = last_m1['RSI']
                if 30 < rsi_m1 < 70:  # Not oversold/overbought
                    if rsi_m1 > 55:
                        bullish_signals += 1
                        technical_analysis['indicators'].append('RSI Bullish')
                    elif rsi_m1 < 45:
                        bearish_signals += 1
                        technical_analysis['indicators'].append('RSI Bearish')
            
            # MACD analysis
            if 'MACD' in m1_df.columns and 'MACD_signal' in m1_df.columns:
                if last_m1['MACD'] > last_m1['MACD_signal']:
                    bullish_signals += 1
                    technical_analysis['indicators'].append('MACD Bullish')
                else:
                    bearish_signals += 1
                    technical_analysis['indicators'].append('MACD Bearish')
            
            # EMA alignment
            if all(col in m1_df.columns for col in ['EMA8', 'EMA20', 'EMA50']):
                if last_m1['close'] > last_m1['EMA8'] > last_m1['EMA20']:
                    bullish_signals += 2
                    technical_analysis['indicators'].append('EMA Bullish Alignment')
                elif last_m1['close'] < last_m1['EMA8'] < last_m1['EMA20']:
                    bearish_signals += 2
                    technical_analysis['indicators'].append('EMA Bearish Alignment')
            
            # Determine signal
            total_signals = bullish_signals + bearish_signals
            if total_signals > 0:
                if bullish_signals > bearish_signals:
                    technical_analysis['signal'] = 'BUY'
                    technical_analysis['confidence'] = min(0.85, bullish_signals / 5)
                elif bearish_signals > bullish_signals:
                    technical_analysis['signal'] = 'SELL'
                    technical_analysis['confidence'] = min(0.85, bearish_signals / 5)
                else:
                    technical_analysis['confidence'] = 0.4
            
            return technical_analysis
            
        except Exception as e:
            logger(f"❌ Technical confluence error: {str(e)}")
            return {'valid': False}

    def _analyze_session_alignment(self, symbol: str) -> Dict[str, Any]:
        """Session alignment analysis"""
        try:
            current_hour = datetime.datetime.utcnow().hour
            
            session_analysis = {
                'valid': True,
                'session': 'UNKNOWN',
                'confidence': 0.5,
                'multiplier': 1.0
            }
            
            # Determine current session
            if 8 <= current_hour < 16:
                session_analysis['session'] = 'LONDON'
                session_analysis['multiplier'] = self.xau_config['session_multipliers']['LONDON']
                session_analysis['confidence'] = 0.8
            elif 13 <= current_hour < 21:
                if 13 <= current_hour < 16:
                    session_analysis['session'] = 'OVERLAP'
                    session_analysis['multiplier'] = self.xau_config['session_multipliers']['OVERLAP']
                    session_analysis['confidence'] = 0.95
                else:
                    session_analysis['session'] = 'NEW_YORK'
                    session_analysis['multiplier'] = self.xau_config['session_multipliers']['NEW_YORK']
                    session_analysis['confidence'] = 0.85
            else:
                session_analysis['session'] = 'ASIAN'
                session_analysis['multiplier'] = self.xau_config['session_multipliers']['ASIAN']
                session_analysis['confidence'] = 0.4
            
            return session_analysis
            
        except Exception as e:
            logger(f"❌ Session analysis error: {str(e)}")
            return {'valid': False}

    def _analyze_volatility_filter(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Volatility filter analysis"""
        try:
            volatility_analysis = {
                'valid': True,
                'confidence': 0.5,
                'volatility_level': 'NORMAL'
            }
            
            # Calculate ATR-like volatility
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift(1))
            low_close = abs(df['low'] - df['close'].shift(1))
            
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            current_volatility = true_range.tail(10).mean()
            avg_volatility = true_range.tail(50).mean()
            
            volatility_ratio = current_volatility / avg_volatility if avg_volatility > 0 else 1
            
            # Optimal volatility for XAU/USD scalping
            if 0.8 <= volatility_ratio <= 1.4:
                volatility_analysis['confidence'] = 0.8
                volatility_analysis['volatility_level'] = 'OPTIMAL'
            elif 0.6 <= volatility_ratio <= 1.8:
                volatility_analysis['confidence'] = 0.6
                volatility_analysis['volatility_level'] = 'ACCEPTABLE'
            else:
                volatility_analysis['confidence'] = 0.3
                volatility_analysis['volatility_level'] = 'EXTREME'
            
            return volatility_analysis
            
        except Exception as e:
            logger(f"❌ Volatility analysis error: {str(e)}")
            return {'valid': False}

    def _optimize_tp_sl(self, confidence: float, volatility_data: Dict[str, Any]) -> Dict[str, int]:
        """Optimize TP/SL based on confidence and volatility"""
        try:
            base_tp = 15
            base_sl = 8
            
            # Confidence adjustments
            if confidence >= 0.85:
                tp_multiplier = 1.8
                sl_multiplier = 0.7
            elif confidence >= 0.75:
                tp_multiplier = 1.5
                sl_multiplier = 0.8
            elif confidence >= 0.65:
                tp_multiplier = 1.3
                sl_multiplier = 0.9
            else:
                tp_multiplier = 1.0
                sl_multiplier = 1.0
            
            # Volatility adjustments
            volatility_level = volatility_data.get('volatility_level', 'NORMAL')
            if volatility_level == 'OPTIMAL':
                tp_multiplier *= 1.2
            elif volatility_level == 'EXTREME':
                tp_multiplier *= 0.8
                sl_multiplier *= 1.2
            
            return {
                'tp': max(10, int(base_tp * tp_multiplier)),
                'sl': max(5, int(base_sl * sl_multiplier))
            }
            
        except Exception as e:
            logger(f"❌ TP/SL optimization error: {str(e)}")
            return {'tp': 15, 'sl': 8}

    def _calculate_position_multiplier(self, confidence: float, session_data: Dict[str, Any]) -> float:
        """Calculate position size multiplier"""
        try:
            # Base multiplier from confidence
            if confidence >= 0.85:
                base_multiplier = 2.0
            elif confidence >= 0.75:
                base_multiplier = 1.5
            elif confidence >= 0.65:
                base_multiplier = 1.2
            else:
                base_multiplier = 1.0
            
            # Session multiplier
            session_multiplier = session_data.get('multiplier', 1.0)
            
            return min(3.0, base_multiplier * session_multiplier)
            
        except Exception as e:
            logger(f"❌ Position multiplier error: {str(e)}")
            return 1.0

    def _generate_signal_reasons(self, components: Dict[str, Any]) -> List[str]:
        """Generate human-readable signal reasons"""
        reasons = []
        
        for component_name, data in components.items():
            if data.get('valid', False) and data.get('confidence', 0) > 0.6:
                signal = data.get('signal')
                if signal:
                    reasons.append(f"{component_name.replace('_', ' ').title()}: {signal}")
                
                # Add specific patterns/indicators
                if 'patterns' in data:
                    reasons.extend(data['patterns'])
                if 'indicators' in data:
                    reasons.extend(data['indicators'])
        
        return reasons


# Global instance
xauusd_scalping_optimizer = XAUUSDScalpingOptimizer()


def get_xauusd_scalping_signal(symbol: str) -> Dict[str, Any]:
    """Get optimized XAU/USD scalping signal"""
    return xauusd_scalping_optimizer.analyze_xauusd_scalping_signal(symbol)


def validate_xauusd_scalping_conditions(symbol: str) -> Dict[str, Any]:
    """Validate optimal conditions for XAU/USD scalping"""
    try:
        # Check spread
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return {'valid': False, 'reason': 'No tick data'}
        
        spread_usd = (tick.ask - tick.bid)
        spread_acceptable = spread_usd <= 5.0  # 5 USD spread limit
        
        # Check session
        current_hour = datetime.datetime.utcnow().hour
        optimal_session = 8 <= current_hour <= 21  # London + NY sessions
        
        # Check volatility (simplified)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 20)
        volatility_ok = True
        if rates and len(rates) >= 10:
            df = pd.DataFrame(rates)
            price_range = (df['high'].max() - df['low'].min()) / df['close'].mean()
            volatility_ok = 0.001 <= price_range <= 0.01  # 0.1% to 1% range
        
        return {
            'valid': spread_acceptable and optimal_session and volatility_ok,
            'spread_usd': spread_usd,
            'spread_acceptable': spread_acceptable,
            'optimal_session': optimal_session,
            'volatility_ok': volatility_ok,
            'current_hour': current_hour
        }
        
    except Exception as e:
        logger(f"❌ XAU/USD validation error: {str(e)}")
        return {'valid': False, 'reason': str(e)}
