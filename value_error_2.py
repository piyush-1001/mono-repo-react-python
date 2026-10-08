def find_number(numbers, target):
    index = numbers.index(target)
    return index


numbers = [10, 20, 30]
target = 50

index = find_number(numbers, target)

print(index)
