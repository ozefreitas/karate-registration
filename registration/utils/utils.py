def range_decoder(some_range: str):
    some_range = some_range.split("-")
    some_range = range(int(some_range[0]), int(some_range[1]))
    return some_range