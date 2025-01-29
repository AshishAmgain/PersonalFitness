import math

def calculate_angle(a, b, c):
    # Calculate vectors from point b to points a and c
    ba = [a[0] - b[0], a[1] - b[1]]
    bc = [c[0] - b[0], c[1] - b[1]]

    # Calculate magnitudes
    magnitude_ba = math.sqrt(ba[0] ** 2 + ba[1] ** 2)
    magnitude_bc = math.sqrt(bc[0] ** 2 + bc[1] ** 2)

    # Check if points are too close together
    if magnitude_ba < 1e-10 or magnitude_bc < 1e-10:
        return 0.0

    # Calculate dot product
    dot_product = ba[0] * bc[0] + ba[1] * bc[1]

    # Calculate cosine angle with bounds check
    cosine_angle = max(min(dot_product / (magnitude_ba * magnitude_bc), 1.0), -1.0)

    # Calculate angle in degrees
    angle = math.degrees(math.acos(cosine_angle))

    return angle