###
# https://www.tradingview.com/pine/?id=PUB%3B4a1f75b8d4584640b4adf197b3d8bef5
###

#region imports
from AlgorithmImports import *
from collections import deque
from scipy import stats
import talib
from numpy import mean, array
#endregion

# Good indicator template: https://www.quantconnect.com/forum/discussion/12691/python-indicator-template/p1
# I did not use it here but it should derive from.

# Use like this:
#
# self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol
# NOT SURE WHERE TO PUT THE EXTRA PARAMETERS LIKE SECURITY AND ALGORITHM§
# 1. in this first try i'm sending the algorithm when creating it.
# self.squeeze = TTMSqueezePro("squeeze", 21)
# self.RegisterIndicator(self.spy, self.squeeze, Resolution.Daily)
# history = self.History(self.spy, 21, Resolution.Daily)
# self.squeeze.Warmup(history)

# TODO: there is a problem with the values being one day late. I'm not sure if it's because of how we close it but it might be the daily period.

class TTMSqueezePro(PythonIndicator):
    Squeeze = 0 # like value this is the second part of the indicator.

    # //BOLLINGER BANDS
    BB_mult = 2.0 # input.float(2.0, "Bollinger Band STD Multiplier")
    # //KELTNER CHANNELS
    KC_mult_high = 1.0 # input.float(1.0, "Keltner Channel #1")
    KC_mult_mid = 1.5 # input.float(1.5, "Keltner Channel #2")
    KC_mult_low = 2.0 # input.float(2.0, "Keltner Channel #3")

    SQZ_COLORS = ['green', 'black', 'red', 'orange']

    # according to this example we don't need to pass security and algo as that
    # will be passed with RegisterIndicator.
    # https://github.com/QuantConnect/Lean/blob/b9d3d999170f385e2371fc3fef1823f2ddd4c83b/Algorithm.Python/CustomWarmUpPeriodIndicatorAlgorithm.py

    def __init__(self, name, length = 20):
        # default indicator definition
        super().__init__()
        self.Name = name
        self.Value = 0
        self.Time = datetime.min
        self.Squeeze = 0

        # set automatic warmup period
        self.WarmUpPeriod = length * 3

        self.length = length
        self.queue = deque(maxlen=self.length)
        self.queueMean = deque(maxlen=self.length)
        self.queueSqz = deque(maxlen=self.length)

        # define the base indicators to use
        self.BB = BollingerBands(self.length, self.BB_mult)
        self.KCHigh = KeltnerChannels(self.length, self.KC_mult_high)
        self.KCMid = KeltnerChannels(self.length, self.KC_mult_mid)
        self.KCLow = KeltnerChannels(self.length, self.KC_mult_low)

        self.MAX = Maximum(self.length)
        self.MIN = Minimum(self.length)
        self.SMA = SimpleMovingAverage('SMA', self.length)

    @property
    def IsReady(self) -> bool:
        # it's ready when:
        # - we have enough data to calculate the momentum oscilator value
        # - we have enough data to calculate the squeeze data
        return (len(self.queueMean) >= self.length) and self.BB.IsReady and self.KCHigh.IsReady and self.KCMid.IsReady and self.KCLow.IsReady

    def ManualUpdate(self, input) -> bool:
        self.Update(input)
        if self.IsReady:
            self.Current = IndicatorDataPoint(input.Symbol, input.Time, self.Value)
        return self.IsReady

    def Update(self, input) -> bool:
        # update all the indicators with the new data
        dataPoint = IndicatorDataPoint(input.Symbol, input.Time, input.Close)
        self.BB.Update(dataPoint)
        self.SMA.Update(dataPoint)
        # Feed into the Max and Min indicators the highest and lowest values only
        self.MAX.Update(IndicatorDataPoint(input.Symbol, input.Time, input.High))
        self.MIN.Update(IndicatorDataPoint(input.Symbol, input.Time, input.Low))
        # Keltner channels indicators
        self.KCHigh.Update(input)
        self.KCMid.Update(input)
        self.KCLow.Update(input)

        # Calculate the mom oscillator only after we get the proper amount of values for the array.
        if len(self.queueMean) >= self.length:
            self.Time = input.Time
            self.Value = self.MomOscillator()
            # self.Current = IndicatorDataPoint(input.Symbol, input.Time, self.Value)
            # self.OnUpdated(self.Current)
            data = IndicatorDataPoint(input.Symbol, input.Time, self.Value)
            if len(self.queue) > 0 and data.Time == self.queue[0].Time:
                self.queue[0] = data
            else:
                self.queue.appendleft(data)

        # calculate momentum oscilator.
        if self.MAX.IsReady and self.MIN.IsReady and self.SMA.IsReady:
            data = IndicatorDataPoint(input.Symbol, input.Time, self.MeanPrice(input.Close))
            if len(self.queueMean) > 0 and data.Time == self.queueMean[0].Time:
                self.queueMean[0] = data
            else:
                self.queueMean.appendleft(data)

        # Add the value and sqz status to a queue so we can check later if
        # we switched status recently.
        if self.BB.IsReady and self.KCHigh.IsReady and self.KCMid.IsReady and self.KCLow.IsReady:
            self.Squeeze = self.SqueezeValue()
            data = IndicatorDataPoint(input.Symbol, input.Time, self.Squeeze)
            if len(self.queueSqz) > 0 and data.Time == self.queueSqz[0].Time:
                self.queueSqz[0] = data
            else:
                self.queueSqz.appendleft(data)

        return self.IsReady

    def KC_basis(self):
        return self.sma.Current.Value

    def BB_basis(self):
        # return self.sma.Current.Value
        return self.BB.MiddleBand.Current.Value

    def BB_upper(self):
        return self.BB.UpperBand.Current.Value

    def BB_lower(self):
        return self.BB.LowerBand.Current.Value

    def KC_upper_high(self):
        return self.KCHigh.UpperBand.Current.Value

    def KC_lower_high(self):
        return self.KCHigh.LowerBand.Current.Value

    def KC_upper_mid(self):
        return self.KCMid.UpperBand.Current.Value

    def KC_lower_mid(self):
        return self.KCMid.LowerBand.Current.Value

    def KC_upper_low(self):
        return self.KCLow.UpperBand.Current.Value

    def KC_lower_low(self):
        return self.KCLow.LowerBand.Current.Value

    # //SQUEEZE CONDITIONS
    def NoSqz(self):
        return self.BB_lower() < self.KC_lower_low() or self.BB_upper() > self.KC_upper_low() # NO SQUEEZE: GREEN

    def LowSqz(self):
        return self.BB_lower() >= self.KC_lower_low() or self.BB_upper() <= self.KC_upper_low() # LOW COMPRESSION: BLACK

    def MidSqz(self):
        return self.BB_lower() >= self.KC_lower_mid() or self.BB_upper() <= self.KC_upper_mid() # MID COMPRESSION: RED

    def HighSqz(self):
        return self.BB_lower() >= self.KC_lower_high() or self.BB_upper() <= self.KC_upper_high() # HIGH COMPRESSION: ORANGE

    # //SQUEEZE DOTS COLOR
    # sq_color = HighSqz ? color.new(color.orange, 0) : MidSqz ? color.new(color.red, 0) : LowSqz ? color.new(color.black, 0) : color.new(color.green, 0)
    def SqueezeColor(self):
        if self.HighSqz():
            return 'orange'
        elif self.MidSqz():
            return 'red'
        elif self.LowSqz():
            return 'black'
        else:
            return 'green'

    def SqueezeValue(self):
        return self.SQZ_COLORS.index(self.SqueezeColor())

    def MomentumHistogramColor(self):
        bullish = Color.Aqua if self.queue[0].Value > self.queue[1].Value else Color.Blue
        bearish = Color.Red if self.queue[0].Value < self.queue[1].Value else Color.Yellow
        return bullish if self.Bullish() else bearish

    def Bullish(self):
        return self.queue[0].Value > 0

    def Bearish(self):
        return self.queue[0].Value <= 0

    # This calculates the mean price value that we'll add to a series type/array and we'll use to
    # calculate the momentum oscilator (aka linear regression)
    def MeanPrice(self, price):
        return price - mean([mean([self.MAX.Current.Value, self.MIN.Current.Value]), self.SMA.Current.Value])

    def LosingMomentum(self, maxDays = 2):
        # reverse the momentum values
        slicedQueue = list(self.queue)[:maxDays]
        # if absolute then we also check the momentum `color`
        # go over the reversed values and make sure they are decreasing
        return all(earlier.Value > later.Value for later, earlier in zip(slicedQueue, slicedQueue[1:]))

    def GainingMomentum(self, maxDays = 2):
        # reverse the momentum values
        slicedQueue = list(self.queue)[:maxDays]
        # if absolute then we also check the momentum `color`
        # go over the reversed values and make sure they are increasing
        return all(earlier.Value < later.Value for later, earlier in zip(slicedQueue, slicedQueue[1:]))

    # It's squeezing if the colors are different than green.
    def Squeezing(self):
        current = self.queueSqz[0]
        return current.Value != self.SQZ_COLORS.index('green')

    def SqueezeChange(self, toColor = 'green'):
        earlier = self.queueSqz[1]
        last = self.queueSqz[0]
        colorIndex = self.SQZ_COLORS.index(toColor)
        return last.Value == colorIndex and earlier.Value != last.Value

    def SqueezeDuration(self, over = 2):
        # pick last `over` days but today/current value
        slicedQueue = list(self.queueSqz)[1:over+1]
        colorIndex = self.SQZ_COLORS.index('green')
        # go over the reversed values and make sure they are increasing
        return all(val.Value != colorIndex for val in slicedQueue)

    def MomOscillator(self):
        '''
        //MOMENTUM OSCILLATOR
        mom = ta.linreg(close - math.avg(math.avg(
                                                  ta.highest(high, length),
                                                  ta.lowest(low, length)
                                                  ),
                                         ta.sma(close, length)
                                        ),
                        length, 0)

        https://www.quantconnect.com/forum/discussion/10168/least-squares-linear-regression/p1/comment-28627
        https://www.tradingview.com/pine-script-reference/v4/#fun_linreg

        // linreg = intercept + slope * (length - 1 - offset)
        // where length is the y argument,
        // offset is the z argument,
        // intercept and slope are the values calculated with the least squares method on source series (x argument).
        -> linreg(source, length, offset) → series[float]
        '''
        # x = [range(len(self.queueMean))]
        # y = self.queueMean

        # slope, intercept = stats.linregress(x, y)[0], stats.linregress(x, y)[1]
        # linreg = intercept + slope * (self.length - 1)

        # we need to reverse the queue in order to get the most recent regression
        series = array([m.Value for m in reversed(self.queueMean)])
        size = len(series)
        # considering we are not taking a shorter regression value we are going to get the last value
        # of the returned array as that is where the linar regression value sits the rest are `nan`
        linreg = talib.LINEARREG(series, size)[size - 1]

        return linreg

    def Warmup(self, history):
        for index, row in history.iterrows():
            self.Update(row)
