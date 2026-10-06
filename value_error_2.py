def find_number(numbers: list[int], target: int) -> int | None:
    """Return the index of target in numbers, or None if absent."""
    return numbers.index(target) if target in numbers else None


numbers = [10, 20, 30]
target = 50

index = find_number(numbers, target)

print(index)
