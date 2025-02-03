# Python Code Examples and Explanations

This repository contains a collection of Python code snippets that demonstrate various concepts such as variable deletion, handling `None` values, global variables, and arithmetic operations. Below, you'll find detailed explanations for each program.

---

## Program 1: Deleting Elements or Variables in Python
Explanation:
Variable Deletion: The del statement is used to delete a variable or an element from a list. When del x is executed, the variable x is removed from memory, and any subsequent reference to it will raise a NameError.

List Reference: When b = a is executed, both a and b reference the same list in memory. Deleting a using del a only removes the reference a, but the list itself remains in memory as long as b still references it.


## Program 2: Handling Variables Without Values
Explanation:
Unassigned Variables: In Python, attempting to use a variable that has not been assigned a value will result in a NameError.

Using None: The None keyword is used to define a variable without assigning it a specific value. It is often used as a placeholder to indicate that a variable exists but has no meaningful value yet.


## Program 3: Global Variables in Functions
Explanation:
Global Variables: Variables defined outside of functions are considered global. To modify a global variable inside a function, you must use the global keyword. Without it, Python would create a new local variable instead of modifying the global one.

Modifying Global Variables: In this example, the modify_global function changes the value of the global variable x from 10 to 2.


## Program 4: Arithmetic Operations and Rounding
Explanation:
Division: The / operator performs floating-point division, while the // operator performs integer division (floor division).

Rounding: The round() function is used to round a floating-point number to a specified number of decimal places. In this example, c is rounded to 2 decimal places, resulting in 3.33.



