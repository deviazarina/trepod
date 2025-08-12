#!/usr/bin/env python3
"""
Aggressive Quality Filter - Filter agresif untuk trading berkualitas tinggi
Mencegah trades ngawur sambil mempertahankan frekuensi trading tinggi

Author: MT5 Advanced Trading Bot
Version: 4.0 - Aggressive Quality Control
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from logger_utils import logger

class AggressiveQualityFilter:
    """Filter agresif yang memblokir trades ngawur tapi mempertahankan frekuensi tinggi"""
    
    def __init__(self):
        # Konfigurasi filtering yang agresif tapi pintar
        self.quality_gates = {
            'minimum_confluence': 0.6,        # 60% confluence minimum
            'spread_tolerance': 3.0,          # Max 3x normal spread
            'volatility_check': True,         # Cek volatility extreme
            'momentum_alignment': 0.5,        # 50% momentum alignment
            'session_suitability': 0.4,       # 40% session score minimum
            'technical_strength': 0.5,        # 50% technical strength
            'risk_reward_minimum': 1.0        # Minimum 1:1 risk/reward
        }
        
        # Threshold berdasarkan kualitas sinyal
        self.confidence_thresholds = {
            'ULTRA_HIGH_QUALITY': 0.15,      # 15% - Trade premium dengan semua filter pass
            'HIGH_QUALITY': 0.20,            # 20% - Trade berkualitas dengan >80% filter pass  
            'GOOD_QUALITY': 0.25,            # 25% - Trade bagus dengan >60% filter pass
            'ACCEPTABLE_QUALITY': 0.35,      # 35% - Trade diterima dengan >40% filter pass
            'LOW_QUALITY': 0.50,             # 50% - Trade marginal dengan filter minimal
            'REJECT': 1.00                   # 100% - Tolak total
        }
        
        # Session multipliers untuk trading yang tepat waktu
        self.session_multipliers = {
            'LONDON_NY_OVERLAP': 2.0,        # 2x frekuensi saat overlap
            'LONDON': 1.5,                   # 1.5x saat London
            'NEW_YORK': 1.3,                 # 1.3x saat NY
            'ASIAN_ACTIVE': 1.0,             # Normal saat Asian aktif
            'OFF_HOURS': 0.6                 # 60% saat off-hours
        }
        
        # Symbol-specific parameters
        self.symbol_configs = {
            'EURUSD': {'max_spread': 2.0, 'min_volatility': 0.0002, 'base_confidence': 0.25},
            'GBPUSD': {'max_spread': 3.0, 'min_volatility': 0.0003, 'base_confidence': 0.30},
            'USDJPY': {'max_spread': 2.5, 'min_volatility': 0.02, 'base_confidence': 0.25},
            'XAUUSD': {'max_spread': 5.0, 'min_volatility': 0.10, 'base_confidence': 0.20},  # Ultra-aggressive
            'BTCUSD': {'max_spread': 10.0, 'min_volatility': 5.0, 'base_confidence': 0.20}   # Ultra-aggressive
        }
        
        # Performance tracking untuk adaptive learning
        self.filter_stats = {
            'total_signals': 0,
            'approved_signals': 0,
            'rejected_signals': 0,
            'quality_distribution': {
                'ULTRA_HIGH': 0, 'HIGH': 0, 'GOOD': 0, 
                'ACCEPTABLE': 0, 'LOW': 0, 'REJECTED': 0
            },
            'approval_rate': 0.0,
            'successful_predictions': 0,
            'failed_predictions': 0
        }

    def filter_trading_signal(self, symbol: str, signal: str, confidence: float, 
                            analysis_data: Dict[str, Any], market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Filter comprehensive untuk trading signal
        
        Returns:
        - should_trade: bool - Apakah boleh trade
        - quality_level: str - Level kualitas sinyal
        - adjusted_confidence: float - Confidence yang disesuaikan
        - position_multiplier: float - Pengali ukuran posisi
        - filter_reasons: List[str] - Alasan approve/reject
        - recommended_params: Dict - Parameter trading yang disarankan
        """
        try:
            self.filter_stats['total_signals'] += 1
            
            logger(f"🎯 AGGRESSIVE FILTER: Analyzing {signal} signal for {symbol}")
            logger(f"   📊 Base confidence: {confidence:.1%}")
            
            # Initialize filter result
            filter_result = {
                'should_trade': False,
                'quality_level': 'REJECT',
                'adjusted_confidence': confidence,
                'position_multiplier': 0.0,
                'filter_reasons': [],
                'recommended_params': {},
                'filter_score': 0.0
            }
            
            # Run all quality checks
            quality_checks = self._run_quality_checks(symbol, signal, confidence, analysis_data, market_data)
            
            # Calculate overall quality score
            quality_score = self._calculate_quality_score(quality_checks)
            filter_result['filter_score'] = quality_score
            
            # Determine quality level
            quality_level = self._determine_quality_level(quality_score, quality_checks)
            filter_result['quality_level'] = quality_level
            
            # Get symbol-specific configuration
            symbol_config = self._get_symbol_config(symbol)
            base_threshold = symbol_config['base_confidence']
            
            # Apply session-based adjustments
            session_info = self._get_session_info()
            session_multiplier = session_info['multiplier']
            adjusted_threshold = base_threshold / session_multiplier  # Lower threshold = more aggressive
            
            # Apply quality-based confidence threshold
            quality_threshold = self.confidence_thresholds.get(quality_level, 1.0)
            final_threshold = min(adjusted_threshold, quality_threshold)
            
            # Decision logic
            if quality_level == 'REJECT':
                filter_result['should_trade'] = False
                filter_result['filter_reasons'].append("Quality checks failed")
                self.filter_stats['rejected_signals'] += 1
            
            elif confidence >= final_threshold and quality_score >= 0.4:
                filter_result['should_trade'] = True
                filter_result['position_multiplier'] = self._calculate_position_multiplier(quality_level, quality_score, session_multiplier)
                filter_result['adjusted_confidence'] = min(0.95, confidence * (1 + quality_score * 0.3))
                filter_result['recommended_params'] = self._generate_trading_params(quality_level, symbol, analysis_data)
                
                filter_result['filter_reasons'].extend([
                    f"Quality level: {quality_level}",
                    f"Quality score: {quality_score:.1%}",
                    f"Session: {session_info['session']} ({session_multiplier:.1f}x)",
                    f"Threshold: {final_threshold:.1%} vs Confidence: {confidence:.1%}"
                ])
                
                self.filter_stats['approved_signals'] += 1
                self.filter_stats['quality_distribution'][quality_level.split('_')[0]] += 1
                
                logger(f"✅ FILTER APPROVED: {quality_level} quality ({quality_score:.1%})")
                logger(f"   📈 Position multiplier: {filter_result['position_multiplier']:.2f}x")
                logger(f"   🎯 Adjusted confidence: {filter_result['adjusted_confidence']:.1%}")
                
            else:
                filter_result['should_trade'] = False
                filter_result['filter_reasons'].extend([
                    f"Confidence {confidence:.1%} below threshold {final_threshold:.1%}",
                    f"Quality score {quality_score:.1%} insufficient"
                ])
                self.filter_stats['rejected_signals'] += 1
                
                logger(f"❌ FILTER REJECTED: Low confidence/quality")
                logger(f"   📊 Confidence: {confidence:.1%} < {final_threshold:.1%}")
                logger(f"   📉 Quality: {quality_score:.1%}")
            
            # Update approval rate
            total = self.filter_stats['approved_signals'] + self.filter_stats['rejected_signals']
            if total > 0:
                self.filter_stats['approval_rate'] = self.filter_stats['approved_signals'] / total
            
            return filter_result
            
        except Exception as e:
            logger(f"❌ Aggressive filter error for {symbol}: {str(e)}")
            return {
                'should_trade': False,
                'quality_level': 'ERROR',
                'adjusted_confidence': 0.0,
                'position_multiplier': 0.0,
                'filter_reasons': [f"Filter error: {str(e)}"],
                'recommended_params': {},
                'filter_score': 0.0
            }

    def _run_quality_checks(self, symbol: str, signal: str, confidence: float,
                          analysis_data: Dict[str, Any], market_data: pd.DataFrame) -> Dict[str, float]:
        """Jalankan semua quality checks"""
        checks = {}
        
        try:
            # 1. Technical Confluence Check
            checks['technical_confluence'] = self._check_technical_confluence(analysis_data)
            
            # 2. Spread Quality Check
            checks['spread_quality'] = self._check_spread_quality(symbol, analysis_data)
            
            # 3. Market Structure Check
            checks['market_structure'] = self._check_market_structure(signal, market_data)
            
            # 4. Volume Confirmation Check
            checks['volume_confirmation'] = self._check_volume_confirmation(market_data)
            
            # 5. Momentum Alignment Check
            checks['momentum_alignment'] = self._check_momentum_alignment(signal, market_data)
            
            # 6. Session Suitability Check
            checks['session_suitability'] = self._check_session_suitability(symbol)
            
            # 7. Volatility Health Check
            checks['volatility_health'] = self._check_volatility_health(symbol, market_data)
            
            # 8. Risk/Reward Check
            checks['risk_reward'] = self._check_risk_reward(analysis_data)
            
        except Exception as e:
            logger(f"⚠️ Quality checks error: {str(e)}")
            # Return default moderate scores on error
            checks = {check: 0.5 for check in ['technical_confluence', 'spread_quality', 'market_structure',
                     'volume_confirmation', 'momentum_alignment', 'session_suitability', 
                     'volatility_health', 'risk_reward']}
        
        return checks

    def _check_technical_confluence(self, analysis_data: Dict[str, Any]) -> float:
        """Check konfluensi indikator teknikal"""
        try:
            technical_signals = ['ema_signal', 'rsi_signal', 'macd_signal', 'bollinger_signal', 'stochastic_signal']
            
            total_signals = 0
            agreeing_signals = 0
            
            base_signal = analysis_data.get('signal', 'NEUTRAL')
            
            for indicator in technical_signals:
                if indicator in analysis_data:
                    total_signals += 1
                    if analysis_data[indicator] == base_signal:
                        agreeing_signals += 1
            
            if total_signals == 0:
                return 0.5  # Default moderate score
            
            confluence_ratio = agreeing_signals / total_signals
            
            # Bonus for high confluence
            if confluence_ratio >= 0.8:
                return min(1.0, confluence_ratio + 0.15)
            
            return confluence_ratio
            
        except Exception:
            return 0.5

    def _check_spread_quality(self, symbol: str, analysis_data: Dict[str, Any]) -> float:
        """Check kualitas spread"""
        try:
            current_spread = analysis_data.get('current_spread', 2.0)
            symbol_config = self._get_symbol_config(symbol)
            max_spread = symbol_config['max_spread']
            
            if current_spread <= max_spread * 0.5:
                return 1.0  # Excellent spread
            elif current_spread <= max_spread:
                return 0.8  # Good spread
            elif current_spread <= max_spread * 1.5:
                return 0.5  # Acceptable spread
            elif current_spread <= max_spread * 2.0:
                return 0.3  # Poor spread
            else:
                return 0.1  # Very poor spread
                
        except Exception:
            return 0.7

    def _check_market_structure(self, signal: str, market_data: pd.DataFrame) -> float:
        """Check struktur pasar"""
        try:
            if len(market_data) < 10:
                return 0.4
            
            closes = market_data['close'].tail(10).values
            highs = market_data['high'].tail(20).values
            lows = market_data['low'].tail(20).values
            
            # Trend strength
            trend_score = 0.0
            if len(closes) >= 5:
                recent_trend = closes[-1] - closes[-5]
                signal_direction = 1 if signal == 'BUY' else -1
                trend_direction = 1 if recent_trend > 0 else -1
                
                if trend_direction == signal_direction:
                    trend_score = 0.6
                else:
                    trend_score = 0.3  # Counter-trend can work
            
            # Support/Resistance levels
            structure_score = 0.0
            current_price = closes[-1]
            
            resistance_level = np.percentile(highs, 95)
            support_level = np.percentile(lows, 5)
            
            if signal == 'BUY':
                distance_to_support = abs(current_price - support_level) / current_price
                if distance_to_support < 0.002:  # Near support
                    structure_score = 0.4
                else:
                    structure_score = 0.2
            else:  # SELL
                distance_to_resistance = abs(current_price - resistance_level) / current_price  
                if distance_to_resistance < 0.002:  # Near resistance
                    structure_score = 0.4
                else:
                    structure_score = 0.2
            
            return min(1.0, trend_score + structure_score)
            
        except Exception:
            return 0.5

    def _check_volume_confirmation(self, market_data: pd.DataFrame) -> float:
        """Check konfirmasi volume"""
        try:
            if 'volume' not in market_data.columns or len(market_data) < 10:
                return 0.6  # Default moderate score
            
            recent_volume = market_data['volume'].tail(3).mean()
            avg_volume = market_data['volume'].tail(20).mean()
            
            if avg_volume <= 0:
                return 0.6
            
            volume_ratio = recent_volume / avg_volume
            
            if volume_ratio >= 1.5:
                return 1.0  # Strong volume confirmation
            elif volume_ratio >= 1.2:
                return 0.8  # Good volume
            elif volume_ratio >= 0.8:
                return 0.6  # Acceptable volume
            else:
                return 0.3  # Low volume
                
        except Exception:
            return 0.6

    def _check_momentum_alignment(self, signal: str, market_data: pd.DataFrame) -> float:
        """Check alignment momentum"""
        try:
            if len(market_data) < 10:
                return 0.5
            
            closes = market_data['close'].values
            
            # Short-term momentum (5 bars)
            short_momentum = (closes[-1] - closes[-5]) / closes[-5] if closes[-5] != 0 else 0
            
            # Medium-term momentum (10 bars)
            medium_momentum = (closes[-1] - closes[-10]) / closes[-10] if len(closes) >= 10 and closes[-10] != 0 else 0
            
            signal_direction = 1 if signal == 'BUY' else -1
            
            momentum_score = 0.0
            
            # Check short-term alignment
            if (short_momentum > 0 and signal_direction > 0) or (short_momentum < 0 and signal_direction < 0):
                momentum_score += 0.5
            
            # Check medium-term alignment
            if (medium_momentum > 0 and signal_direction > 0) or (medium_momentum < 0 and signal_direction < 0):
                momentum_score += 0.5
            
            return momentum_score
            
        except Exception:
            return 0.5

    def _check_session_suitability(self, symbol: str) -> float:
        """Check kesesuaian session trading"""
        try:
            current_utc_hour = datetime.utcnow().hour
            
            # Define optimal sessions for different symbol types
            if any(s in symbol.upper() for s in ['EUR', 'GBP']):
                if 8 <= current_utc_hour <= 17:  # London
                    return 0.9
                elif 13 <= current_utc_hour <= 17:  # Overlap
                    return 1.0
                else:
                    return 0.4
                    
            elif any(s in symbol.upper() for s in ['USD', 'CAD']):
                if 13 <= current_utc_hour <= 22:  # NY
                    return 0.9
                elif 13 <= current_utc_hour <= 17:  # Overlap
                    return 1.0
                else:
                    return 0.5
                    
            elif any(s in symbol.upper() for s in ['XAU', 'BTC']):
                # 24/7 markets
                if 13 <= current_utc_hour <= 17:  # Overlap
                    return 1.0
                elif 8 <= current_utc_hour <= 22:  # Major sessions
                    return 0.8
                else:
                    return 0.6
            else:
                return 0.7
                
        except Exception:
            return 0.7

    def _check_volatility_health(self, symbol: str, market_data: pd.DataFrame) -> float:
        """Check kesehatan volatilitas"""
        try:
            if len(market_data) < 14:
                return 0.5
            
            # Calculate simple volatility
            closes = market_data['close'].tail(14).values
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes)) if closes[i-1] != 0]
            
            if not returns:
                return 0.5
            
            volatility = np.std(returns)
            symbol_config = self._get_symbol_config(symbol)
            min_volatility = symbol_config['min_volatility']
            
            # Check volatility is in healthy range
            if volatility >= min_volatility * 0.5 and volatility <= min_volatility * 3.0:
                return 0.9  # Healthy volatility
            elif volatility >= min_volatility * 0.3:
                return 0.7  # Acceptable volatility
            elif volatility >= min_volatility * 0.1:
                return 0.5  # Low volatility
            else:
                return 0.3  # Very low volatility
                
        except Exception:
            return 0.5

    def _check_risk_reward(self, analysis_data: Dict[str, Any]) -> float:
        """Check rasio risk/reward"""
        try:
            tp_pips = analysis_data.get('tp_pips', 0)
            sl_pips = analysis_data.get('sl_pips', 0)
            
            if tp_pips <= 0 or sl_pips <= 0:
                return 0.5  # Default if no TP/SL data
            
            risk_reward_ratio = tp_pips / sl_pips
            
            if risk_reward_ratio >= 2.0:
                return 1.0  # Excellent R:R
            elif risk_reward_ratio >= 1.5:
                return 0.8  # Good R:R
            elif risk_reward_ratio >= 1.0:
                return 0.6  # Acceptable R:R
            else:
                return 0.3  # Poor R:R
                
        except Exception:
            return 0.5

    def _calculate_quality_score(self, quality_checks: Dict[str, float]) -> float:
        """Calculate overall quality score"""
        try:
            # Weighted quality calculation
            weights = {
                'technical_confluence': 0.20,
                'market_structure': 0.18,
                'momentum_alignment': 0.15,
                'volume_confirmation': 0.12,
                'spread_quality': 0.10,
                'session_suitability': 0.10,
                'volatility_health': 0.08,
                'risk_reward': 0.07
            }
            
            total_score = 0.0
            total_weight = 0.0
            
            for check, score in quality_checks.items():
                weight = weights.get(check, 0.05)
                total_score += score * weight
                total_weight += weight
            
            if total_weight == 0:
                return 0.5
            
            normalized_score = total_score / total_weight
            
            # Bonus for exceptional quality
            passed_checks = sum(1 for score in quality_checks.values() if score >= 0.7)
            total_checks = len(quality_checks)
            
            if total_checks > 0:
                pass_rate = passed_checks / total_checks
                if pass_rate >= 0.8:
                    normalized_score = min(1.0, normalized_score + 0.1)  # 10% bonus
            
            return min(1.0, max(0.0, normalized_score))
            
        except Exception:
            return 0.5

    def _determine_quality_level(self, quality_score: float, quality_checks: Dict[str, float]) -> str:
        """Tentukan level kualitas sinyal"""
        try:
            # Count high-quality checks
            high_quality_checks = sum(1 for score in quality_checks.values() if score >= 0.8)
            total_checks = len(quality_checks)
            
            if quality_score >= 0.85 and high_quality_checks >= total_checks * 0.8:
                return 'ULTRA_HIGH_QUALITY'
            elif quality_score >= 0.75 and high_quality_checks >= total_checks * 0.6:
                return 'HIGH_QUALITY'
            elif quality_score >= 0.65 and high_quality_checks >= total_checks * 0.4:
                return 'GOOD_QUALITY'
            elif quality_score >= 0.50:
                return 'ACCEPTABLE_QUALITY'
            elif quality_score >= 0.35:
                return 'LOW_QUALITY'
            else:
                return 'REJECT'
                
        except Exception:
            return 'LOW_QUALITY'

    def _get_symbol_config(self, symbol: str) -> Dict[str, float]:
        """Dapatkan konfigurasi symbol"""
        for key, config in self.symbol_configs.items():
            if key in symbol.upper():
                return config
        
        # Default config
        return {'max_spread': 3.0, 'min_volatility': 0.001, 'base_confidence': 0.30}

    def _get_session_info(self) -> Dict[str, Any]:
        """Dapatkan info session saat ini"""
        try:
            current_utc_hour = datetime.utcnow().hour
            
            if 13 <= current_utc_hour <= 17:
                return {'session': 'LONDON_NY_OVERLAP', 'multiplier': 2.0}
            elif 8 <= current_utc_hour <= 17:
                return {'session': 'LONDON', 'multiplier': 1.5}
            elif 13 <= current_utc_hour <= 22:
                return {'session': 'NEW_YORK', 'multiplier': 1.3}
            elif 0 <= current_utc_hour <= 9:
                return {'session': 'ASIAN_ACTIVE', 'multiplier': 1.0}
            else:
                return {'session': 'OFF_HOURS', 'multiplier': 0.6}
                
        except Exception:
            return {'session': 'UNKNOWN', 'multiplier': 1.0}

    def _calculate_position_multiplier(self, quality_level: str, quality_score: float, session_multiplier: float) -> float:
        """Calculate position size multiplier"""
        try:
            base_multipliers = {
                'ULTRA_HIGH_QUALITY': 2.5,
                'HIGH_QUALITY': 2.0,
                'GOOD_QUALITY': 1.6,
                'ACCEPTABLE_QUALITY': 1.2,
                'LOW_QUALITY': 0.8,
                'REJECT': 0.0
            }
            
            base_multiplier = base_multipliers.get(quality_level, 1.0)
            
            # Apply quality score fine-tuning
            score_adjustment = (quality_score - 0.5) * 0.4  # -0.2 to +0.2
            
            # Apply session multiplier (capped)
            final_multiplier = (base_multiplier + score_adjustment) * min(1.5, session_multiplier)
            
            return max(0.0, min(3.0, final_multiplier))  # Cap between 0-3x
            
        except Exception:
            return 1.0

    def _generate_trading_params(self, quality_level: str, symbol: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate parameter trading yang disarankan"""
        try:
            # Base parameters by quality
            quality_params = {
                'ULTRA_HIGH_QUALITY': {'tp_multiplier': 2.5, 'sl_multiplier': 0.8, 'trailing_stop': True},
                'HIGH_QUALITY': {'tp_multiplier': 2.0, 'sl_multiplier': 0.9, 'trailing_stop': True},
                'GOOD_QUALITY': {'tp_multiplier': 1.8, 'sl_multiplier': 1.0, 'trailing_stop': True},
                'ACCEPTABLE_QUALITY': {'tp_multiplier': 1.5, 'sl_multiplier': 1.0, 'trailing_stop': False},
                'LOW_QUALITY': {'tp_multiplier': 1.2, 'sl_multiplier': 1.1, 'trailing_stop': False}
            }
            
            params = quality_params.get(quality_level, {'tp_multiplier': 1.0, 'sl_multiplier': 1.0, 'trailing_stop': False})
            
            # Get base TP/SL from analysis
            base_tp = analysis_data.get('tp_pips', 15)
            base_sl = analysis_data.get('sl_pips', 8)
            
            # Apply multipliers
            recommended_params = {
                'tp_pips': round(base_tp * params['tp_multiplier'], 1),
                'sl_pips': round(base_sl * params['sl_multiplier'], 1),
                'trailing_stop': params['trailing_stop'],
                'break_even': quality_level in ['ULTRA_HIGH_QUALITY', 'HIGH_QUALITY'],
                'partial_close': quality_level == 'ULTRA_HIGH_QUALITY'
            }
            
            # Ensure minimum risk/reward ratio
            if recommended_params['sl_pips'] > 0:
                min_tp = recommended_params['sl_pips'] * 1.0  # At least 1:1
                recommended_params['tp_pips'] = max(recommended_params['tp_pips'], min_tp)
            
            return recommended_params
            
        except Exception:
            return {'tp_pips': 15, 'sl_pips': 8, 'trailing_stop': False}

    def get_filter_statistics(self) -> Dict[str, Any]:
        """Dapatkan statistik filter"""
        return {
            'total_signals_processed': self.filter_stats['total_signals'],
            'approval_rate': f"{self.filter_stats['approval_rate']:.1%}",
            'approved_signals': self.filter_stats['approved_signals'],
            'rejected_signals': self.filter_stats['rejected_signals'],
            'quality_distribution': self.filter_stats['quality_distribution'],
            'filter_efficiency': 'HIGH' if self.filter_stats['approval_rate'] > 0.3 else 'MEDIUM'
        }

    def reset_statistics(self):
        """Reset statistik filter"""
        self.filter_stats = {
            'total_signals': 0,
            'approved_signals': 0,
            'rejected_signals': 0,
            'quality_distribution': {
                'ULTRA_HIGH': 0, 'HIGH': 0, 'GOOD': 0,
                'ACCEPTABLE': 0, 'LOW': 0, 'REJECTED': 0
            },
            'approval_rate': 0.0,
            'successful_predictions': 0,
            'failed_predictions': 0
        }


# Global instance
aggressive_filter = AggressiveQualityFilter()


def filter_trading_signal(symbol: str, signal: str, confidence: float,
                         analysis_data: Dict[str, Any], market_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Wrapper function untuk kemudahan akses
    
    Usage:
    result = filter_trading_signal('EURUSD', 'BUY', 0.65, analysis_data, df)
    if result['should_trade']:
        execute_with_params(result['recommended_params'], result['position_multiplier'])
    """
    return aggressive_filter.filter_trading_signal(symbol, signal, confidence, analysis_data, market_data)


def get_filter_stats() -> Dict[str, Any]:
    """Dapatkan statistik filter"""
    return aggressive_filter.get_filter_statistics()


if __name__ == "__main__":
    # Test filter
    print("🧪 Aggressive Quality Filter - Testing Mode")
    
    sample_analysis = {
        'signal': 'BUY',
        'tp_pips': 15,
        'sl_pips': 8,
        'current_spread': 1.8,
        'ema_signal': 'BUY',
        'rsi_signal': 'BUY',
        'macd_signal': 'NEUTRAL'
    }
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=50, freq='H')
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.randn(50).cumsum() + 1.1000,
        'high': np.random.randn(50).cumsum() + 1.1020,
        'low': np.random.randn(50).cumsum() + 1.0980,
        'close': np.random.randn(50).cumsum() + 1.1010,
        'volume': np.random.randint(100, 1000, 50)
    })
    
    result = filter_trading_signal('EURUSD', 'BUY', 0.65, sample_analysis, sample_data)
    print(f"\n📊 Filter Result:")
    print(f"   Should Trade: {result['should_trade']}")
    print(f"   Quality Level: {result['quality_level']}")
    print(f"   Quality Score: {result['filter_score']:.1%}")
    print(f"   Position Multiplier: {result['position_multiplier']:.2f}x")
    print(f"   Recommended TP: {result['recommended_params'].get('tp_pips', 'N/A')}")
    print(f"   Recommended SL: {result['recommended_params'].get('sl_pips', 'N/A')}")