import pandas as pd
import pandas_datareader.data as web  # Package and modules for importing data; this code may change depending on pandas version
import datetime
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





# We will look at stock prices over the past year, starting at January 1, 2016
start = datetime.datetime(1900, 1, 1)
end = datetime.datetime(2017, 1, 1)
# end = datetime.date.today()

# First argument is the series we want, second is the source ("yahoo" for Yahoo! Finance), third is the start date, fourth is the end date
vixDataFrame = web.DataReader("^VIX", "yahoo", start, end)
xivDataFrame = web.DataReader("XIV", "yahoo", start, end)

adjCloseSMAColumn = "Adj Close " + str(cnst.sellIndicatorSMADays) + "d Avg"
outlierSMADeltaColumn = "Adj Close Delta % " + str(cnst.outlierSMADays) + "d Avg"
outlierZScoreColumn = outlierSMADeltaColumn + " Z-Score"

dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.deltaPct, inputColumn="Adj Close")
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.log, inputColumn="Adj Close")
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.movingAvg, inputColumn="Adj Close",
                        movingAvgWindow=cnst.sellIndicatorSMADays)
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.movingAvg, inputColumn="Adj Close Delta %",
                        movingAvgWindow=cnst.outlierSMADays)
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.log, inputColumn=adjCloseSMAColumn)

# display(vixDataFrame)

# class TradeState(Enum):
#     idle = 1
#     hold = 2
#     sell = 3

class TradePosition:
    def __init__(self, shareCount, purchasePrice):
        self.shareCount = shareCount
        self.purchasePrice = purchasePrice

    def totalPrice(self):
        return (self.shareCount * self.purchasePrice)


def computeProfit(indicatorDataFrame, purchaseDataFrame, startDate, endDate, printTrades=False, printProfit=True):
    positions = []
    purchasePrice = 0.0
    buyDollarAmount = 1000
    maxPurchase = 0.0
    maxLoss = 0.0
    allProfits = []
    shouldPrint = True
    waitToBuy = False

    dataFrameSlice = indicatorDataFrame[startDate: endDate].copy()
    dfutil.addComputedMetricColumn(dataFrameSlice, dfutil.MetricType.zscore, inputColumn=outlierSMADeltaColumn)
    dataFrameSlice["WaitToBuy"] = dataFrameSlice[outlierZScoreColumn] > cnst.deltaSignificantZScore

    for index, row in dataFrameSlice.iterrows():
        # 1. Watch for statistically significant positive Velocity event in VIX
        # 2. Once velocity event occurs wait for velocity to return to 0.0, then purchase XIV
        # 3. Wait for VIX to drop below long-term moving average
        # 4. Once VIX is below moving average, sell stock when velocity is 0.0 (or slightly positive)

        dateStr = index.strftime("%Y-%m-%d")
        purchasePrice = purchaseDataFrame.loc[index, "Adj Close"]
        isBelowSellIndicator = row[adjCloseSMAColumn] > row["Adj Close"]

        waitToBuy = waitToBuy or (row["WaitToBuy"] == True)

        if waitToBuy:
            if row[outlierSMADeltaColumn] <= 0.0:
                waitToBuy = False
                if not isBelowSellIndicator:
                    pos = TradePosition(math.floor(buyDollarAmount / purchasePrice), purchasePrice)
                    positions.append(pos)
                    maxPurchase = max(maxPurchase, pos.totalPrice())
                    if printTrades:
                        print("   BUY: " + locale.currency(
                            pos.totalPrice()) + ", Date: " + dateStr + ", Price: " + locale.currency(purchasePrice))

        if len(positions) and isBelowSellIndicator and row[outlierSMADeltaColumn] >= 0.0:
            if len(positions) > 1:
                outlay = sum(p.totalPrice() for p in positions)
                if printTrades:
                    print("OUTLAY: " + locale.currency(outlay))
            for p in positions:
                profit = (purchasePrice - p.purchasePrice) * p.shareCount
                maxLoss = min(profit, maxLoss)
                allProfits.append(profit)
                if printTrades:
                    print("  SELL: " + locale.currency(
                        purchasePrice * p.shareCount) + ", Date: " + dateStr + ", Price: " + locale.currency(
                        purchasePrice) + ", Profit: " + locale.currency(profit))
            positions = []
            if printTrades:
                print("\n")

    if printProfit:
        print(startDate.strftime("%Y") + " - " + endDate.strftime("%Y"))
        print("   max loss: " + locale.currency(maxLoss))
        print("Term profit: " + locale.currency(sum(allProfits)))
        print("   Open Pos: " + str(len(positions)))
        print("\n")

    return sum(allProfits)


totalProfit = 0
for year in range(2011, 2017):
    totalProfit += computeProfit(vixDataFrame, xivDataFrame, datetime.datetime(year, 1, 1),
                                 datetime.datetime(year + 1, 1, 1), printTrades=True, printProfit=True)

print("Total Profit: " + locale.currency(totalProfit))

alertLineStyle = ['c-']
purchaseLineStyle = ['m-']
sellLineStyle = ['r-']

graphStartDate = datetime.datetime(2011,1,1)
graphEndDate = datetime.datetime(2012,1,1)

vixDataFrame = vixDataFrame[graphStartDate : graphEndDate].copy()
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.zscore, inputColumn=outlierSMADeltaColumn)
vixDataFrame["WaitToBuy"] = vixDataFrame[outlierZScoreColumn] > cnst.deltaSignificantZScore

# vixDataFrame["Adj Close"].plot(title="^VIX", grid=True, figsize=(12,6), alpha=0.75, color="blue")
# plt.legend(loc=2)
# plt.show()

xivDataFrame = xivDataFrame[graphStartDate : graphEndDate].copy()
xivDataFrame["Adj Close"].plot(title="XIV", grid=True, figsize=(12,6), alpha=0.75, color="green")
vixDataFrame["Adj Close"].plot(title="^VIX", grid=True, figsize=(12,6), alpha=0.75, color="gray")
vixDataFrame[adjCloseSMAColumn].plot(grid=True, color="orange")
vixOutlierDataFrame = vixDataFrame[vixDataFrame['WaitToBuy'] == True]
vixOutlierDataFrame["Adj Close"].plot(grid=True, color="red", style='^', alpha=1,)
# plt.legend(loc=2)
vixDataFrame[outlierZScoreColumn].plot(grid=True, secondary_y=[outlierZScoreColumn], color="red", alpha=0.25,)
plt.show()
