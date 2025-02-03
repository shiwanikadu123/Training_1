# Python Code Examples and Explanations

This repository contains a collection of Python code snippets that demonstrate various concepts such as variable deletion, handling `None` values, global variables, and arithmetic operations. Below, you'll find detailed explanations for each program.

---

## Program 1: Deleting Elements or Variables in Python
Explanation:
Variable Deletion: The del statement is used to delete a variable or an element from a list. When del x is executed, the variable x is removed from memory, and any subsequent reference to it will raise a NameError.

List Reference: When b = a is executed, both a and b reference the same list in memory. Deleting a using del a only removes the reference a, but the list itself remains in memory as long as b still references it.
