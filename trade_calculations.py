from dateutil.relativedelta import relativedelta
import dataframe_utilities as dfutil
import constants as cnst

def shouldWaitToBuy(date, indicatorDataFrame, zScoreInputColumn):
    oneYearBefore = date - relativedelta(years=1)

    indicatorDataFrame = truncateByDateRange(indicatorDataFrame, oneYearBefore, date)

    outlierZScoreColumn = zScoreInputColumn + " Z-Score"
    dfutil.addComputedMetricColumn(indicatorDataFrame, dfutil.MetricType.zscore, inputColumn=zScoreInputColumn)
    indicatorDataFrame["WaitToBuy"] = indicatorDataFrame[outlierZScoreColumn] > cnst.deltaSignificantZScore

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
