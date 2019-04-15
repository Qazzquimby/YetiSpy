PROGRESS_INTERVALS = [1, 5, 10, 15, 20, 25, 33, 50, 150]


class ProgressPrinter:
    def __init__(self, name, total_values, max_calls_between_prints):
        self.name = name

        self.interval = self._get_interval(total_values, max_calls_between_prints)
        self.calls_between_prints = self._get_calls_between_prints(total_values)

        self.current_num_calls = 0
        self.previous_prints = 0

    def maybe_print(self):
        self.current_num_calls += 1
        if self.current_num_calls >= self.calls_between_prints:
            self._print()
            self.previous_prints += 1
            self.current_num_calls = 0

    def _get_interval(self, total_values, max_calls_between_prints):
        last_interval = PROGRESS_INTERVALS[0]

        for interval in PROGRESS_INTERVALS:
            calls_between_prints = self._get_calls_between_prints_from_interval(total_values,
                                                                                interval)
            if calls_between_prints >= max_calls_between_prints:
                return last_interval
            last_interval = interval
        return PROGRESS_INTERVALS[-1]

    def _get_calls_between_prints(self, total_values):
        calls_between_prints = self._get_calls_between_prints_from_interval(total_values,
                                                                            self.interval)
        return calls_between_prints

    @staticmethod
    def _get_calls_between_prints_from_interval(total_values, interval):
        return total_values * interval / 100

    def _print(self):
        print(f"{self.name} {self.interval * (self.previous_prints + 1)}% complete.")
