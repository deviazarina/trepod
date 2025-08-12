#!/usr/bin/env python3
"""
Smart Signal Validator - Validasi sinyal yang agresif tapi tidak ngawur
Memastikan setiap trade memiliki probabilitas tinggi untuk profit

Author: MT5 Advanced Trading Bot
Version: 4.0 - Smart Validation System
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from logger_utils import logger

class SmartSignalValidator:
    """Sistem validasi pintar untuk memastikan trading agresif tapi tidak ngawur"""
    
    def __init__(self):
        # Konfigurasi validasi berkualitas tinggi
        self.validation_weights = {
            'technical_confluence': 0.25,    # 25% - Konfluensi indikator teknikal
            'market_structure': 0.20,        # 20% - Struktur pasar yang sehat
            'volume_confirmation': 0.15,     # 15% - Konfirmasi volume
            'momentum_alignment': 0.15,      # 15% - Alignment momentum
            'risk_reward_ratio': 0.10,       # 10% - Risk/Reward yang baik
            'session_timing': 0.10,          # 10% - Timing session optimal
            'spread_conditions': 0.05        # 5% - Kondisi spread
        }
        
        # Threshold kualitas untuk berbagai level agresivitas
        self.quality_thresholds = {
            'ULTRA_HIGH': 0.85,    # Grade A+ - Trade terbaik, position size 2.5x
            'HIGH': 0.75,          # Grade A - Trade berkualitas, position size 1.8x
            'GOOD': 0.65,          # Grade B+ - Trade yang bagus, position size 1.4x
            'ACCEPTABLE': 0.55,    # Grade B - Trade yang diterima, position size 1.0x
            'MARGINAL': 0.45,      # Grade C - Trade marginal, position size 0.7x
            'REJECT': 0.35         # Grade D/F - Tolak trade
        }
        
        # Faktor koreksi berdasarkan volatilitas pasar
        self.volatility_adjustments = {
            'LOW': {'threshold_reduction': 0.05, 'confidence_bonus': 0.10},
            'NORMAL': {'threshold_reduction': 0.0, 'confidence_bonus': 0.0},
            'HIGH': {'threshold_reduction': -0.05, 'confidence_bonus': -0.05},  # Lebih ketat saat volatil
            'EXTREME': {'threshold_reduction': -0.10, 'confidence_bonus': -0.10}
        }
        
        # Tracking performa untuk learning adaptif
        self.performance_history = {
            'total_validated': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'win_rate': 0.0,
            'quality_performance': {
                'ULTRA_HIGH': {'total': 0, 'wins': 0, 'win_rate': 0.0},
                'HIGH': {'total': 0, 'wins': 0, 'win_rate': 0.0},
                'GOOD': {'total': 0, 'wins': 0, 'win_rate': 0.0},
                'ACCEPTABLE': {'total': 0, 'wins': 0, 'win_rate': 0.0},
                'MARGINAL': {'total': 0, 'wins': 0, 'win_rate': 0.0}
            }
        }

    def validate_trading_signal(self, symbol: str, signal: str, analysis_data: Dict[str, Any], 
                              market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validasi komprehensif sinyal trading untuk memastikan kualitas tinggi
        
        Returns:
        - is_valid: bool - Apakah sinyal layak di-trade
        - quality_score: float - Skor kualitas 0-1
        - quality_grade: str - Grade A+ hingga F
        - confidence_multiplier: float - Pengali confidence
        - position_size_multiplier: float - Pengali ukuran posisi
        - validation_reasons: List[str] - Alasan validasi
        - rejection_reasons: List[str] - Alasan penolakan
        """
        try:
            logger(f"🎯 SMART VALIDATOR: Analyzing {signal} signal for {symbol}")
            
            # Inisialisasi hasil validasi
            validation_result = {
                'is_valid': False,
                'quality_score': 0.0,
                'quality_grade': 'F',
                'confidence_multiplier': 0.0,
                'position_size_multiplier': 0.0,
                'validation_reasons': [],
                'rejection_reasons': [],
                'recommended_tp': None,
                'recommended_sl': None
            }
            
            # Komponen validasi
            validation_components = {}
            
            # 1. TECHNICAL CONFLUENCE VALIDATION
            technical_score = self._validate_technical_confluence(signal, analysis_data, market_data)
            validation_components['technical_confluence'] = technical_score
            
            # 2. MARKET STRUCTURE VALIDATION
            structure_score = self._validate_market_structure(signal, market_data, symbol)
            validation_components['market_structure'] = structure_score
            
            # 3. VOLUME CONFIRMATION VALIDATION
            volume_score = self._validate_volume_confirmation(signal, market_data)
            validation_components['volume_confirmation'] = volume_score
            
            # 4. MOMENTUM ALIGNMENT VALIDATION
            momentum_score = self._validate_momentum_alignment(signal, market_data)
            validation_components['momentum_alignment'] = momentum_score
            
            # 5. RISK/REWARD RATIO VALIDATION
            risk_reward_score = self._validate_risk_reward_ratio(signal, analysis_data, market_data)
            validation_components['risk_reward_ratio'] = risk_reward_score
            
            # 6. SESSION TIMING VALIDATION
            timing_score = self._validate_session_timing(symbol)
            validation_components['session_timing'] = timing_score
            
            # 7. SPREAD CONDITIONS VALIDATION
            spread_score = self._validate_spread_conditions(symbol, analysis_data)
            validation_components['spread_conditions'] = spread_score
            
            # Calculate weighted quality score
            quality_score = 0.0
            for component, score in validation_components.items():
                weight = self.validation_weights.get(component, 0)
                quality_score += score * weight
                
                if score >= 0.7:
                    validation_result['validation_reasons'].append(f"{component.replace('_', ' ').title()}: {score:.1%}")
                elif score < 0.4:
                    validation_result['rejection_reasons'].append(f"Poor {component.replace('_', ' ')}: {score:.1%}")
            
            # Apply volatility adjustments
            volatility_level = self._detect_market_volatility(market_data)
            volatility_adjustment = self.volatility_adjustments.get(volatility_level, {'threshold_reduction': 0, 'confidence_bonus': 0})
            
            adjusted_quality_score = quality_score + volatility_adjustment['confidence_bonus']
            adjusted_quality_score = max(0.0, min(1.0, adjusted_quality_score))  # Clamp between 0-1
            
            # Determine quality grade and validation status
            quality_grade = self._get_quality_grade(adjusted_quality_score)
            threshold_adjustment = volatility_adjustment['threshold_reduction']
            
            # Check if signal passes minimum quality threshold
            min_threshold = self.quality_thresholds['REJECT'] + threshold_adjustment
            is_valid = adjusted_quality_score >= min_threshold
            
            # Calculate multipliers based on quality
            if is_valid:
                confidence_multiplier = self._calculate_confidence_multiplier(quality_grade, adjusted_quality_score)
                position_size_multiplier = self._calculate_position_size_multiplier(quality_grade)
                
                # Generate optimal TP/SL based on quality
                tp_sl_recommendations = self._generate_tp_sl_recommendations(
                    signal, quality_grade, market_data, symbol
                )
                validation_result.update(tp_sl_recommendations)
            else:
                confidence_multiplier = 0.0
                position_size_multiplier = 0.0
                validation_result['rejection_reasons'].append(f"Quality score {adjusted_quality_score:.1%} below minimum {min_threshold:.1%}")
            
            # Update validation result
            validation_result.update({
                'is_valid': is_valid,
                'quality_score': adjusted_quality_score,
                'quality_grade': quality_grade,
                'confidence_multiplier': confidence_multiplier,
                'position_size_multiplier': position_size_multiplier,
                'volatility_level': volatility_level,
                'validation_components': validation_components
            })
            
            # Log validation summary
            if is_valid:
                logger(f"✅ VALIDATION PASSED: {quality_grade} grade signal ({adjusted_quality_score:.1%})")
                logger(f"   🎯 Confidence multiplier: {confidence_multiplier:.2f}x")
                logger(f"   📊 Position size multiplier: {position_size_multiplier:.2f}x")
                logger(f"   ✅ Reasons: {', '.join(validation_result['validation_reasons'])}")
            else:
                logger(f"❌ VALIDATION FAILED: {quality_grade} grade ({adjusted_quality_score:.1%})")
                logger(f"   ❌ Reasons: {', '.join(validation_result['rejection_reasons'])}")
            
            # Update performance tracking
            self.performance_history['total_validated'] += 1
            
            return validation_result
            
        except Exception as e:
            logger(f"❌ Smart validation error for {symbol}: {str(e)}")
            return {
                'is_valid': False,
                'quality_score': 0.0,
                'quality_grade': 'F',
                'confidence_multiplier': 0.0,
                'position_size_multiplier': 0.0,
                'validation_reasons': [],
                'rejection_reasons': [f"Validation error: {str(e)}"],
                'recommended_tp': None,
                'recommended_sl': None
            }

    def _validate_technical_confluence(self, signal: str, analysis_data: Dict[str, Any], 
                                     market_data: pd.DataFrame) -> float:
        """Validasi konfluensi indikator teknikal"""
        try:
            confluence_score = 0.0
            total_indicators = 0
            
            # Check various technical indicators alignment
            indicators_to_check = ['ema_signal', 'rsi_signal', 'macd_signal', 'bollinger_signal', 
                                 'stochastic_signal', 'atr_signal']
            
            for indicator in indicators_to_check:
                if indicator in analysis_data:
                    total_indicators += 1
                    indicator_signal = analysis_data[indicator]
                    
                    if indicator_signal == signal:
                        confluence_score += 1.0  # Full point for alignment
                    elif indicator_signal == 'NEUTRAL':
                        confluence_score += 0.5  # Half point for neutral
                    # 0 points for contradiction
            
            if total_indicators == 0:
                return 0.5  # Default moderate score if no indicators
                
            normalized_score = confluence_score / total_indicators
            
            # Bonus for high confluence
            if normalized_score >= 0.8:
                normalized_score += 0.1  # 10% bonus for strong confluence
                
            return min(1.0, normalized_score)
            
        except Exception:
            return 0.5  # Default moderate score on error

    def _validate_market_structure(self, signal: str, market_data: pd.DataFrame, symbol: str) -> float:
        """Validasi struktur pasar yang sehat"""
        try:
            if len(market_data) < 20:
                return 0.4  # Insufficient data
                
            structure_score = 0.0
            
            # 1. Trend consistency (40% weight)
            recent_closes = market_data['close'].tail(10).values
            if len(recent_closes) >= 10:
                trend_direction = 1 if recent_closes[-1] > recent_closes[0] else -1
                signal_direction = 1 if signal == 'BUY' else -1
                
                if trend_direction == signal_direction:
                    structure_score += 0.4  # Trend alignment
                else:
                    structure_score += 0.1  # Counter-trend (can work but riskier)
            
            # 2. Support/Resistance levels (30% weight)
            try:
                highs = market_data['high'].tail(20).values
                lows = market_data['low'].tail(20).values
                current_price = market_data['close'].iloc[-1]
                
                # Check if current price is near significant levels
                resistance_levels = np.percentile(highs, [90, 95])
                support_levels = np.percentile(lows, [5, 10])
                
                if signal == 'BUY' and any(abs(current_price - level) / current_price < 0.005 for level in support_levels):
                    structure_score += 0.3  # Buying near support
                elif signal == 'SELL' and any(abs(current_price - level) / current_price < 0.005 for level in resistance_levels):
                    structure_score += 0.3  # Selling near resistance
                else:
                    structure_score += 0.15  # Moderate structure
                    
            except Exception:
                structure_score += 0.15  # Default if calculation fails
            
            # 3. Price action quality (30% weight)
            try:
                last_candle = market_data.iloc[-1]
                prev_candle = market_data.iloc[-2]
                
                # Check for strong candle formation
                body_size = abs(last_candle['close'] - last_candle['open'])
                candle_range = last_candle['high'] - last_candle['low']
                
                if candle_range > 0:
                    body_ratio = body_size / candle_range
                    
                    if body_ratio >= 0.7:  # Strong body
                        candle_direction = 1 if last_candle['close'] > last_candle['open'] else -1
                        signal_direction = 1 if signal == 'BUY' else -1
                        
                        if candle_direction == signal_direction:
                            structure_score += 0.3  # Strong confirmation
                        else:
                            structure_score += 0.1  # Weak confirmation
                    else:
                        structure_score += 0.2  # Moderate candle
                else:
                    structure_score += 0.15  # Default
                    
            except Exception:
                structure_score += 0.15  # Default if calculation fails
                
            return min(1.0, structure_score)
            
        except Exception:
            return 0.5  # Default moderate score

    def _validate_volume_confirmation(self, signal: str, market_data: pd.DataFrame) -> float:
        """Validasi konfirmasi volume"""
        try:
            if 'volume' not in market_data.columns or len(market_data) < 10:
                return 0.6  # Default score if no volume data
                
            recent_volume = market_data['volume'].tail(5).mean()
            avg_volume = market_data['volume'].tail(20).mean()
            
            if avg_volume <= 0:
                return 0.6  # Default score
                
            volume_ratio = recent_volume / avg_volume
            
            # High volume confirmation is good
            if volume_ratio >= 1.5:
                return 0.9  # Strong volume confirmation
            elif volume_ratio >= 1.2:
                return 0.8  # Good volume confirmation
            elif volume_ratio >= 0.8:
                return 0.7  # Acceptable volume
            else:
                return 0.4  # Low volume - risky
                
        except Exception:
            return 0.6  # Default moderate score

    def _validate_momentum_alignment(self, signal: str, market_data: pd.DataFrame) -> float:
        """Validasi alignment momentum"""
        try:
            if len(market_data) < 14:
                return 0.5  # Insufficient data
                
            # Calculate simple momentum indicators
            closes = market_data['close'].values
            
            # 1. Price momentum (50% weight)
            short_momentum = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
            medium_momentum = (closes[-1] - closes[-10]) / closes[-10] if closes[-10] != 0 else 0
            
            momentum_score = 0.0
            
            if signal == 'BUY':
                if short_momentum > 0 and medium_momentum > 0:
                    momentum_score += 0.5  # Strong bullish momentum
                elif short_momentum > 0:
                    momentum_score += 0.3  # Short-term bullish
                elif medium_momentum > 0:
                    momentum_score += 0.2  # Medium-term bullish
                else:
                    momentum_score += 0.1  # Weak momentum
            else:  # SELL
                if short_momentum < 0 and medium_momentum < 0:
                    momentum_score += 0.5  # Strong bearish momentum
                elif short_momentum < 0:
                    momentum_score += 0.3  # Short-term bearish
                elif medium_momentum < 0:
                    momentum_score += 0.2  # Medium-term bearish
                else:
                    momentum_score += 0.1  # Weak momentum
            
            # 2. Acceleration (50% weight)
            if len(closes) >= 20:
                recent_acceleration = (closes[-1] - closes[-5]) - (closes[-5] - closes[-10])
                older_acceleration = (closes[-10] - closes[-15]) - (closes[-15] - closes[-20])
                
                if signal == 'BUY' and recent_acceleration > older_acceleration:
                    momentum_score += 0.5  # Accelerating upward
                elif signal == 'SELL' and recent_acceleration < older_acceleration:
                    momentum_score += 0.5  # Accelerating downward
                else:
                    momentum_score += 0.2  # Moderate acceleration
            else:
                momentum_score += 0.3  # Default for insufficient data
                
            return min(1.0, momentum_score)
            
        except Exception:
            return 0.5  # Default moderate score

    def _validate_risk_reward_ratio(self, signal: str, analysis_data: Dict[str, Any], 
                                  market_data: pd.DataFrame) -> float:
        """Validasi rasio risk/reward"""
        try:
            # Get TP and SL from analysis data
            tp_pips = analysis_data.get('tp_pips', 0)
            sl_pips = analysis_data.get('sl_pips', 0)
            
            if tp_pips <= 0 or sl_pips <= 0:
                return 0.4  # Poor risk management
                
            risk_reward_ratio = tp_pips / sl_pips
            
            # Evaluate based on risk/reward ratio
            if risk_reward_ratio >= 3.0:
                return 1.0  # Excellent 1:3 or better
            elif risk_reward_ratio >= 2.0:
                return 0.9  # Good 1:2 ratio
            elif risk_reward_ratio >= 1.5:
                return 0.7  # Acceptable 1:1.5 ratio
            elif risk_reward_ratio >= 1.0:
                return 0.5  # Minimum 1:1 ratio
            else:
                return 0.2  # Poor risk/reward
                
        except Exception:
            return 0.5  # Default moderate score

    def _validate_session_timing(self, symbol: str) -> float:
        """Validasi timing session trading"""
        try:
            current_utc_hour = datetime.utcnow().hour
            
            # Define optimal trading sessions for different symbols
            if any(s in symbol.upper() for s in ['EUR', 'GBP', 'CHF']):
                # European pairs - best during London and Overlap
                if 8 <= current_utc_hour <= 17:  # London
                    return 0.9
                elif 13 <= current_utc_hour <= 17:  # Overlap
                    return 1.0
                elif 0 <= current_utc_hour <= 9:  # Asian
                    return 0.4
                else:
                    return 0.6  # Off hours
                    
            elif any(s in symbol.upper() for s in ['USD', 'CAD']):
                # USD pairs - best during NY and Overlap
                if 13 <= current_utc_hour <= 22:  # NY
                    return 0.9
                elif 13 <= current_utc_hour <= 17:  # Overlap
                    return 1.0
                elif 8 <= current_utc_hour <= 17:  # London
                    return 0.7
                else:
                    return 0.5
                    
            elif any(s in symbol.upper() for s in ['JPY', 'AUD', 'NZD']):
                # Asian pairs - best during Asian session
                if 0 <= current_utc_hour <= 9:  # Asian
                    return 0.9
                elif 8 <= current_utc_hour <= 13:  # London start
                    return 0.7
                else:
                    return 0.5
                    
            elif any(s in symbol.upper() for s in ['XAU', 'GOLD', 'BTC']):
                # 24/7 markets - always good but best during overlaps
                if 13 <= current_utc_hour <= 17:  # Overlap
                    return 1.0
                elif 8 <= current_utc_hour <= 22:  # Major sessions
                    return 0.8
                else:
                    return 0.6  # Off hours
            else:
                return 0.7  # Default for unknown symbols
                
        except Exception:
            return 0.7  # Default moderate score

    def _validate_spread_conditions(self, symbol: str, analysis_data: Dict[str, Any]) -> float:
        """Validasi kondisi spread"""
        try:
            current_spread = analysis_data.get('current_spread', 0)
            typical_spread = analysis_data.get('typical_spread', current_spread * 1.5)
            
            if current_spread <= 0:
                return 0.7  # Default if no spread data
                
            spread_ratio = current_spread / typical_spread if typical_spread > 0 else 1.0
            
            # Evaluate spread conditions
            if spread_ratio <= 0.8:
                return 1.0  # Excellent - tight spread
            elif spread_ratio <= 1.0:
                return 0.9  # Good - normal spread
            elif spread_ratio <= 1.5:
                return 0.7  # Acceptable - slightly wide
            elif spread_ratio <= 2.0:
                return 0.5  # Poor - wide spread
            else:
                return 0.3  # Very poor - extremely wide spread
                
        except Exception:
            return 0.7  # Default moderate score

    def _detect_market_volatility(self, market_data: pd.DataFrame) -> str:
        """Deteksi level volatilitas pasar"""
        try:
            if len(market_data) < 20:
                return 'NORMAL'
                
            # Calculate ATR-based volatility
            highs = market_data['high'].tail(14).values
            lows = market_data['low'].tail(14).values
            closes = market_data['close'].tail(15).values[:-1]  # Previous closes
            
            true_ranges = []
            for i in range(len(highs)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i])
                tr3 = abs(lows[i] - closes[i])
                true_ranges.append(max(tr1, tr2, tr3))
                
            atr = np.mean(true_ranges)
            current_price = market_data['close'].iloc[-1]
            
            if current_price <= 0:
                return 'NORMAL'
                
            volatility_percentage = (atr / current_price) * 100
            
            if volatility_percentage >= 2.0:
                return 'EXTREME'
            elif volatility_percentage >= 1.0:
                return 'HIGH'
            elif volatility_percentage <= 0.3:
                return 'LOW'
            else:
                return 'NORMAL'
                
        except Exception:
            return 'NORMAL'

    def _get_quality_grade(self, quality_score: float) -> str:
        """Konversi skor kualitas ke grade"""
        if quality_score >= self.quality_thresholds['ULTRA_HIGH']:
            return 'A+'
        elif quality_score >= self.quality_thresholds['HIGH']:
            return 'A'
        elif quality_score >= self.quality_thresholds['GOOD']:
            return 'B+'
        elif quality_score >= self.quality_thresholds['ACCEPTABLE']:
            return 'B'
        elif quality_score >= self.quality_thresholds['MARGINAL']:
            return 'C'
        else:
            return 'F'

    def _calculate_confidence_multiplier(self, quality_grade: str, quality_score: float) -> float:
        """Hitung multiplier confidence berdasarkan kualitas"""
        base_multipliers = {
            'A+': 2.5,  # Ultra high confidence
            'A': 2.0,   # High confidence
            'B+': 1.6,  # Good confidence
            'B': 1.2,   # Normal confidence
            'C': 0.8,   # Low confidence
            'F': 0.0    # No confidence
        }
        
        base_multiplier = base_multipliers.get(quality_grade, 1.0)
        
        # Fine-tune based on exact score
        score_adjustment = (quality_score - 0.5) * 0.5  # -0.25 to +0.25
        final_multiplier = base_multiplier + score_adjustment
        
        return max(0.0, final_multiplier)

    def _calculate_position_size_multiplier(self, quality_grade: str) -> float:
        """Hitung multiplier ukuran posisi berdasarkan kualitas"""
        multipliers = {
            'A+': 2.5,  # Maximum position for best signals
            'A': 1.8,   # Large position for high quality
            'B+': 1.4,  # Medium-large position
            'B': 1.0,   # Normal position
            'C': 0.7,   # Small position for marginal signals
            'F': 0.0    # No position
        }
        
        return multipliers.get(quality_grade, 1.0)

    def _generate_tp_sl_recommendations(self, signal: str, quality_grade: str, 
                                      market_data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Generate TP/SL recommendations berdasarkan kualitas sinyal"""
        try:
            # Base TP/SL ratios based on quality
            tp_sl_ratios = {
                'A+': {'tp_ratio': 3.0, 'sl_ratio': 1.0},  # 1:3 risk/reward
                'A': {'tp_ratio': 2.5, 'sl_ratio': 1.0},   # 1:2.5 risk/reward
                'B+': {'tp_ratio': 2.0, 'sl_ratio': 1.0},  # 1:2 risk/reward
                'B': {'tp_ratio': 1.5, 'sl_ratio': 1.0},   # 1:1.5 risk/reward
                'C': {'tp_ratio': 1.0, 'sl_ratio': 1.0},   # 1:1 risk/reward (breakeven)
            }
            
            if quality_grade not in tp_sl_ratios:
                return {'recommended_tp': None, 'recommended_sl': None}
            
            ratios = tp_sl_ratios[quality_grade]
            
            # Calculate ATR for dynamic TP/SL
            if len(market_data) >= 14:
                highs = market_data['high'].tail(14).values
                lows = market_data['low'].tail(14).values
                closes = market_data['close'].tail(15).values[:-1]
                
                true_ranges = []
                for i in range(len(highs)):
                    tr1 = highs[i] - lows[i]
                    tr2 = abs(highs[i] - closes[i]) if i < len(closes) else highs[i] - lows[i]
                    tr3 = abs(lows[i] - closes[i]) if i < len(closes) else highs[i] - lows[i]
                    true_ranges.append(max(tr1, tr2, tr3))
                    
                atr = np.mean(true_ranges)
                current_price = market_data['close'].iloc[-1]
                
                # Convert ATR to pips (approximate)
                if any(s in symbol.upper() for s in ['JPY']):
                    pip_factor = 0.01  # JPY pairs
                else:
                    pip_factor = 0.0001  # Most other pairs
                    
                base_sl_pips = (atr / pip_factor) * 0.8  # 80% of ATR for SL
                
                recommended_sl = max(5, min(20, base_sl_pips))  # Clamp between 5-20 pips
                recommended_tp = recommended_sl * ratios['tp_ratio']
                
                return {
                    'recommended_tp': round(recommended_tp, 1),
                    'recommended_sl': round(recommended_sl, 1)
                }
            
            # Fallback static values
            base_tp_sl = {
                'XAUUSD': {'tp': 15, 'sl': 8},
                'EURUSD': {'tp': 12, 'sl': 6},
                'GBPUSD': {'tp': 15, 'sl': 8},
                'USDJPY': {'tp': 12, 'sl': 6},
                'BTCUSD': {'tp': 25, 'sl': 12}
            }
            
            symbol_key = next((k for k in base_tp_sl.keys() if k in symbol.upper()), 'EURUSD')
            base = base_tp_sl[symbol_key]
            
            return {
                'recommended_tp': base['tp'] * ratios['tp_ratio'],
                'recommended_sl': base['sl'] * ratios['sl_ratio']
            }
            
        except Exception:
            return {'recommended_tp': None, 'recommended_sl': None}

    def get_performance_summary(self) -> Dict[str, Any]:
        """Dapatkan ringkasan performa validasi"""
        total_validated = self.performance_history['total_validated']
        if total_validated == 0:
            return {'status': 'No trades validated yet'}
        
        return {
            'total_validated': total_validated,
            'overall_win_rate': self.performance_history['win_rate'],
            'quality_performance': self.performance_history['quality_performance'],
            'validation_efficiency': f"{(self.performance_history['successful_trades'] / total_validated * 100):.1f}%"
        }

    def update_trade_outcome(self, quality_grade: str, was_successful: bool):
        """Update outcome trade untuk adaptive learning"""
        try:
            if quality_grade in self.performance_history['quality_performance']:
                self.performance_history['quality_performance'][quality_grade]['total'] += 1
                
                if was_successful:
                    self.performance_history['quality_performance'][quality_grade]['wins'] += 1
                    self.performance_history['successful_trades'] += 1
                else:
                    self.performance_history['failed_trades'] += 1
                
                # Recalculate win rates
                perf = self.performance_history['quality_performance'][quality_grade]
                if perf['total'] > 0:
                    perf['win_rate'] = perf['wins'] / perf['total']
                
                total_trades = self.performance_history['successful_trades'] + self.performance_history['failed_trades']
                if total_trades > 0:
                    self.performance_history['win_rate'] = self.performance_history['successful_trades'] / total_trades
                    
        except Exception as e:
            logger(f"⚠️ Error updating trade outcome: {str(e)}")


# Global instance for easy access
smart_validator = SmartSignalValidator()


def validate_trading_signal(symbol: str, signal: str, analysis_data: Dict[str, Any], 
                          market_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Function wrapper untuk kemudahan akses
    
    Usage:
    validation = validate_trading_signal('EURUSD', 'BUY', analysis_data, df)
    if validation['is_valid']:
        # Execute trade dengan confidence dan position size multipliers
        execute_trade_with_validation(validation)
    """
    return smart_validator.validate_trading_signal(symbol, signal, analysis_data, market_data)


def update_trade_outcome(quality_grade: str, was_successful: bool):
    """Update outcome untuk adaptive learning"""
    smart_validator.update_trade_outcome(quality_grade, was_successful)


def get_validation_performance() -> Dict[str, Any]:
    """Dapatkan ringkasan performa validasi"""
    return smart_validator.get_performance_summary()


if __name__ == "__main__":
    # Test validasi
    print("🧪 Smart Signal Validator - Testing Mode")
    
    # Sample data untuk testing
    sample_data = {
        'symbol': 'EURUSD',
        'signal': 'BUY',
        'confidence': 0.75,
        'tp_pips': 15,
        'sl_pips': 8,
        'ema_signal': 'BUY',
        'rsi_signal': 'BUY',
        'macd_signal': 'NEUTRAL',
        'current_spread': 1.2,
        'typical_spread': 1.5
    }
    
    # Create sample market data
    dates = pd.date_range('2024-01-01', periods=50, freq='H')
    market_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(50).cumsum() + 1.1000,
        'high': np.random.randn(50).cumsum() + 1.1020,
        'low': np.random.randn(50).cumsum() + 1.0980,
        'close': np.random.randn(50).cumsum() + 1.1010,
        'volume': np.random.randint(100, 1000, 50)
    })
    
    # Test validation
    result = validate_trading_signal('EURUSD', 'BUY', sample_data, market_data)
    print(f"\n✅ Validation Result:")
    print(f"   Valid: {result['is_valid']}")
    print(f"   Quality Grade: {result['quality_grade']}")
    print(f"   Quality Score: {result['quality_score']:.1%}")
    print(f"   Confidence Multiplier: {result['confidence_multiplier']:.2f}x")
    print(f"   Position Size Multiplier: {result['position_size_multiplier']:.2f}x")
    print(f"   Recommended TP: {result.get('recommended_tp', 'N/A')}")
    print(f"   Recommended SL: {result.get('recommended_sl', 'N/A')}")