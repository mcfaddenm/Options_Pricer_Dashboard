class MovingAverageCrossoverStrategy:
    def __init__(self, short_window, long_window):
        self.short_window = short_window
        self.long_window = long_window

    def generate_positions(self, data):
        data['short_mavg'] = data['close'].rolling(window=self.short_window).mean()
        data['long_mavg'] = data['close'].rolling(window=self.long_window).mean()
        data['position'] = np.where(data['short_mavg'] > data['long_mavg'], 1, -1)
        return data['position']
