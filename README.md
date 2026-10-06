# Oxygen

Oxygen is a custom interpreted programming language built from scratch in Python.
This repo includes the language, an online playground powered with Pyodide, and a VSCode syntax highlighting extension.

## Why did I make Oxygen?
Oxygen was originally made for the Hack Club Crescent competition (Week 2, Language card)

## Running Oxygen code

To run oxygen code run the main.py file with the file as the first argument, or just main.py for the REPL

### Run a file:

```
main.py fizzbuzz.oxy
```

### Open the REPL

```
main.py
```

The REPL fully supports the language, including code blocks

## How to write in Oxygen?

### Variables & Data Types

Variables are declared by assigning a value. Strings, numbers, and booleans are supported out of the box.

```
name = "Hugo"
age = 15
isAwesome = true
```


### Mutable Strings & Indexing

Unlike many languages, Oxygen allows you to modify strings in place using index assignment:

```
text = "Hello"
text[0] = "J"
print(text) # Output: Jello
```


### Control Flow (if/elif/else)

Conditional logic uses keywords like if, elif, else, and must be closed with an end statement:

```
score = 85

if score >= 90 then
    print("Grade: A")
elif score >= 80 then
    print("Grade: B")
else
    print("Grade: Needs Improvement")
end
```


### Loops

Oxygen supports both for and while loops, closing blocks with end:

```
for i = 1 to 5 do
    print("Count:", i)
end

count = 0
while count < 3 do
    print("While count:", count)
    count = count + 1
end
```


### Functions

Define custom functions using the def keyword. Functions can take parameters and return values:

```
def add(a, b)
    result = a + b
    return result
end

sumValue = add(10, 20)
print("Sum is:", sumValue)
```


## License

This project is licensed under the Apache 2.0 license.
For more details see the LICENSE file

