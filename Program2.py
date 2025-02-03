# Defining a variable without assigning a value
a

NameError: name 'a' is not defined

a = None  # Default value set to None
if a is None:
    print("a has no value")
else:
    print(a)

