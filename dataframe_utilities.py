import math
import numpy as np
from scipy import stats

MetricTypeZScore = "zScore"
MetricTypeMovingAvg = "movingAvg"
MetricTypeTrimmedMovingAvg = "trimmedMovingAvg"
MetricTypeDeltaDiff = "deltaDiff"
MetricTypeDeltaPct = "deltaPct"
MetricTypeLog = "log"

def addComputedMetricColumn(dataFrame=None, metricType=None, inputColumn="", movingAvgWindow=0, highTrimPercent=0.0):
    if metricType == MetricTypeZScore:
        mean = dataFrame[inputColumn].mean()
        stdDeviation = dataFrame[inputColumn].std()
        newColumnName = inputColumn + " Z-Score"
        dataFrame[newColumnName] = (dataFrame[inputColumn] - mean) / stdDeviation
        return newColumnName

    elif metricType == MetricTypeMovingAvg:
        assert movingAvgWindow > 0
        newColumnName = inputColumn + " " + str(movingAvgWindow) + "d Avg"
        dataFrame[newColumnName] = np.round(dataFrame[inputColumn].rolling(window=movingAvgWindow, center=False).median(), 4)
        return newColumnName

    elif metricType == MetricTypeTrimmedMovingAvg:
        assert movingAvgWindow > 0
        newColumnName = inputColumn + " " + str(movingAvgWindow) + "d Trim Avg"

        newColumnValues = np.full(len(dataFrame.index), np.nan)

        for idx in range(movingAvgWindow, len(dataFrame.index)):
            windowStartDate = dataFrame.index[idx - movingAvgWindow]
            windowEndDate = dataFrame.index[idx]
            values = np.array(dataFrame.ix[windowStartDate:windowEndDate,:][inputColumn].values)
            newColumnValues[idx] = np.median(stats.trim1(values, highTrimPercent, tail="right"))

        dataFrame[newColumnName] = newColumnValues
        return newColumnName

    elif metricType == MetricTypeDeltaDiff:
        # Calculate daily $ & percentage change
        newColumnName = inputColumn + " Delta $"
        dataFrame[newColumnName] = dataFrame[inputColumn].diff()
        return newColumnName

    elif metricType == MetricTypeDeltaPct:
        # Calculate daily $ & percentage change
        newColumnName = inputColumn + " Delta %"
        dataFrame[newColumnName] = dataFrame[inputColumn].pct_change()
        return newColumnName

    elif metricType == MetricTypeLog:
        newColumnName = inputColumn + " log"
        dataFrame[newColumnName] = dataFrame[inputColumn].apply(lambda x: math.log(x))
        return newColumnName
