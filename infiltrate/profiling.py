"""Timing diagnostics"""
import time


def timer(function, args=None, name=None):
    """Times the given function and prints the results."""
    if args is None:
        args = {}
    if name is None:
        name = function

    print(f"profiling {name}")
    start = time.time()

    result = function(**args)

    end = time.time()
    print(f"{end - start} seconds")
    return result


_start_times = {}
PRINT_TIMINGS = True


def start_timer(name: str):
    """Begins a timer keyed to the given name."""
    start_time = time.time()
    _start_times[name] = start_time


def end_timer(name: str):
    """Ends the timer keyed to the given name. That name must have a running timer."""
    end_time = time.time()
    try:
        start_time = _start_times[name]
    except KeyError:
        raise ValueError(f"{name} was not used in start_timer")
    duration = end_time - start_time
    _start_times.pop(name)
    if PRINT_TIMINGS:
        print("-" * len(_start_times.keys()), f"{name} - {duration} seconds")
