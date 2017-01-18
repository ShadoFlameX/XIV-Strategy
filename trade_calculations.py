import logging
from dateutil.relativedelta import relativedelta
import dataframe_utilities as dfutil
import constants as cnst
import locale
import math
import numpy as np

logger = logging.getLogger("xivstrategy.trade_calculations")

def shouldWaitToBuy(date, indicatorDataFrame, zScoreInputColumn, zScoreThreshold):
    oneYearBefore = date - relativedelta(years=1)

    indicatorDataFrame = truncateByDateRange(indicatorDataFrame, oneYearBefore, date)

    outlierZScoreColumn = dfutil.addComputedMetricColumn(indicatorDataFrame, dfutil.MetricTypeZScore, inputColumn=zScoreInputColumn)
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

    def description(self):
        sellDateStr = self.sellDate.strftime("%Y-%m-%d") if self.sellDate is not None else "N/A"
        sellPriceStr = locale.currency(self.sellPrice) if self.sellPrice is not None else "N/A"

        return "Purchase Date: " + self.purchaseDate .strftime("%Y-%m-%d") + ", " +\
               "Purchase Price: " + locale.currency(self.purchasePrice) + ", " +\
               "Share Count: " + str(self.shareCount) + ", " +\
               "Sell Date: " + sellDateStr + ", " +\
               "Sell Price: " + sellPriceStr


class SimulationResult:
    def __init__(self, zScoreThreshold=None, sellIndicatorSMADays=None, outlierSMADays=None, highTrimPercent=None, maxOutlay=None, maxLoss=None, closedPositions=None, openPositions=None):
        self.zScoreThreshold=zScoreThreshold
        self.sellIndicatorSMADays = sellIndicatorSMADays
        self.outlierSMADays = outlierSMADays
        self.highTrimPercent = highTrimPercent
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

    def csvString(self):
        return locale.currency(self.netProfit()) + ", " +\
               str(np.round(self.profitRatio(), 4)) + ", " + \
               locale.currency(self.tradeCosts() * -1) + ", " +\
               str(len(self.closedPositions)) + ", " +\
               locale.currency(self.maxOutlay) + ", " +\
               locale.currency(self.maxLoss) + ", " +\
               str(self.zScoreThreshold) + ", " +\
               str(self.sellIndicatorSMADays) + ", " +\
               str(self.outlierSMADays) + ", " +\
               str(self.highTrimPercent)

    def description(self):
        description = "\n"
        description += "=========== Final Summary ===========\n"
        description += "          Net Profit: " + locale.currency(self.netProfit()) + "\n"
        description += "        Profit Ratio: " + str(self.profitRatio()) + "\n"
        description += "         Trade Costs: " + locale.currency(self.tradeCosts() * -1) + "\n"
        description += "         Trade Count: " + str(len(self.closedPositions)) + "\n"
        description += "          Max Outlay: " + locale.currency(self.maxOutlay) + "\n"
        description += "            Max Loss: " + locale.currency(self.maxLoss) + "\n"
        description += "" + "\n"
        description += "     zScoreThreshold: " + str(self.zScoreThreshold) + "\n"
        description += "sellIndicatorSMADays: " + str(self.sellIndicatorSMADays) + "\n"
        description += "      outlierSMADays: " + str(self.outlierSMADays) + "\n"
        description += "     highTrimPercent: " + str(self.highTrimPercent) + "\n"
        description += "==================================="

        return description

