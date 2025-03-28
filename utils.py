class MovingMedianFilter:
    def __init__(self, window_size: int, *, initial_value: float = 0.0):
        assert window_size > 0, "Window size must be positive"
        self.data = [initial_value] * window_size

    def add(self, value):
        # maintains self.data at a fixed size
        self.data.pop(0)
        self.data.append(value)
        return self  # for chaining

    def median(self):
        sorted_data = sorted(self.data)
        mid = len(sorted_data) // 2
        return sorted_data[mid]
