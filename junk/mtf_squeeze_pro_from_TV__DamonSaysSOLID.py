// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © Beardy_Fred

//@version=5
indicator("Multi-Timeframe TTM Squeeze Pro", shorttitle="MTF Squeeze Pro", overlay=true)

length          = input.int(20, "TTM Squeeze Length")

//BOLLINGER BANDS
BB_mult         = input.float(2.0, "Bollinger Band STD Multiplier")
BB_basis        = ta.sma(close, length)
dev             = BB_mult * ta.stdev(close, length)
BB_upper        = BB_basis + dev
BB_lower        = BB_basis - dev

//KELTNER CHANNELS
KC_mult_high    = input.float(1.0, "Keltner Channel #1")
KC_mult_mid     = input.float(1.5, "Keltner Channel #2")
KC_mult_low     = input.float(2.0, "Keltner Channel #3")
KC_basis        = ta.sma(close, length)
devKC           = ta.sma(ta.tr, length)
KC_upper_high   = KC_basis + devKC * KC_mult_high
KC_lower_high   = KC_basis - devKC * KC_mult_high
KC_upper_mid    = KC_basis + devKC * KC_mult_mid
KC_lower_mid    = KC_basis - devKC * KC_mult_mid
KC_upper_low    = KC_basis + devKC * KC_mult_low
KC_lower_low    = KC_basis - devKC * KC_mult_low

//SQUEEZE CONDITIONS
NoSqz           = BB_lower < KC_lower_low or BB_upper > KC_upper_low //NO SQUEEZE: GREEN
LowSqz          = BB_lower >= KC_lower_low or BB_upper <= KC_upper_low //LOW COMPRESSION: BLACK
MidSqz          = BB_lower >= KC_lower_mid or BB_upper <= KC_upper_mid //MID COMPRESSION: RED
HighSqz         = BB_lower >= KC_lower_high or BB_upper <= KC_upper_high //HIGH COMPRESSION: ORANGE

//MOMENTUM OSCILLATOR
mom             = ta.linreg(close - math.avg(math.avg(ta.highest(high, length), ta.lowest(low, length)), ta.sma(close, length)), length, 0)

