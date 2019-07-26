import numpy as np

def movingAvg(x_t,idx):
    # try:
    #     winPos = movingAvg.indecies.index(idx)
    # except ValueError:          # not in list
    #     movingAvg.indecies.extend(idx)
    #     movingAvg.indecies.extend
    if not str(idx) in movingAvg.windows:
        movingAvg.windows[str(idx)] = []
    else:
        if len(movingAvg.windows[str(idx)]) > movingAvg.windowSize:
            movingAvg.windows[str(idx)].pop(0)
    movingAvg.windows[str(idx)].append(x_t)
    return np.mean(movingAvg.windows[str(idx)])
movingAvg.windows = {}
movingAvg.windowSize = 30
