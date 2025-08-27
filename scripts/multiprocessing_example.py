import sys
import time
import multiprocessing
import os


def is_prime(n):
    """
    A simple (and not very efficient) function to check if a number is prime.
    This is just to simulate a CPU-intensive task.
    """
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def find_prime_task(number):
    """
    The task for each worker process. It finds a prime and returns a status.
    """
    if is_prime(number):
        # We use os.getpid() to show that different processes are doing the work.
        return f"Worker PID: {os.getpid()} | Found prime: {number}"
    return None


if __name__ == "__main__":
    # This guard is CRITICAL for multiprocessing to work correctly.

    print("--- Multiprocessing Script Started ---")

    # Default values
    num_to_check = 10000
    worker_processes = None  # None lets multiprocessing decide the optimal number

    # Get arguments from the command line (passed by the GUI)
    if len(sys.argv) > 1:
        num_to_check = int(sys.argv[1])
    if len(sys.argv) > 2 and int(sys.argv[2]) > 0:
        worker_processes = int(sys.argv[2])

    # Generate a list of large numbers to check for primality
    start_num = 100_000_000
    numbers = range(start_num, start_num + num_to_check)

    print(f"Checking {num_to_check} numbers for primes starting from {start_num}.")
    print(f"Using {worker_processes or 'default'} worker processes.")
    start_time = time.time()

    # Create a pool of worker processes
    with multiprocessing.Pool(processes=worker_processes) as pool:
        results = pool.map(find_prime_task, numbers)

    for result in results:
        if result:
            print(result)

    end_time = time.time()
    print(f"\n--- Finished in {end_time - start_time:.2f} seconds ---")