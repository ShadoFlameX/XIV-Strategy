from multiprocessing import Process
import datetime
import pandas as pd
import pandas_datareader.data as web # Package and modules for importing data; this code may change depending on pandas version
import matplotlib.pyplot as plt

start = datetime.datetime(1900,1,1)
end = datetime.datetime(2016,12,31)

vixDataFrame = web.DataReader("^VIX", "yahoo", start, end)

# vixDataFrame["Adj Close"].plot(title="^VIX", grid=True, figsize=(12,6), alpha=0.75, color="blue")

# vixDataFrame["Close"].plot(title="^VIXY", grid=True, figsize=(12,6), alpha=0.75, color="blue")


print("Hello")



fig, axes = plt.subplots(nrows=2, ncols=1)
fig.subplots_adjust(hspace=0.5)
vixDataFrame["Adj Close"].plot(ax=axes[0], title="^VIX", grid=True, figsize=(8,6), alpha=0.75, color="blue")
vixDataFrame["Close"].plot(ax=axes[1], title="^VIXY", grid=True, figsize=(10,6), alpha=0.75, color="blue")


plt.show()