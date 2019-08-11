"""Timing diagnostics"""
import time


def timer(function, name=None):
    """Times the given function and prints the results."""
    if not name:
        name = function
    print(f"profiling {name}")
    start = time.time()

    result = function()

    end = time.time()
    print(f"{end - start} seconds")
    return result
