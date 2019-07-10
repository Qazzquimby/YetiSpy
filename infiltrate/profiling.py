import time


def timer(function, name=None):
    if not name:
        name = function
    print(f"profiling {name}")
    start = time.time()

    result = function()

    end = time.time()
    print(f"{end - start} seconds")
    return result
