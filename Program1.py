# Delete an list of element in python
x = 10
print(x)  # Output: 10
del x
print(x)  # This will raise a NameError, since 'x' is deleted


a = [1, 2, 3]
b = a  # b references the same list as a
del a  # Now 'a' is deleted, but the list is still referenced by 'b'
print(b)  # Output: [1, 2, 3]
