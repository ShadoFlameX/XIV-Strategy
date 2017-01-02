from enum import Enum
import math
import numpy as np
from scipy import stats

class MetricType(Enum):
    zscore = 1
    movingAvg = 2
    trimmedMovingAvg = 3
    deltaDiff = 4
    deltaPct = 5
    log = 6
    logLog = 7


def addComputedMetricColumn(dataFrame, metricType, inputColumn="", movingAvgWindow=0, highTrimPercent=0.0):
    if metricType is MetricType.zscore:
        mean = dataFrame[inputColumn].mean()
        stdDeviation = dataFrame[inputColumn].std()
        newColumnName = inputColumn + " Z-Score"
        dataFrame[newColumnName] = (dataFrame[inputColumn] - mean) / stdDeviation
        return newColumnName

    elif metricType is MetricType.movingAvg:
        assert movingAvgWindow > 0
        newColumnName = inputColumn + " " + str(movingAvgWindow) + "d Avg"
        dataFrame[newColumnName] = np.round(dataFrame[inputColumn].rolling(window=movingAvgWindow, center=False).median(), 4)
        return newColumnName

    elif metricType is MetricType.trimmedMovingAvg:
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

    elif metricType is MetricType.deltaDiff:
        # Calculate daily $ & percentage change
        newColumnName = inputColumn + " Delta $"
        dataFrame[newColumnName] = dataFrame[inputColumn].diff()
        return newColumnName

    elif metricType is MetricType.deltaPct:
        # Calculate daily $ & percentage change
        newColumnName = inputColumn + " Delta %"
        dataFrame[newColumnName] = dataFrame[inputColumn].pct_change()
        return newColumnName

    elif metricType is MetricType.log:
        newColumnName = inputColumn + " log"
        dataFrame[newColumnName] = dataFrame[inputColumn].apply(lambda x: math.log(x))
        return newColumnName
