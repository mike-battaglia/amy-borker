###
# https://www.tradingview.com/pine/?id=PUB%3BNKRAPozzrOVOjGnzZfYFDRPk2zfhfA1m
###

//@version=3
//
//@author Makit0
// 
//script based in:
// original John Carter's ideas (SQUEEZE & SQUEEZE PRO) https://www.simplertrading.com/
// LazyBear's script (Squeeze Momentum Indicator) https://www.tradingview.com/script/nqQ1DT5a-Squeeze-Momentum-Indicator-LazyBear/
//
// USE IT IN CONJUNCTION WITH THE SQUEEZE PRO ARROWS INDICATOR
// 
// This system is based in the volatility reversion to the mean: volatility contraction leads to volatility expansion and the other way on
// The dot signal is a warning of volatility compression, more often than not this leads to a expansion of volatility and a move in the action price usually bigger than the expected move
// Be aware of the trend direction, use the momentum histogram to see the slope direction
//  
// There are 3 levels of compression:
// Level 1: ORANGE, the lesser compresion level
// Level 2: RED, the normal level marked by the original squeeze indicator
// Level 3: YELLOW, the max compression level
// The more the compression the bigger the after move
// 
// The GREEN dots signal the volatility expansion out of the squeeze ranges
// 
study(title="Makit0_Squeeze_PRO_v0.5BETA", shorttitle="SQZPRO", overlay=false)

source = close
length = 20
ma = sma(source,length)
devBB = stdev(source,length)
devKC = sma(tr,length)


//Bollinger 2x
upBB = ma + devBB * 2
lowBB = ma - devBB * 2

//Keltner 2x
upKCWide = ma + devKC * 2
lowKCWide = ma - devKC * 2

//Keltner 1.5x
upKCNormal = ma + devKC * 1.5
lowKCNormal = ma - devKC * 1.5

//Keltner 1x
upKCNarrow = ma + devKC
lowKCNarrow = ma - devKC

sqzOnWide  = (lowBB >= lowKCWide) and (upBB <= upKCWide) //WIDE SQUEEZE: ORANGE
sqzOnNormal  = (lowBB >= lowKCNormal) and (upBB <= upKCNormal) //NORMAL SQUEEZE: RED
sqzOnNarrow  = (lowBB >= lowKCNarrow) and (upBB <= upKCNarrow) //NARROW SQUEEZE: YELLOW
sqzOffWide = (lowBB < lowKCWide) and (upBB > upKCWide) //FIRED WIDE SQUEEZE: GREEN
noSqz  = (sqzOnWide == false) and (sqzOffWide == false) //NO SQUEEZE: BLUE

//Momentum Oscillator
mom = linreg(source  -  avg(avg(highest(high, length), lowest(low, length)),sma(close,length)),length,0)

//Momentum histogram color
mom_color = iff( mom > 0,iff( mom > nz(mom[1]), aqua, blue),iff( mom < nz(mom[1]), red, yellow))

//Squeeze Dots color
sq_color = noSqz ? blue : sqzOnNarrow ? yellow : sqzOnNormal ? red : sqzOnWide ? orange : lime

plot(mom, title='MOM', color=mom_color, style=histogram, linewidth=5)
plot(0, title='SQZ', color=sq_color, style=circles, transp=0, linewidth=3)

