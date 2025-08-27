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
    worker_processes = 0  # 0 means auto-detect
    max_cpu_percentage = 100  # 100 means no limit

    # Get arguments from the command line (passed by the GUI)
    if len(sys.argv) > 1:
        num_to_check = int(sys.argv[1])
    if len(sys.argv) > 2:
        worker_processes = int(sys.argv[2])
    if len(sys.argv) > 3:
        max_cpu_percentage = int(sys.argv[3])

    # Generate a list of large numbers to check for primality
    start_num = 100_000_000
    numbers = range(start_num, start_num + num_to_check)

    # Determine the number of workers to use
    available_cpus = os.cpu_count() or 1  # os.cpu_count() can be None

    # Calculate the absolute limit based on the percentage
    if 1 <= max_cpu_percentage < 100:
        cpu_limit = max(1, int(available_cpus * (max_cpu_percentage / 100.0)))
        limit_msg = f"capped at {max_cpu_percentage}%"
    else:
        cpu_limit = available_cpus
        limit_msg = "no limit"

    if worker_processes > 0:
        num_workers_to_use = worker_processes
    else:
        num_workers_to_use = available_cpus  # Auto mode

    num_workers_to_use = min(num_workers_to_use, cpu_limit)

    print(f"Checking {num_to_check} numbers for primes starting from {start_num}.")
    print(f"System has {available_cpus} CPUs. Using {num_workers_to_use} worker processes ({limit_msg}).")
    start_time = time.time()

    # Create a pool of worker processes
    with multiprocessing.Pool(processes=num_workers_to_use) as pool:
        results = pool.map(find_prime_task, numbers)

    for result in results:
        if result:
            print(result)

    end_time = time.time()
    print(f"\n--- Finished in {end_time - start_time:.2f} seconds ---")

