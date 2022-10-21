# quantconnect-optimize-ma
Native Moving Average Optimization using QuantConnect

This attempts to find a general purpose moving average that could be used for confirmation of other strategies. I later added an ATR short strategy that doesn't really fit with the others.

It optimizes across:
 - Indicator Type (sma, ema, vwap, atr)
 - Period Length
