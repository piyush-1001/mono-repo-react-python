def find_number(numbers: list, target) -> int | None:
    """Find the index of target in numbers list.

    Args:
        numbers: List of numbers to search.
        target: Value to find.

    Returns:
        Index of target if found, None otherwise.
    """
    try:
        return numbers.index(target)
    except ValueError:
        return None


numbers = [10, 20, 30]
target = 20

index = find_number(numbers, target)

if index is not None:
    print(index)
