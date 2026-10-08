class NumberNotFoundError(Exception):
    """Raised when the target number is not found in the list."""

    def __init__(self, target: int) -> None:
        """Initialize the exception.

        Args:
            target: The number that was not found.
        """
        self.target = target
        super().__init__(f"Number {target} not found in list")


def find_number(numbers: list[int], target: int) -> int:
    """Find the index of a target number in a list.

    Args:
        numbers: List of numbers to search.
        target: The number to find.

    Returns:
        The index of the target in the list.

    Raises:
        NumberNotFoundError: If target is not in the list.
    """
    if target not in numbers:
        raise NumberNotFoundError(target)
    index = numbers.index(target)
    return index


numbers = [10, 20, 30]
target = 50

try:
    index = find_number(numbers, target)
    print(index)
except NumberNotFoundError as e:
    print(f"Number not found: {e.target}")
