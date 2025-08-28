import argparse
import sys
import time

def main():
    parser = argparse.ArgumentParser(description="A more advanced example for Guini using the ArgParse section.")

    parser.add_argument(
        '--file',
        type=str,
        help="Path to the input data file."
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=10,
        help="Number of processing iterations to run."
    )
    parser.add_argument(
        '--verbose',
        action='store_true', # This is a boolean flag
        help="Enable verbose output."
    )
    parser.add_argument(
        '--numbers',
        type=str,
        help="A comma-separated string of numbers to process."
    )

    args, unknown = parser.parse_known_args()

    if not args.file:
        print("Error: An input file must be provided via the --file argument.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting processing for file: {args.file}")
    if args.verbose:
        print("Verbose mode is ON.")

    for i in range(args.iterations):
        if args.verbose:
            print(f"  - Iteration {i + 1}/{args.iterations}...")
        time.sleep(0.1) # Simulate work

    if args.numbers:
        try:
            number_list = [int(n.strip()) for n in args.numbers.split(',') if n.strip()]
            print(f"\nProcessing number list: {number_list}")
            print(f"Sum of numbers: {sum(number_list)}")
        except ValueError:
            print(f"\nError: Could not parse numbers from '{args.numbers}'.", file=sys.stderr)

    print("\nProcessing complete.")

if __name__ == "__main__":
    main()