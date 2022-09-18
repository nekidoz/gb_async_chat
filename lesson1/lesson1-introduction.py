from enum import Enum


class Direction(Enum):
    """Direction for iterators and generators
    """
    UP = 1
    DOWN = 2


""" ************************* ITERATOR *****************************"""


class CounterIterator:
    """Iterator class that can iterate integers forward and backward.

    Attributes:
        low - minimum integer value to iterate from (or to), inclusive; if not specified, defaults to 1;
        high -maximum integer value to iterate from (or to), inclusive; if not specified and direction is UP, iterates up infinitely; if not specified and direction is DOWN, raises ValueError;
        direction - iterator direction; if not specified, defaults to UP.
    """
    def __init__(self, low: int = None, high: int = None, direction: Direction = None):
        self.low = low if low else 1
        self.high = high
        self.direction = direction if direction else Direction.UP
        if not high and direction == Direction.DOWN:
            raise ValueError("High value must be specified when iterating down.")
        self.current = self.low - 1 if self.direction == Direction.UP else self.high + 1

    def __iter__(self):
        return self

    def __next__(self):
        if self.direction == Direction.UP:
            if self.high and self.current >= self.high:
                raise StopIteration
            self.current += 1
        else:
            if self.low and self.current <= self.low:
                raise StopIteration
            self.current -= 1
        return self.current


""" ************************* GENERATOR *****************************"""


def counter_generator(low: int = None, high: int = None, direction: Direction = None):
    """Generator function that can iterate integers forward and backward.

    Attributes:
        low - minimum integer value to iterate from (or to), inclusive; if not specified, defaults to 1;
        high -maximum integer value to iterate from (or to), inclusive; if not specified and direction is UP, iterates up infinitely; if not specified and direction is DOWN, raises ValueError;
        direction - iterator direction; if not specified, defaults to UP.
    """
    low = low if low else 1
    direction = direction if direction else Direction.UP
    if not high and direction == Direction.DOWN:
        raise ValueError("High value must be specified when iterating down.")
    current = low - 1 if direction == Direction.UP else high + 1
    while True:
        if direction == Direction.UP:
            if high and current >= high:
                return
            current += 1
        else:
            if low and current <= low:
                return
            current -= 1
        yield current


""" ************************* TEST *****************************"""


def test_iterator(iterator_type):
    print(f"Default iterator output:")
    for index, value in enumerate(iterator_type()):
        print(value, end=" ")
        if index >= 9:
            break
    print("... (infinite)")

    print(f"Iterator(3, 9) output:")
    for value in iterator_type(3, 9):
        print(value, end=" ")
    print()

    print(f"iterator(3, 9, DOWN) output:")
    for value in iterator_type(3, 9, Direction.DOWN):
        print(value, end=" ")
    print()

    print(f"iterator(1, 1) output:")
    for value in iterator_type(1, 1):
        print(value, end=" ")
    print()

    print(f"iterator(1, 1, DOWN) output:")
    for value in iterator_type(1, 1, Direction.DOWN):
        print(value, end=" ")
    print()

    print(f"iterator(9, 3) (boundaries invalid) output:")
    for value in iterator_type(9, 3):
        print(value, end=" ")
    print()

    print(f"iterator(9, 3, DOWN) (boundaries invalid) output:")
    for value in iterator_type(9, 3, Direction.DOWN):
        print(value, end=" ")
    print()


""" ************************* MAIN *****************************"""

if __name__ == "__main__":
    print("\n*** Testing CounterIterator ***\n")
    test_iterator(CounterIterator)
    print("\n*** Testing counter_generator ***\n")
    test_iterator(counter_generator)
