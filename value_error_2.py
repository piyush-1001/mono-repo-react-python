"""Number search utilities."""


def find_number(numbers: list[int], target: int) -> int | None:
    try:
        return numbers.index(target)
    except ValueError:
        return None


def main() -> None:
    """Run demo lookup."""
    print(find_number([10, 20, 30], 50))


if __name__ == "__main__":
    main()
