from dateutil.relativedelta import relativedelta
import dataframe_utilities as dfutil
import constants as cnst
import locale
import math

def shouldWaitToBuy(date, indicatorDataFrame, zScoreInputColumn, zScoreThreshold):
    oneYearBefore = date - relativedelta(years=1)

    indicatorDataFrame = truncateByDateRange(indicatorDataFrame, oneYearBefore, date)

    outlierZScoreColumn = zScoreInputColumn + " Z-Score"
    dfutil.addComputedMetricColumn(indicatorDataFrame, dfutil.MetricType.zscore, inputColumn=zScoreInputColumn)
    indicatorDataFrame["WaitToBuy"] = indicatorDataFrame[outlierZScoreColumn] > zScoreThreshold

    return indicatorDataFrame.tail(1)["WaitToBuy"][0]


def truncateByDateRange(dataFrame, startDate, EndDate):
    dataFrame = dataFrame.truncate(before=startDate)
    dataFrame = dataFrame.truncate(after=EndDate)
    return dataFrame

class TradePosition:
    def __init__(self, purchaseDate, purchasePrice, shareCount, sellDate=None, sellPrice=None):
        self.purchaseDate = purchaseDate
        self.purchasePrice = purchasePrice
        self.shareCount = shareCount
        self.sellDate = sellDate
        self.sellPrice = sellPrice

    def totalPurchasePrice(self):
        return (self.shareCount * self.purchasePrice)

    def totalSellPrice(self):
        return (self.shareCount * self.sellPrice)

    def profit(self):
        return (self.sellPrice - self.purchasePrice) * self.shareCount


class SimulationResult:
    def __init__(self, zScoreThreshold=None, sellIndicatorSMADays=None, outlierSMADays=None, maxOutlay=0.0, maxLoss=0.0, closedPositions=None, openPositions=None):
        self.zScoreThreshold=zScoreThreshold
        self.sellIndicatorSMADays = sellIndicatorSMADays
        self.outlierSMADays = outlierSMADays
        self.maxOutlay = maxOutlay
        self.maxLoss = maxLoss
        self.closedPositions = closedPositions
        self.openPositions = openPositions

    def netProfit(self):
        netProfit = 0.0
        for p in self.closedPositions:
            netProfit += p.totalSellPrice() - p.totalPurchasePrice()
        netProfit -= self.tradeCosts()
        return netProfit

    def tradeCosts(self):
        return len(self.closedPositions) * cnst.tradingCost * 2

    def profitRatio(self):
        if self.netProfit() > 0:
            return self.netProfit() / self.maxOutlay
        else:
            return 0.0

    def printDescription(self):
        print("========== Final Summary ==========")
        print("          Net Profit: " + locale.currency(self.netProfit()))
        print("        Profit Ratio: " + str(self.profitRatio()))
        print("         Trade Costs: " + locale.currency(self.tradeCosts() * -1))
        print("         Trade Count: " + str(len(self.closedPositions)))
        print("          Max Outlay: " + locale.currency(self.maxOutlay))
        print("            Max Loss: " + locale.currency(self.maxLoss))
        print("")
        print("     zScoreThreshold: " + str(self.zScoreThreshold))
        print("sellIndicatorSMADays: " + str(self.sellIndicatorSMADays))
        print("      outlierSMADays: " + str(self.outlierSMADays))
        print("===================================")


