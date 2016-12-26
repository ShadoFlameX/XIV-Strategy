import pandas as pd
import pandas_datareader.data as web
import os

cacheDir = "data_fetcher_cache/"

def fetchData(symbol, startDate, endDate):
    assert symbol
    assert startDate
    assert endDate

    filename = cacheDir + symbol + "_" + startDate.strftime("%Y-%m-%d") + "_" + endDate.strftime("%Y-%m-%d") + ".pic"

    if os.path.exists(filename):
        dataFrame = pd.read_pickle(filename)
    else:
        dataFrame = web.DataReader(symbol, "yahoo", startDate, endDate)
        if not dataFrame.empty:
            dataFrame.to_pickle(filename)

    return dataFrame
