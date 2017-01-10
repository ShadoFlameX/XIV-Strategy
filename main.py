import dataframe_utilities as dfutil
import data_fetcher
import email_helper
import trade_calculations as tcalc

import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import locale
from concurrent.futures import ThreadPoolExecutor, wait, as_completed
import os
import sys

import pandas as pd
from pylab import plot, show, hist, figure, title
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Global Setup
locale.setlocale(locale.LC_ALL, 'en_US')
SHOULD_SAVE_CSV_FILE = False
SHOULD_SEND_EMAIL = True
FETCH_LATEST_QUOTE = True

def clamp(n, minn, maxn): return min(max(n, minn), maxn)

fetchStart = datetime.datetime(1900, 1, 1)
fetchEnd = datetime.datetime.now()

vixDataFrame = data_fetcher.fetchData(symbol="^VIX", startDate=fetchStart, endDate=fetchEnd, fetchLatestQuote=FETCH_LATEST_QUOTE)
dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricTypeDeltaPct, inputColumn="Adj Close")

xivDataFrame = data_fetcher.fetchData(symbol="XIV", startDate=fetchStart, endDate=fetchEnd, fetchLatestQuote=FETCH_LATEST_QUOTE)

endDate = xivDataFrame.index[len(xivDataFrame.index) - 1] #datetime.datetime(2015, 2, 25) #
startDate = endDate - relativedelta(years=1) #xivDataFrame.index[0] #

pool = ThreadPoolExecutor(4)

outlierSMADaysRange = [2] #range(2,3)
sellIndicatorSMADaysRange = [60] #range(60,91)
highTrimPercentRange = [0] #np.arange(0.0, 0.71, 0.1)
zScoreRange = [2.0] #np.arange(1.3, 2.36, 0.05)
futures = []
results = []
for outlierSMADays in outlierSMADaysRange:
    for sellIndicatorSMADays in sellIndicatorSMADaysRange:
        for highTrimPercent in highTrimPercentRange:
            movingAvgColumn = dfutil.addComputedMetricColumn(vixDataFrame,
                                                             dfutil.MetricTypeTrimmedMovingAvg,
                                                             inputColumn="Adj Close",
                                                             movingAvgWindow=sellIndicatorSMADays,
                                                             highTrimPercent=highTrimPercent)

            for zScore in zScoreRange:
                futures.append(pool.submit(tcalc.runSimulation, startDate, endDate, vixDataFrame, xivDataFrame, sellIndicatorSMADays, outlierSMADays, zScore, highTrimPercent, False))

            vixDataFrame.drop(movingAvgColumn, axis=1, inplace=True)

for x in as_completed(futures):
    simResult = x.result()
    results.append(simResult)

results.sort(key=lambda x: x.profitRatio(), reverse=True)

for r in results:
    r.printDescription()
    print("")

if SHOULD_SAVE_CSV_FILE:
    csvString = "Net Profit, Profit Ratio, Trade Costs, Trade Count, Max Outlay, Max Loss, zScoreThreshold, sellIndicatorSMADays, outlierSMADays, highTrimPercent\n"
    for r in results:
        csvString += r.csvString() + "\n"

    resultsFilePath = os.path.dirname(os.path.realpath(__file__)) + "/" + "results_output/results_" + datetime.datetime.now().strftime("%Y-%m-%d_%H%M") + ".csv"
    text_file = open(resultsFilePath, "w")
    text_file.write(csvString)
    text_file.close()


if SHOULD_SEND_EMAIL:
    lastDate = xivDataFrame.index[len(xivDataFrame.index) - 1]
    if lastDate.date() == datetime.datetime.now().date():
        # Send an email with buy/sell info for today
        topResult = results[0]
        currentPrice = currentIndicatorRow = xivDataFrame.ix[lastDate]["Adj Close"]
        trimmedXivDataFrame = xivDataFrame.truncate(after=endDate, before=startDate)
        chartImage = data_fetcher.chart_image(trimmedXivDataFrame)

        email_helper.sendSummaryEmail(date=datetime.datetime.now(), currentPrice=currentPrice, openPositions=topResult.openPositions, closedPositions=topResult.closedPositions, chartImage=chartImage)
    else:
        print("Skip sending email, last quote date is not today")

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
#
# xivAdjCloseSMAColumn = dfutil.addComputedMetricColumn(xivDataFrame, dfutil.MetricTypeMovingAvg, inputColumn="Adj Close", movingAvgWindow=3)
# outlierSMADeltaColumn = dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricTypeMovingAvg, inputColumn="Adj Close Delta %", movingAvgWindow=results[0].outlierSMADays)
# adjCloseSMATrimmedColumn = dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricTypeTrimmedMovingAvg, inputColumn="Adj Close", movingAvgWindow=results[0].sellIndicatorSMADays, highTrimPercent=results[0].highTrimPercent)
# adjCloseSMAColumn = dfutil.addComputedMetricColumn(vixDataFrame, dfutil.MetricTypeMovingAvg, inputColumn="Adj Close", movingAvgWindow=results[0].sellIndicatorSMADays)
# trimmedVixDataFrame = vixDataFrame.truncate(after=endDate, before=startDate)
# trimmedXivDataFrame = xivDataFrame.truncate(after=endDate, before=startDate)
#
# purchaseDataFrame = pd.DataFrame(index=purchaseDates, data=purchasePrices)
# sellDataFrame = pd.DataFrame(index=sellDates, data=sellPrices)
# ax = trimmedXivDataFrame["Adj Close"].plot(title="XIV Purchases", grid=True, figsize=(12,6), alpha=0.5, color="blue")
# trimmedXivDataFrame[xivAdjCloseSMAColumn].plot(ax=ax, grid=True, color="blue", alpha=0.15)
# trimmedVixDataFrame["Adj Close"].plot(ax=ax, grid=True, color="gray", alpha=0.5)
# trimmedVixDataFrame[adjCloseSMATrimmedColumn].plot(ax=ax, grid=True, color="red")
# trimmedVixDataFrame[adjCloseSMAColumn].plot(ax=ax, grid=True, color="brown", alpha = 0.5)
# purchaseDataFrame.plot(ax=ax, grid=True, color="green", style='^', alpha=1)
# sellDataFrame.plot(ax=ax, grid=True, color="red", style='^', alpha=1)
# plt.show()
