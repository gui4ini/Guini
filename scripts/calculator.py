import sys

if len(sys.argv) > 2:
    try:
        num1 = float(sys.argv[1])
        num2 = float(sys.argv[2])
        result = num1 + num2
        print(f"The sum of {num1} and {num2} is: {result}")
    except (ValueError, IndexError):
        print("Error: Please provide two numbers as arguments.")
else:
    print("Usage: python calculator.py <num1> <num2>")