//MOMENTUM HISTOGRAM COLOR
mom_up1_col     = input.color(color.new(color.aqua, 0), title = "+ive Rising Momentum", group = "Histogram Color")
mom_up2_col     = input.color(color.new(#2962ff, 0), title = "+ive Falling Momentum", group = "Histogram Color")
mom_down1_col   = input.color(color.new(color.red, 0), title = "-ive Rising Momentum", group = "Histogram Color")
mom_down2_col   = input.color(color.new(color.yellow, 0), title = "-ive Falling Momentum", group = "Histogram Color")

iff_1           = mom > nz(mom[1]) ? mom_up1_col : mom_up2_col
iff_2           = mom < nz(mom[1]) ? mom_down1_col : mom_down2_col
mom_color       = mom > 0 ? iff_1 : iff_2

//SQUEEZE DOTS COLOR
NoSqz_Col       = input.color(color.new(color.green, 0), title = "No Squeeze", group = "Squeeze Dot Color")
LowSqz_Col      = input.color(color.new(color.black, 0), title = "Low Compression", group = "Squeeze Dot Color")
MidSqz_Col      = input.color(color.new(color.red, 0), title = "Medium Compression", group = "Squeeze Dot Color")
HighSqz_Col     = input.color(color.new(color.orange, 0), title = "High Compression", group = "Squeeze Dot Color")

sq_color        = HighSqz ? HighSqz_Col : MidSqz ? MidSqz_Col : LowSqz ? LowSqz_Col : NoSqz_Col

//MULTI TIMEFRAME HISTOGRAM COLOR
[HC_1m]         = request.security(syminfo.tickerid, "1", [mom_color])
[HC_5m]         = request.security(syminfo.tickerid, "5", [mom_color])
[HC_15m]        = request.security(syminfo.tickerid, "15", [mom_color])
[HC_30m]        = request.security(syminfo.tickerid, "30", [mom_color])
[HC_1H]         = request.security(syminfo.tickerid, "60", [mom_color])
[HC_4H]         = request.security(syminfo.tickerid, "240", [mom_color])
[HC_D]          = request.security(syminfo.tickerid, "D"  , [mom_color])
[HC_W]          = request.security(syminfo.tickerid, "W"  , [mom_color])
[HC_M]          = request.security(syminfo.tickerid, "M"  , [mom_color])

//MULTI TIMEFRAME SQUEEZE COLOR
[SC_1m]         = request.security(syminfo.tickerid, "1", [sq_color])
[SC_5m]         = request.security(syminfo.tickerid, "5", [sq_color])
[SC_15m]        = request.security(syminfo.tickerid, "15", [sq_color])
[SC_30m]        = request.security(syminfo.tickerid, "30", [sq_color])
[SC_1H]         = request.security(syminfo.tickerid, "60", [sq_color])
[SC_4H]         = request.security(syminfo.tickerid, "240", [sq_color])
[SC_D]          = request.security(syminfo.tickerid, "D"  , [sq_color])
[SC_W]          = request.security(syminfo.tickerid, "W"  , [sq_color])
[SC_M]          = request.security(syminfo.tickerid, "M"  , [sq_color])

tableYposInput  = input.string("top", "Panel position", options = ["top", "middle", "bottom"])
tableXposInput  = input.string("right", "", options = ["left", "center", "right"])

var table TTM   = table.new(tableYposInput + "_" + tableXposInput, 10, 2, border_width = 1)

TC              = input.color(color.new(color.white, 0), "Table Text Color")
TS              = input.string(size.small, "Table Text Size", options = [size.tiny, size.small, size.normal, size.large])

if barstate.isconfirmed
    table.cell(TTM, 0, 0, "MOM", text_color = color.new(color.white, 0), bgcolor = color.new(color.gray, 0), text_size = TS)
    table.cell(TTM, 1, 0, "1m", text_color = TC, bgcolor = HC_1m, text_size = TS)
    table.cell(TTM, 2, 0, "5m", text_color = TC, bgcolor = HC_5m, text_size = TS)
    table.cell(TTM, 3, 0, "15m", text_color = TC, bgcolor = HC_15m, text_size = TS)
    table.cell(TTM, 4, 0, "30m", text_color = TC, bgcolor = HC_30m, text_size = TS)
    table.cell(TTM, 5, 0, "1H", text_color = TC, bgcolor = HC_1H, text_size = TS)
    table.cell(TTM, 6, 0, "4H", text_color = TC, bgcolor = HC_4H, text_size = TS)
    table.cell(TTM, 7, 0, "D", text_color = TC, bgcolor = HC_D, text_size = TS)
    table.cell(TTM, 8, 0, "W", text_color = TC, bgcolor = HC_W, text_size = TS)
    table.cell(TTM, 9, 0, "M", text_color = TC, bgcolor = HC_M, text_size = TS)
    
    table.cell(TTM, 0, 1, "SQZ", text_color = color.new(color.white, 0), bgcolor = color.new(color.gray, 0), text_size = TS)
    table.cell(TTM, 1, 1, "1m", text_color = TC, bgcolor = SC_1m, text_size = TS)
    table.cell(TTM, 2, 1, "5m", text_color = TC, bgcolor = SC_5m, text_size = TS)
    table.cell(TTM, 3, 1, "15m", text_color = TC, bgcolor = SC_15m, text_size = TS)
    table.cell(TTM, 4, 1, "30m", text_color = TC, bgcolor = SC_30m, text_size = TS)
    table.cell(TTM, 5, 1, "1H", text_color = TC, bgcolor = SC_1H, text_size = TS)
    table.cell(TTM, 6, 1, "4H", text_color = TC, bgcolor = SC_4H, text_size = TS)
    table.cell(TTM, 7, 1, "D", text_color = TC, bgcolor = SC_D, text_size = TS)
    table.cell(TTM, 8, 1, "W", text_color = TC, bgcolor = SC_W, text_size = TS)
    table.cell(TTM, 9, 1, "M", text_color = TC, bgcolor = SC_M, text_size = TS)
