import sys


def guess_type(value: str) -> str:
    """
    Guesses the data type of a string value.
    Returns 'boolean', 'integer', 'float', or 'string'.
    """
    if value.lower() in ['true', 'false']:
        return 'boolean'
    try:
        int(value)
        return 'integer'
    except ValueError:
        try:
            float(value)
            return 'float'
        except ValueError:
            return 'string'


def main():
    """
    Main function to process command-line arguments.
    """
    print("--- Argument Type Analysis ---")
    # We skip sys.argv[0] because it's the script's own filename
    for arg in sys.argv[1:]:
        guessed_type = guess_type(arg)
        print(f"Argument: '{arg}' -> Guessed Type: {guessed_type}")


if __name__ == "__main__":
    main()