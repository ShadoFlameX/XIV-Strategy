from enum import Enum
import math
import numpy as np

class MetricType(Enum):
    zscore = 1
    movingAvg = 2
    deltaDiff = 3
    deltaPct = 4
    log = 5
    logLog = 6


def addComputedMetricColumn(dataFrame, metricType, inputColumn="", movingAvgWindow=0):
    if metricType is MetricType.zscore:
        mean = dataFrame[inputColumn].mean()
        stdDeviation = dataFrame[inputColumn].std()
        zScoreColumnName = inputColumn + " Z-Score"
        dataFrame[zScoreColumnName] = (dataFrame[inputColumn] - mean) / stdDeviation

    elif metricType is MetricType.movingAvg:
        assert movingAvgWindow > 0
        newColumnName = inputColumn + " " + str(movingAvgWindow) + "d Avg"
        dataFrame[newColumnName] = np.round(dataFrame[inputColumn].rolling(window=movingAvgWindow, center=False).median(), 2)

    elif metricType is MetricType.deltaDiff:
        # Calculate daily $ & percentage change
        dataFrame[inputColumn + " Delta $"] = dataFrame[inputColumn].diff()

    elif metricType is MetricType.deltaPct:
        # Calculate daily $ & percentage change
        dataFrame[inputColumn + " Delta %"] = dataFrame[inputColumn].pct_change()

    elif metricType is MetricType.log:
        dataFrame[inputColumn + " log"] = dataFrame[inputColumn].apply(lambda x: math.log(x))
