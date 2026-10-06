"""Number lookup utilities."""


def find_number(numbers: list[int], target: int) -> int | None:
    """Return the index of target in numbers, or None when target is absent.

    Args:
        numbers: List of numbers to search through.
        target: Number to look for.

    Returns:
        Zero-based index of the first match, or None if target is not present.
    """
    try:
        return numbers.index(target)
    except ValueError:
        return None


def main() -> None:
    """Run the demo lookup and print the result."""
    numbers = [10, 20, 30]
    target = 50

    index = find_number(numbers, target)

    if index is None:
        print(f"{target} not found in {numbers}")
    else:
        print(f"{target} found at index {index}")


if __name__ == "__main__":
    main()
