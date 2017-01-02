import data_fetcher
import trade_calculations as tcalc
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import locale
from pylab import plot, show, hist, figure, title

from concurrent.futures import ThreadPoolExecutor, wait, as_completed


# Local Imports
import constants as cnst
import dataframe_utilities as dfutil

# Global Setup
locale.setlocale(locale.LC_ALL, 'en_US')

def clamp(n, minn, maxn): return min(max(n, minn), maxn)

fetchStart = datetime.datetime(1900, 1, 1)
fetchEnd = datetime.datetime.now()

vixDataFrame = data_fetcher.fetchData(symbol="^VIX", startDate=fetchStart, endDate=fetchEnd)
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.deltaPct, inputColumn="Adj Close")
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.log, inputColumn="Adj Close")

xivDataFrame = data_fetcher.fetchData(symbol="XIV", startDate=fetchStart, endDate=fetchEnd)

startDate = xivDataFrame.index[0]
endDate = xivDataFrame.index[len(xivDataFrame.index) - 1]

pool = ThreadPoolExecutor(100)
futures = []
results = []
for outlierSMADays in range(1,3):
    for sellIndicatorSMADays in range(65,101):
        for highTrimPercent in np.arange(0.0, 0.75, 0.05):
            movingAvgColumn = dfutil.addComputedMetricColumn(vixDataFrame,
                                                             dfutil.MetricType.trimmedMovingAvg,
                                                             inputColumn="Adj Close",
                                                             movingAvgWindow=sellIndicatorSMADays,
                                                             highTrimPercent=highTrimPercent)

            for zScore in np.arange(1.3, 2.25, 0.05):
                futures.append(pool.submit(tcalc.runSimulation, startDate, endDate, vixDataFrame, xivDataFrame, sellIndicatorSMADays, outlierSMADays, zScore, highTrimPercent, False))

            vixDataFrame.drop(movingAvgColumn, axis=1, inplace=True)

for x in as_completed(futures):
    simResult = x.result()
    results.append(simResult)

results.sort(key=lambda x: x.profitRatio(), reverse=True)

for r in results:
    r.printDescription()
    print("")

if True:
    csvString = "Net Profit, Profit Ratio, Trade Costs, Trade Count, Max Outlay, Max Loss, zScoreThreshold, sellIndicatorSMADays, outlierSMADays, highTrimPercent\n"
    for r in results:
        csvString += r.csvString() + "\n"

    text_file = open("results_output/results_" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M") + ".csv", "w")
    text_file.write(csvString)
    text_file.close()

# purchaseDates = []
# purchasePrices = []
# sellDates = []
# sellPrices = []
# for p in results[0].closedPositions:
#     purchaseDates.append(p.purchaseDate)
#     purchasePrices.append(p.purchasePrice)
#     sellDates.append(p.sellDate)
#     sellPrices.append(p.sellPrice)

# adjCloseSMATrimmedColumn = dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.trimmedMovingAvg, inputColumn="Adj Close", movingAvgWindow=sellIndicatorSMADays)
# adjCloseSMAColumn = dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.movingAvg, inputColumn="Adj Close", movingAvgWindow=sellIndicatorSMADays)
# trimmedVixDataFrame = vixDataFrame.truncate(after=endDate, before=startDate)
# trimmedXivDataFrame = xivDataFrame.truncate(after=endDate, before=startDate)

# purchaseDataFrame = pd.DataFrame(index=purchaseDates, data=purchasePrices)
# sellDataFrame = pd.DataFrame(index=sellDates, data=sellPrices)
# ax = trimmedXivDataFrame["Adj Close"].plot(title="XIV Purchases", grid=True, figsize=(12,6), alpha=0.15, color="blue")
# trimmedVixDataFrame["Adj Close"].plot(ax=ax, grid=True, color="gray", alpha=1)
# trimmedVixDataFrame[adjCloseSMATrimmedColumn].plot(ax=ax, grid=True, color="red")
# trimmedVixDataFrame[adjCloseSMAColumn].plot(ax=ax, grid=True, color="brown", alpha = 0.5)
# purchaseDataFrame.plot(ax=ax, grid=True, color="green", style='^', alpha=1)
# sellDataFrame.plot(ax=ax, grid=True, color="red", style='^', alpha=1)
# plt.show()