def runSimulation(startDate=None,
                  endDate=None,
                  vixDataFrame=None, xivDataFrame=None,
                  sellIndicatorSMADays=cnst.sellIndicatorSMADays,
                  outlierSMADays=cnst.outlierSMADays,
                  zScoreThreshold=cnst.deltaSignificantZScore,
                  printTrades=False):
    print("Run simulation for zScoreThreshold: " + str(zScoreThreshold) + ", outlierSMADays: " + str(outlierSMADays) + ", sellIndicatorSMADays: " + str( sellIndicatorSMADays) + "...")

    vixDataFrameCopy = vixDataFrame.copy()
    xivDataFrameCopy = xivDataFrame.copy()

    aggMaxOutlay = 0.0
    aggMaxLoss = 0.0
    aggProfit = 0.0
    maxOutlay = 0.0
    maxLoss = 0.0
    buyDollarAmount = 1000

    closedPositions = []
    openPositions = []
    shouldWait = False
    date = startDate
    currentYear = startDate.year

    adjCloseSMAColumn = "Adj Close " + str(sellIndicatorSMADays) + "d Avg"
    dfutil.addComputedMetricColumn(vixDataFrameCopy, dfutil.MetricType.movingAvg, inputColumn="Adj Close",
                                   movingAvgWindow=sellIndicatorSMADays)
    dfutil.addComputedMetricColumn(vixDataFrameCopy, dfutil.MetricType.movingAvg, inputColumn="Adj Close Delta %",
                                   movingAvgWindow=outlierSMADays)
    dfutil.addComputedMetricColumn(vixDataFrameCopy, dfutil.MetricType.log, inputColumn=adjCloseSMAColumn)

    outlierSMADeltaColumn = "Adj Close Delta % " + str(outlierSMADays) + "d Avg"

    while date <= endDate:
        if date.year > currentYear or date == endDate:
            profit = sum(p.profit() for p in closedPositions if p.sellDate.year == currentYear)

            if printTrades:
                if len(openPositions):
                    print("")
                print("========== " + str(currentYear) + " Summary ==========")
                print("  Max Outlay: " + locale.currency(maxOutlay))
                print("    Max Loss: " + locale.currency(maxLoss))
                print("Total Profit: " + locale.currency(profit))
                print("==================================\n")
            aggMaxOutlay = max(aggMaxOutlay, maxOutlay)
            aggMaxLoss = min(aggMaxLoss, maxLoss)
            aggProfit += profit
            maxOutlay = 0
            maxLoss = 0
            currentYear = date.year

        if date in xivDataFrameCopy.index:
            currentIndicatorRow = vixDataFrameCopy.ix[date]
            currentTargetRow = xivDataFrameCopy.ix[date]

            currentPrice = currentTargetRow["Adj Close"]
            adjCloseDelta = currentIndicatorRow["Adj Close Delta %"]
            isBelowSellIndicator = currentIndicatorRow[adjCloseSMAColumn] > currentIndicatorRow["Adj Close"]
            dateStr = date.strftime("%Y-%m-%d")

            shouldWait = shouldWait or shouldWaitToBuy(date=date, indicatorDataFrame=vixDataFrameCopy, zScoreInputColumn=outlierSMADeltaColumn, zScoreThreshold=zScoreThreshold)
            if shouldWait:

                if adjCloseDelta <= 0.0:
                    shouldWait = False
                    if not isBelowSellIndicator:
                        shareCountToBuy = math.floor(buyDollarAmount / currentPrice)
                        pos = TradePosition(date, currentPrice, shareCountToBuy)
                        openPositions.append(pos)

                        if printTrades:
                            print("   BUY: " + locale.currency(
                                pos.totalPurchasePrice()) + ", Date: " + dateStr + ", Price: " + locale.currency(
                                currentPrice))

            if len(openPositions) and isBelowSellIndicator and adjCloseDelta >= 0.0:
                outlay = sum(p.totalPurchasePrice() for p in openPositions)
                maxOutlay = max(maxOutlay, outlay)
                if printTrades and len(openPositions) > 1:
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
                closedPositions.extend(openPositions)
                openPositions = []

                if printTrades:
                    print("")

        date = date + relativedelta(days=1)

    return SimulationResult(zScoreThreshold=zScoreThreshold, sellIndicatorSMADays=sellIndicatorSMADays, outlierSMADays=outlierSMADays, maxOutlay=aggMaxOutlay, maxLoss=aggMaxLoss, closedPositions=closedPositions, openPositions=openPositions)
