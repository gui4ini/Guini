import sys
import numpy as np
import matplotlib.pyplot as plt

def format_polynomial_string(coeffs):
    """Formats a list of coefficients into a readable polynomial string."""
    degree = len(coeffs) - 1
    poly_str = []
    for i, coeff in enumerate(coeffs):
        if coeff == 0:
            continue

        power = degree - i

        sign = " + " if coeff > 0 else " - "

        abs_coeff = abs(coeff)
        if abs_coeff == 1 and power != 0:
            coeff_str = ""
        else:
            coeff_str = f"{abs_coeff:g}"

        if power > 1:
            var_str = f"x^{power}"
        elif power == 1:
            var_str = "x"
        else: # power == 0
            var_str = ""

        term = f"{coeff_str}{var_str}" if coeff_str and var_str else f"{coeff_str or var_str}"
        poly_str.append(sign + term)

    if not poly_str:
        return "y = 0"

    result = "".join(poly_str).lstrip(" +")
    return f"y = {result.strip()}"

def plot_polynomial(coeffs, x_min, x_max, num_points):
    """
    Generates and saves a plot of a polynomial given its coefficients.
    """
    # Create a polynomial function from the coefficients
    p = np.poly1d(coeffs)

    # Generate x values for the plot
    x = np.linspace(x_min, x_max, num_points)
    y = p(x)

    # Create the plot
    plt.figure(figsize=(10, 6))
    label_str = format_polynomial_string(coeffs)
    plt.plot(x, y, label=label_str)
    plt.title("Polynomial Plot")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.grid(True)
    plt.legend()
    plt.axhline(0, color='black', linewidth=0.5)
    plt.axvline(0, color='black', linewidth=0.5)
    plt.show(block=True)

if __name__ == "__main__":
    # Default test case when run with no arguments
    if len(sys.argv) == 1:
        print("No arguments provided. Running a test case.")
        print("Usage: python plot_polyn.py <xmin> <xmax> <num_points> <coef_0> <coef_1> ... <coef_n>")
        coefficients = [1.0, 1.0, 1.0, 1.0]
        # Use default plot parameters for the test case
        plot_polynomial(coefficients, x_min=-10, x_max=10, num_points=400)
    # Check for minimum number of arguments for a custom run
    elif len(sys.argv) < 5: # At least xmin, xmax, num_points, and one coefficient
        print("Usage: python plot_polyn.py <xmin> <xmax> <num_points> <coef_0> <coef_1> ... <coef_n>")
        sys.exit(1)
    # Custom run with user-provided arguments
    else:
        try:
            x_min = float(sys.argv[1])
            x_max = float(sys.argv[2])
            num_points = int(sys.argv[3])
            # Read coefficients from lowest degree (c0) to highest (cn)
            user_coeffs = [float(c) for c in sys.argv[4:]]
            # Reverse the list for numpy and the formatting function, which expect highest degree first
            coeffs_for_numpy = user_coeffs[::-1]
            plot_polynomial(coeffs_for_numpy, x_min, x_max, num_points)
        except ValueError:
            print("Error: xmin, xmax, num_points, and all coefficients must be valid numbers.")
            sys.exit(1)