from typing import Optional


def divide(num: float, divisor: float) -> Optional[float]:
    """Divide two numbers.

    Args:
        num: The numerator.
        divisor: The divisor.

    Returns:
        The result of division, or None if divisor is zero.
    """
    try:
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        result = num / divisor
        return result
    except ValueError as error:
        print(f"Error caught: {error}")
        return None
    finally:
        print("Execution finished.")


# Test the function
print(divide(10, 2))  # Output: 5.0
print(divide(10, 0))  # Output: Error caught: Cannot divide by zero, None
