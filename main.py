import data_fetcher
import trade_calculations as tcalc
import pandas as pd
import datetime
from dateutil.relativedelta import relativedelta
import math
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import locale
import sys
from scipy.stats import norm
from pylab import plot, show, hist, figure, title

# Local Imports
import constants as cnst
import dataframe_utilities as dfutil

# Global Setup
locale.setlocale(locale.LC_ALL, 'en_US')

def clamp(n, minn, maxn): return min(max(n, minn), maxn)

fetchStart = datetime.datetime(1900, 1, 1)
fetchEnd = datetime.datetime(2017, 1, 1)

vixDataFrame = data_fetcher.fetchData(symbol="^VIX", startDate=fetchStart, endDate=fetchEnd)
adjCloseSMAColumn = "Adj Close " + str(cnst.sellIndicatorSMADays) + "d Avg"
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.deltaPct, inputColumn="Adj Close")
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.log, inputColumn="Adj Close")
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.movingAvg, inputColumn="Adj Close", movingAvgWindow=cnst.sellIndicatorSMADays)
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.movingAvg, inputColumn="Adj Close Delta %", movingAvgWindow=cnst.outlierSMADays)
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.log, inputColumn=adjCloseSMAColumn)

xivDataFrame = data_fetcher.fetchData(symbol="XIV", startDate=fetchStart, endDate=fetchEnd)

outlierSMADeltaColumn = "Adj Close Delta % " + str(cnst.outlierSMADays) + "d Avg"

startDate = xivDataFrame.index[0]
endDate = xivDataFrame.index[len(xivDataFrame.index) - 1]
# endDate = xivDataFrame.index[100]

maxOutlay = 0.0
maxLoss = 0.0
buyDollarAmount = 1000

positions = []
printTrades = True
shouldWaitToBuy = False
date = startDate
while date < endDate:
    if date in xivDataFrame.index:
        currentIndicatorRow = vixDataFrame.ix[date]
        currentTargetRow = xivDataFrame.ix[date]

        currentPrice = currentTargetRow["Adj Close"]
        adjCloseDelta = currentIndicatorRow["Adj Close Delta %"]
        isBelowSellIndicator = currentIndicatorRow[adjCloseSMAColumn] > currentIndicatorRow["Adj Close"]
        dateStr = date.strftime("%Y-%m-%d")

        shouldWaitToBuy = shouldWaitToBuy or tcalc.shouldWaitToBuy(date=date, indicatorDataFrame=vixDataFrame, zScoreInputColumn=outlierSMADeltaColumn)
        if shouldWaitToBuy:

            if adjCloseDelta <= 0.0:
                shouldWaitToBuy = False
                if not isBelowSellIndicator:
                    shareCountToBuy = math.floor(buyDollarAmount / currentPrice)
                    pos = tcalc.TradePosition(date, currentPrice, shareCountToBuy)
                    positions.append(pos)

                    if printTrades:
                        print("   BUY: " + locale.currency(
                            pos.totalPurchasePrice()) + ", Date: " + dateStr + ", Price: " + locale.currency(currentPrice))

        if len(positions):
            openPositions = [p for p in positions if p.sellDate is None]

            if len(openPositions) and isBelowSellIndicator and adjCloseDelta >= 0.0:
                if len(openPositions) > 1:
                    outlay = sum(p.totalPurchasePrice() for p in openPositions)
                    maxOutlay = max(maxOutlay, outlay)
                    if printTrades:
                        print("OUTLAY: " + locale.currency(outlay))

                for p in openPositions:
                    p.sellDate = date
                    p.sellPrice = currentPrice

                    maxLoss = min(p.profit(), maxLoss)
                    if printTrades:
                        print("  SELL: " + locale.currency(p.totalSellPrice()) +
                              ", Date: " + dateStr +
                              ", Price: " + locale.currency(p.sellPrice) +
                              ", Profit: " + locale.currency(p.profit()))

                if printTrades:
                    print("\n")

    date = date + relativedelta(days=1)

print("  Max Outlay: " + locale.currency(maxOutlay))
print("    Max Loss: " + locale.currency(maxLoss))
print("Total Profit: " + locale.currency(sum(p.profit() for p in positions)))