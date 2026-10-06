import logging

logger = logging.getLogger(__name__)


def find_number(numbers: list[int], target: int) -> int | None:
    """Return the index of target in numbers, or None if absent."""
    return numbers.index(target) if target in numbers else None


def main() -> int | None:
    """Run the sample lookup, log the outcome, and return the index or None."""
    numbers = [10, 20, 30]
    target = 50

    index = find_number(numbers, target)
    logger.info("find_number(%s, %s) -> %s", numbers, target, index)
    return index


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
