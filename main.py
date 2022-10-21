from AlgorithmImports import *
import decimal as d
from datetime import timedelta

class OptimalMovingAverage(QCAlgorithm):
    
    def Initialize(self):

        # 1 = continuation
        # 2 = reversal
        self.algo = 1

        self.SetStartDate(2022, 1, 1)    #Set Start Date
        # self.SetEndDate(2022, 10, 31)  #Set End Date
        self.SetCash(100000)             #Set Strategy Cash
        self.symbol = 'SPY'
        self.ind_length = int(self.GetParameter('ind_length', 50))
        self.ind_type = int(self.GetParameter('ind_type', 1))  # 1=sma, 2=ema, 3=vwap, 4=atr
        self.direction = 'long'

         # 0 to turn off
        self.take_profit_percent = 0.05

        self.long_signal = False
        self.short_signal = False

        # reversal
        if self.algo == 2: 
            # 0 = nearby (early entry)
            # 1 = crossby (late entry)
            self.approach = 0
            self.threshold = 0.02
        
        # atr
        if self.ind_type == 4:
            self.atr_mult = float(self.GetParameter('atr_mult', 2))

        self.AddSecurity(SecurityType.Equity, self.symbol, Resolution.Hour)        
        
        if self.ind_type == 1:
            self.ind = self.SMA(self.symbol, self.ind_length, Resolution.Hour)
            self.ind_type_str = 'sma'
        elif self.ind_type == 2:
            self.ind = self.EMA(self.symbol, self.ind_length, Resolution.Hour)
            self.ind_type_str = 'ema'
        elif self.ind_type == 3:
            self.ind = self.VWAP(self.symbol, self.ind_length, Resolution.Hour)
            self.ind_type_str = 'vwap'
        elif self.ind_type == 4:
            self.ind = self.ATR(self.symbol, self.ind_length, Resolution.Hour)
            self.ind_type_str = 'atr'
        else:
            raise BaseException("Invalid ind_type")

        self.SetWarmUp(timedelta(hours=self.ind_length*2))
        self.prev_price = 0
       
    def OnData(self, data):
        if (not self.ind.IsReady) or self.IsWarmingUp or not data.ContainsKey(self.symbol) or data[self.symbol] is None:
            return

        if not self.prev_price:
            self.prev_price = data[self.symbol].Close
            self.prev_ind = self.ind.Current.Value
            return

        self.Plot("OptimalMovingAverage", self.ind_type_str, self.ind.Current)
        self.Plot("OptimalMovingAverage", "price", data[self.symbol].Close)
   
        holdings = self.Portfolio[self.symbol].Quantity

        # For ATR calculate the actual crossover indicator here
        if (self.ind_type == 4):
            # Short only for now with ATR based indicator
            if self.direction in ['long', 'both']:
                raise Exception(f"Unimplemented for atr")   
            self.atr_offset = data[self.symbol].Close - self.ind.Current.Value * self.atr_mult   

        if self.algo == 1:
            self.OnDataContinuation(data)
        elif self.algo == 2:
            self.OnDataReversal(data)
        else:
            raise Exception(f"Invalid self.algo: {self.algo}")

        if holdings == 0:
            # Open Long position if current price is greater than Indicator
            if  self.long_signal and (self.direction in ['long','both']):
                self.Log("Buy >> {0}".format(self.Securities[self.symbol].Price))
                self.SetHoldings(self.symbol, 1.0, tag='Open Buy: Long Signal')
                self.enter_price = data[self.symbol].Close
            elif self.short_signal and (self.direction in ['short','both']):
                self.Log("SELL >> {0}".format(self.Securities[self.symbol].Price))
                self.SetHoldings(self.symbol, -1.0, tag='Open Sell: Short Signal')
                self.enter_price = data[self.symbol].Close
        elif holdings > 0:
            if self.short_signal:
                self.Log("Liquidating at >> {0}".format(self.Securities[self.symbol].Price))
                self.Liquidate(self.symbol, tag='Liquidating: Short Signal')
            if self.take_profit_percent != 0:
                if data[self.symbol].Close > self.enter_price * (1+self.take_profit_percent):
                    self.Log("Liquidating at >> {0}".format(self.Securities[self.symbol].Price))
                    self.Liquidate(self.symbol, tag=f'Liquidating: Take profit reached at {data[self.symbol].Close}')

        elif holdings < 0:
            if self.long_signal:
                self.Log("Liquidating at >> {0}".format(self.Securities[self.symbol].Price))
                self.Liquidate(self.symbol, tag='Liquidating: Long Signal')  

            if self.take_profit_percent != 0:
                if data[self.symbol].Close < self.enter_price * (1-self.take_profit_percent):
                    self.Log("Liquidating at >> {0}".format(self.Securities[self.symbol].Price))
                    self.Liquidate(self.symbol, tag=f'Liquidating: Take profit reached at {data[self.symbol].Close}')


        self.prev_price = data[self.symbol].Close

        if (self.ind_type == 4):
            self.prev_ind = self.atr_offset
        else:
            self.prev_ind = self.ind.Current.Value

    def OnDataContinuation(self, data):
        crossoverInd = None
        if (self.ind_type == 4):
            crossoverInd = self.prev_ind
        else:
            crossoverInd = self.ind.Current.Value

        self.long_signal = (data[self.symbol].Close > crossoverInd) and (self.prev_price < self.prev_ind)
        self.short_signal = (data[self.symbol].Close < crossoverInd) and (self.prev_price > self.prev_ind)
        
        holdings = self.Portfolio[self.symbol].Quantity

        if holdings == 0:
            # Open Long position if current price is greater than Simple Moving Average
            if self.long_signal and (self.direction in ['long','both']):
                self.Log("Buy >> {0}".format(self.Securities[self.symbol].Price))
                self.SetHoldings(self.symbol, 1.0, tag='Open Buy: Price > MA')
                self.enter_price = data[self.symbol].Close
            elif self.short_signal and (self.direction in ['short','both']):
                self.Log("SELL >> {0}".format(self.Securities[self.symbol].Price))
                self.SetHoldings(self.symbol, -1.0, tag='Open Sell: Price < MA')
                self.enter_price = data[self.symbol].Close
    
    def OnDataReversal(self, data):
        if (self.ind_type == 4):
            raise Exception(f"Unimplemented for atr")

        if self.approach == 0:
            self.long_signal = (data[self.symbol].Close < self.ind.Current.Value*(1+self.threshold)) and \
                             (self.prev_price > self.prev_ind*(1+self.threshold))
            self.short_signal = (data[self.symbol].Close > self.ind.Current.Value*(1-self.threshold)) and \
                                (self.prev_price < self.prev_ind*(1-self.threshold))
        elif self.approach == 1:
            self.long_signal = (data[self.symbol].Close < self.ind.Current.Value*(1-self.threshold)) and \
                             (self.prev_price > self.prev_ind*(1-self.threshold))
            self.short_signal = (data[self.symbol].Close > self.ind.Current.Value*(1+self.threshold)) and \
                                (self.prev_price < self.prev_ind*(1+self.threshold))   
        else:
            raise Exception(f'Invalid approach: {self.approach}')
