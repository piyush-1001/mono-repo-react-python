def find_number(numbers, target) -> int | None:
    """Return the index of target in numbers, or None when target is absent."""
    return numbers.index(target) if target in numbers else None


if __name__ == "__main__":
    numbers = [10, 20, 30]
    target = 50

    index = find_number(numbers, target)

    print(index)
