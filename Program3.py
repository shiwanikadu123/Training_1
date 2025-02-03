x = 10  # Global variable

def modify_global():
    global x  # Use the global variable x
    x = 2  # Modify the global variable

modify_global()
print(x)  # Output: 2
