# division_error.py

def calculate_average(total, count):
    return total / count


total = 100
count = 0

average = calculate_average(total, count)

print(f"Average: {average}")

# percentage_error.py

def calculate_percentage(completed, total):
    percentage = (completed / total) * 100
    return percentage


completed_tasks = 25
total_tasks = 0

percentage = calculate_percentage(completed_tasks, total_tasks)

print(f"Completion: {percentage} %")

