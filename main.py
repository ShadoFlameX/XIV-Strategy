import data_fetcher
import trade_calculations as tcalc
import pandas as pd
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
fetchEnd = datetime.datetime(2017, 1, 1)

vixDataFrame = data_fetcher.fetchData(symbol="^VIX", startDate=fetchStart, endDate=fetchEnd)
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.deltaPct, inputColumn="Adj Close")
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricType.log, inputColumn="Adj Close")

xivDataFrame = data_fetcher.fetchData(symbol="XIV", startDate=fetchStart, endDate=fetchEnd)

startDate = xivDataFrame.index[0]
endDate = xivDataFrame.index[len(xivDataFrame.index) - 1]

pool = ThreadPoolExecutor(10)
futures = []
results = []
for outlierSMADays in range(1,4):
    for sellIndicatorSMADays in range(71,81):
        futures.append(pool.submit(tcalc.runSimulation, startDate, endDate, vixDataFrame, xivDataFrame, sellIndicatorSMADays, outlierSMADays, False))

for x in as_completed(futures):
    simResult = x.result()
    results.append(simResult)

results.sort(key=lambda x: x.profitRatio(), reverse=True)

for r in results:
    r.printDescription()
    print("")

# purchaseDates = []
# purchasePrices = []
# sellDates = []
# sellPrices = []
# for p in results[0].closedPositions:
#     purchaseDates.append(p.purchaseDate)
#     purchasePrices.append(p.purchasePrice)
#     sellDates.append(p.sellDate)
#     sellPrices.append(p.sellPrice)
#
# trimmedVixDataFrame = vixDataFrame.truncate(after=endDate, before=startDate)
#
# purchaseDataFrame = pd.DataFrame(index=purchaseDates, data=purchasePrices)
# sellDataFrame = pd.DataFrame(index=sellDates, data=sellPrices)
# ax = xivDataFrame["Adj Close"].plot(title="XIV Purchases", grid=True, figsize=(12,6), alpha=0.75, color="blue")
# trimmedVixDataFrame["Adj Close"].plot(ax=ax, grid=True, color="gray", alpha=1)
# adjCloseSMAColumn = "Adj Close " + str(sellIndicatorSMADays) + "d Avg"
# trimmedVixDataFrame[adjCloseSMAColumn].plot(ax=ax, grid=True, color="orange")
# purchaseDataFrame.plot(ax=ax, grid=True, color="green", style='^', alpha=1)
# sellDataFrame.plot(ax=ax, grid=True, color="red", style='^', alpha=1)
# plt.show()
