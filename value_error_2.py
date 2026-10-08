"""Number search utilities."""


def find_number(numbers: list[int], target: int) -> int | None:
    try:
        return numbers.index(target)
    except ValueError:
        return None


if __name__ == "__main__":
    numbers = [10, 20, 30]
    target = 50

    index = find_number(numbers, target)

    print(index)
