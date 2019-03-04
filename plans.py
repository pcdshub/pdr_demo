import numpy as np

from bluesky.plan_stubs import sleep, trigger_and_read
from bluesky.preprocessors import run_decorator


@run_decorator()
def wait_for_value(det, field, position, atol, delay=0.5):
    # Initial reading
    reading = yield from trigger_and_read(det)
    curr = reading[field]['value']

    # Repeat until the operator responds
    while not np.isclose(curr, position, atol=atol):
        reading = yield from trigger_and_read(det)
        curr = reading[field]['value']
        if delay:
            yield from sleep(delay)
