def find_number(numbers, target) -> int | None:
    return numbers.index(target) if target in numbers else None


numbers = [10, 20, 30]
target = 50

index = find_number(numbers, target)

print(index)
