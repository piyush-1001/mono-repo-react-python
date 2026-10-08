"""Shared exception classes for the project."""


class NumberNotFoundError(Exception):
    """Raised when the target number is not found in the list."""

    def __init__(self, target: int) -> None:
        """Initialize the exception.

        Args:
            target: The number that was not found.
        """
        self.target = target
        super().__init__(f"Number {target} not found in list")
