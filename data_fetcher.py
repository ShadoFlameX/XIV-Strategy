import pandas as pd
import pandas_datareader.data as web
import urllib, os, re

CACHE_DIR = "data_fetcher_cache/"
YAHOO_TODAY = "http://download.finance.yahoo.com/d/quotes.csv?s=%s&e=.csv&f=d1t1ohgl1vl1"

def fetchData(symbol, startDate, endDate, fetchLatestQuote=False):
    assert symbol
    assert startDate
    assert endDate

    filename = os.path.dirname(os.path.realpath(__file__)) + "/" + CACHE_DIR + symbol + "_" + startDate.strftime("%Y-%m-%d") + "_" + endDate.strftime("%Y-%m-%d") + ".pckl"

    if os.path.exists(filename):
        dataFrame = pd.read_pickle(filename)
    else:
        dataFrame = web.DataReader(symbol, "yahoo", startDate, endDate)
        if not dataFrame.empty:
            dataFrame.to_pickle(filename)

    if fetchLatestQuote:
        currentQuoteRow = fetch_current_quote(symbol=symbol)
        if currentQuoteRow.index >= dataFrame.index[-1]:
            if currentQuoteRow.index[-1].date() == dataFrame.index[-1].date():
                # if both quotes are for the first date, update history's last record.
                dataFrame.iloc[-1] = currentQuoteRow.iloc[-1]
            else:
                dataFrame = dataFrame.append(currentQuoteRow)

    return dataFrame

def fetch_current_quote(symbol=None):
    url = YAHOO_TODAY % symbol
    new_quote = pd.read_csv(url, names=[u'Date', u'Time', u'Open', u'High', u'Low', u'Close', u'Volume', u'Adj Close'])
    stamp = pd.to_datetime(new_quote.Date)
    new_quote.index = stamp
    row = new_quote.iloc[:, 2:]

    googleQuote = fetch_current_quote_google(symbol)
    if googleQuote is not None:
        row['Adj Close'] = googleQuote

    return row

def fetch_current_quote_google(symbol):
    quote = None

    symbol = symbol.replace("^", ":") # Google expects index lookups to use colon
    url = "http://www.google.com/finance?&q="
    txt = urllib.urlopen(url + symbol).read()
    k = re.search('id="ref_(.*?)">(.*?)<', txt)
    if k:
        tmp = k.group(2)
        quote = convert_to_float(tmp.replace(',', ''))
    else:
        print("Google real-time look-up failed!")

    return quote

def convert_to_float(s):
    value = None

    try:
        value = float(s)
    except ValueError:
        print("Could not convert to float: %s", s)

    return value