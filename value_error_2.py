def find_number(numbers: list[int], target: int) -> int | None:
    """Find the index of target in numbers, or None if not found.

    Args:
        numbers: List of integers to search.
        target: Integer value to find.

    Returns:
        The index of target if found, otherwise None.
    """
    try:
        return numbers.index(target)
    except ValueError:
        return None


if __name__ == "__main__":
    numbers = [10, 20, 30]
    target = 50

    index = find_number(numbers, target)

    print(index)