def runSimulation(startDate=None,
                  endDate=None,
                  vixDataFrame=None,
                  xivDataFrame=None,
                  sellIndicatorSMADays=cnst.sellIndicatorSMADays,
                  outlierSMADays=cnst.outlierSMADays,
                  zScoreThreshold=cnst.deltaSignificantZScore,
                  highTrimPercent=0.0,
                  printTrades=False):
    logger.info("Run simulation for zScoreThreshold: " + str(zScoreThreshold) + ", outlierSMADays: " + str(outlierSMADays) + ", sellIndicatorSMADays: " + str( sellIndicatorSMADays) + ", highTrimPercent: " + str(highTrimPercent) + "...")

    vixDataFrameCopy = vixDataFrame.copy()
    xivDataFrameCopy = xivDataFrame.copy()
    xivAdjCloseDeltaColumn = dfutil.addComputedMetricColumn(xivDataFrameCopy,
                                                               dfutil.MetricTypeDeltaPct,
                                                               inputColumn="Adj Close")
    xivAdjCloseSMAColumn = dfutil.addComputedMetricColumn(xivDataFrameCopy, dfutil.MetricTypeMovingAvg, inputColumn="Adj Close", movingAvgWindow=2)
    xivAdjCloseSMADeltaColumn = dfutil.addComputedMetricColumn(xivDataFrameCopy,
                                                               dfutil.MetricTypeDeltaPct,
                                                               inputColumn=xivAdjCloseSMAColumn)
    aggMaxOutlay = 0.0
    aggMaxLoss = 0.0
    aggProfit = 0.0
    maxOutlay = 0.0
    maxLoss = 0.0
    buyDollarAmount = 1000

    closedPositions = []
    openPositions = []
    isWaitingToBuy = False
    isWaitingToSell = False
    date = startDate
    currentYear = startDate.year

    adjCloseSMAColumn = "Adj Close " + str(sellIndicatorSMADays) + "d Avg"
    dfutil.addComputedMetricColumn(vixDataFrameCopy, dfutil.MetricTypeMovingAvg, inputColumn="Adj Close Delta %",
                                   movingAvgWindow=outlierSMADays)

    outlierSMADeltaColumn = "Adj Close Delta % " + str(outlierSMADays) + "d Avg"

    while date <= endDate:
        if date.year > currentYear or date == endDate:
            profit = sum(p.profit() for p in closedPositions if p.sellDate.year == currentYear)

            if printTrades:
                if len(openPositions):
                    logger.info("")
                logger.info("========== " + str(currentYear) + " Summary ==========")
                logger.info("  Max Outlay: " + locale.currency(maxOutlay))
                logger.info("    Max Loss: " + locale.currency(maxLoss))
                logger.info("Total Profit: " + locale.currency(profit))
                logger.info("==================================\n")
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
            targetAdjCloseDelta = currentTargetRow[xivAdjCloseDeltaColumn]
            targetAdjCloseSMADelta = currentTargetRow[xivAdjCloseSMADeltaColumn]
            isBelowSellIndicator = currentIndicatorRow[adjCloseSMAColumn] > currentIndicatorRow["Adj Close"]
            dateStr = date.strftime("%Y-%m-%d")

            isWaitingToBuy = isWaitingToBuy or shouldWaitToBuy(date=date, indicatorDataFrame=vixDataFrameCopy, zScoreInputColumn=outlierSMADeltaColumn, zScoreThreshold=zScoreThreshold)
            if isWaitingToBuy:
                if targetAdjCloseDelta >= 0.0:
                    isWaitingToBuy = False
                    if not isBelowSellIndicator:
                        shareCountToBuy = math.floor(buyDollarAmount / currentPrice)
                        pos = TradePosition(date, currentPrice, shareCountToBuy)
                        openPositions.append(pos)

                        if printTrades:
                            logger.info("   BUY: " + locale.currency(
                                pos.totalPurchasePrice()) + ", Date: " + dateStr + ", Price: " + locale.currency(
                                currentPrice))

            if len(openPositions) and (isBelowSellIndicator or isWaitingToSell):
                isWaitingToSell = True
                if targetAdjCloseSMADelta <= -0.012:
                    isWaitingToSell = False
                    outlay = sum(p.totalPurchasePrice() for p in openPositions)
                    maxOutlay = max(maxOutlay, outlay)
                    if printTrades and len(openPositions) > 1:
                        logger.info("OUTLAY: " + locale.currency(outlay))

                    for p in openPositions:
                        p.sellDate = date
                        p.sellPrice = currentPrice

                        maxLoss = min(p.profit(), maxLoss)
                        if printTrades:
                            logger.info("  SELL: " + locale.currency(p.totalSellPrice()) +
                                        ", Date: " + dateStr +
                                        ", Price: " + locale.currency(p.sellPrice) +
                                        ", Profit: " + locale.currency(p.profit()))
                    closedPositions.extend(openPositions)
                    openPositions = []

                    if printTrades:
                        logger.info("")

        date = date + relativedelta(days=1)

    return SimulationResult(zScoreThreshold=zScoreThreshold, sellIndicatorSMADays=sellIndicatorSMADays, outlierSMADays=outlierSMADays, highTrimPercent=highTrimPercent, maxOutlay=aggMaxOutlay, maxLoss=aggMaxLoss, closedPositions=closedPositions, openPositions=openPositions)
