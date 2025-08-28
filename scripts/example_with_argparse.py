import argparse
import glob
import sys

def main():
    parser = argparse.ArgumentParser(description="A script that accepts lists of arguments from Guini.")

    # For a list of numbers, like '1,2,3,4'
    parser.add_argument(
        '--numbers',
        type=str,  # Guini will pass the whole thing as a single string
        help="A comma-separated string of numbers."
    )

    # For a list of files, which could be a wildcard like 'data/*.csv'
    parser.add_argument(
        '--files',
        type=str, # Guini will pass the wildcard/path string
        help="A path pattern for files (e.g., 'folder/*.txt')."
    )

    # Use parse_known_args to ignore any extra arguments Guini might send
    args, unknown = parser.parse_known_args()

    if args.numbers:
        # Split the string by commas and convert each part to an integer
        try:
            number_list = [int(n.strip()) for n in args.numbers.split(',') if n.strip()]
            print(f"Received numbers: {number_list}")
            print(f"Sum of numbers: {sum(number_list)}")
        except ValueError:
            print(f"Error: Could not parse numbers from '{args.numbers}'. Please provide a comma-separated list of integers.", file=sys.stderr)

    if args.files:
        # Use the glob module to expand the wildcard pattern into a list of files
        file_list = glob.glob(args.files)
        if not file_list:
            print(f"Warning: No files found matching pattern '{args.files}'")
        else:
            print(f"Found {len(file_list)} files matching '{args.files}':")
            for f in file_list:
                print(f" - {f}")

if __name__ == "__main__":
    main()