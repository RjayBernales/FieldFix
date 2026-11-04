import pytest
from app.core import Engine
from app.storage import Store


class Clock:
    def __init__(self): self.now = 1793754000.0
    def __call__(self): return self.now
    def advance(self, seconds=2): self.now += seconds


@pytest.fixture
def engine():
    clock = Clock()
    e = Engine(Store(':memory:'), clock)
    yield e
    e.store.close()
