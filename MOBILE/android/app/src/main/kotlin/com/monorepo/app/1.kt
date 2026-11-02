
fun main() {
    println("===== KOTLIN BASIC PROGRAM =====")

    // Variables
    val name = "Rahul"
    var age = 20
    val city = "Ahmedabad"

    println("Name: $name")
    println("Age: $age")
    println("City: $city")

    // Data types
    val number: Int = 100
    val price: Double = 99.50
    val grade: Char = 'A'
    val isStudent: Boolean = true

    println("Number: $number")
    println("Price: $price")
    println("Grade: $grade")
    println("Student: $isStudent")

    // If else
    if (age >= 18) {
        println("You are eligible to vote")
    } else {
        println("You are not eligible to vote")
    }

    // For loop
    println("Counting from 1 to 10")
    for (i in 1..10) {
        println(i)
    }

    // While loop
    var count = 1
    while (count <= 5) {
        println("Count: $count")
        count++
    }

    // When expression
    val day = 3
    when (day) {
        1 -> println("Monday")
        2 -> println("Tuesday")
        3 -> println("Wednesday")
        4 -> println("Thursday")
        5 -> println("Friday")
        else -> println("Weekend")
    }

    // Function calls
    greet("Rahul")
    println("Addition: ${add(10, 20)}")
    println("Subtraction: ${subtract(50, 20)}")
    println("Multiplication: ${multiply(5, 4)}")

    // Array
    val numbers = arrayOf(10, 20, 30, 40, 50)

    println("Array elements:")
    for (n in numbers) {
        println(n)
    }

    // List
    val fruits = listOf("Apple", "Banana", "Mango")
    println("Fruits: $fruits")

    // Mutable list
    val names = mutableListOf("Amit", "Raj")
    names.add("Karan")
    println("Names: $names")

    // Class object
    val student = Student("Rahul", 20)
    student.display()

    // Exception handling
    try {
        val result = 10 / 2
        println("Result: $result")
    } catch (e: Exception) {
        println("Error: ${e.message}")
    }

    // Null safety
    var message: String? = null
    message = "Welcome to Kotlin"
    println(message?.length)

    println("===== PROGRAM COMPLETED =====")
}

fun greet(name: String) {
    println("Hello, $name!")
}

fun add(a: Int, b: Int): Int {
    return a + b
}

fun subtract(a: Int, b: Int): Int {
    return a - b
}

fun multiply(a: Int, b: Int): Int {
    return a * b
}

class Student(val name: String, val age: Int) {
    fun display() {
        println("Student Name: $name")
        println("Student Age: $age")
    }
}
