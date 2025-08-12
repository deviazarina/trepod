
#!/usr/bin/env python3
"""
XAU/USD Scalping Setup Script
Untuk mengoptimalkan bot khusus scalping XAUUSDm dan XAUUSDc
"""

from xauusd_scalping_optimizer import get_xauusd_scalping_signal, validate_xauusd_scalping_conditions
from logger_utils import logger
import datetime

class XAUUSDScalpingSetup:
    """Setup khusus untuk XAU/USD scalping"""
    
    def __init__(self):
        self.symbols = ["XAUUSDm", "XAUUSDc"]
        self.optimal_settings = {
            'strategy': 'Scalping',
            'confidence_threshold': 0.65,  # 65% minimum
            'max_spread_usd': 5.0,
            'session_filter': True,
            'position_multiplier_max': 3.0
        }
    
    def check_optimal_conditions(self):
        """Check apakah kondisi optimal untuk XAU/USD scalping"""
        logger("🥇 XAU/USD SCALPING CONDITIONS CHECK")
        
        current_hour = datetime.datetime.utcnow().hour
        
        # Check session
        if 8 <= current_hour <= 21:  # London + NY sessions
            session_status = "✅ OPTIMAL SESSION"
        else:
            session_status = "⚠️ SUBOPTIMAL SESSION"
        
        logger(f"   🕐 Current UTC Hour: {current_hour}")
        logger(f"   📊 Session Status: {session_status}")
        
        # Check each symbol
        for symbol in self.symbols:
            validation = validate_xauusd_scalping_conditions(symbol)
            
            if validation['valid']:
                logger(f"   ✅ {symbol}: READY FOR SCALPING")
                logger(f"      📊 Spread: {validation.get('spread_usd', 0):.1f} USD")
                logger(f"      🎯 Session: {validation.get('optimal_session', False)}")
            else:
                logger(f"   ⚠️ {symbol}: {validation.get('reason', 'Not optimal')}")
    
    def get_live_signals(self):
        """Get live XAU/USD scalping signals"""
        logger("🔍 GETTING LIVE XAU/USD SCALPING SIGNALS")
        
        for symbol in self.symbols:
            signal_data = get_xauusd_scalping_signal(symbol)
            
            if signal_data.get('signal'):
                confidence = signal_data.get('confidence', 0)
                tp_pips = signal_data.get('tp_pips', 15)
                sl_pips = signal_data.get('sl_pips', 8)
                
                logger(f"🥇 {symbol} SIGNAL: {signal_data['signal']}")
                logger(f"   📊 Confidence: {confidence:.1%}")
                logger(f"   🎯 TP: {tp_pips} pips | SL: {sl_pips} pips")
                logger(f"   📈 Position Multiplier: {signal_data.get('position_size_multiplier', 1.0):.1f}x")
                
                # Show reasons
                reasons = signal_data.get('reasons', [])
                for reason in reasons[:3]:  # Top 3 reasons
                    logger(f"   ✅ {reason}")
            else:
                logger(f"⚪ {symbol}: {signal_data.get('reason', 'No signal')}")

# Usage example
if __name__ == "__main__":
    setup = XAUUSDScalpingSetup()
    setup.check_optimal_conditions()
    setup.get_live_signals()
