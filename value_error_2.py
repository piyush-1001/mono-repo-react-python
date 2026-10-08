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
target = 30  # Fixed: target must exist in numbers list

index = find_number(numbers, target)

print(index)  # Output: 2
