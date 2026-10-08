function divide(num, divisor) {
  try {
    if (divisor === 0) {
      throw new Error("Cannot divide by zero"); // Throws exception for 0
    }
    const result = num / divisor;
    return result;
  } catch (error) {
    console.error("Error caught:", error.message);
    return undefined;
  } finally {
    console.log("Execution finished.");
  }
}

// Test the function
console.log(divide(10, 2);  // Output: 5
divide(10, 0);              // Output: Error caught: Cannot divide by zero

