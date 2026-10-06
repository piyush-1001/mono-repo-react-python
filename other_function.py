# salary_error.py

def calculate_hourly_salary(monthly_salary, working_days, hours_per_day):
    total_hours = working_days * hours_per_day
    hourly_salary = monthly_salary / total_hours

    return hourly_salary


monthly_salary = 50000
working_days = 0
hours_per_day = 8

salary_per_hour = calculate_hourly_salary(
    monthly_salary,
    working_days,
    hours_per_day,
)

print(f"Hourly Salary: ₹{salary_per_hour}")
