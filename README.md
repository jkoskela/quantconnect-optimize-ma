# quantconnect-optimize-ma
Naive Moving Average Optimization using QuantConnect

This attempts to find a general purpose moving average that could be used for confirmation of other strategies when live trading. I also added an ATR short strategy that doesn't really fit with the others.

It optimizes across:
 - Indicator Type (sma, ema, vwap)
 - Period Length

It uses two different algorithms. This must be selected before optimization, because QuantConnect only allows optimization of two parameters at a time.

## Crossover/Continuation
Enter when the price crosses over the indicator.

Exit
 - If reverses across the indicator
 - At take profit
 
## Reversal
This could be improved with a separate stop loss.

Enter when price is near or crosses over the indicator.

Exit
 - If an opposite signal is generated.
 - At take profit
