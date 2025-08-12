
# ULTRA-AGGRESSIVE SCALPING CONFIGURATION
# Focus: XAUUSD/BTCUSD unlimited trading

ULTRA_SCALPING_CONFIG = {
    'enabled': True,
    'symbols': ['XAUUSDm', 'XAUUSDc', 'BTCUSDm', 'BTCUSDc'],
    'unlimited_trading': True,
    'max_daily_trades': 9999999,
    'max_concurrent_positions': 9999999,
    'ultra_aggressive_mode': True,
    'scalping_parameters': {
        'XAUUSD': {
            'min_tp_pips': 8,
            'max_tp_pips': 15,
            'min_sl_pips': 4,
            'max_sl_pips': 8,
            'lot_multiplier': 1.5,
            'confidence_threshold': 0.35
        },
        'BTCUSD': {
            'min_tp_pips': 15,
            'max_tp_pips': 30,
            'min_sl_pips': 8,
            'max_sl_pips': 15,
            'lot_multiplier': 1.8,
            'confidence_threshold': 0.40
        }
    }
}
