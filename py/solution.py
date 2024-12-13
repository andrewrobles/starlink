from typing import Dict, List, Tuple

from util import Color, Sat, User, Vector3
import math

def solve(users: Dict[User, Vector3], sats: Dict[Sat, Vector3]) -> Dict[User, Tuple[Sat, Color]]:
    colors = [Color.A, Color.B, Color.C, Color.D]
    solution = {}
    color_buckets = {Color.A: [], Color.B: [], Color.C: [], Color.D: []}

    # OPTIMIZATION TO SORT USERS BY NUMBER OF SATS COMPATIBLE
    user_rank = {}
    unsorted_users = [user for user in users.keys()]
    for user in unsorted_users:
        user_rank[user] = 0
        for sat in sats:
            if is_beam_within_45_degrees(users[user], sats[sat]):
                user_rank[user] += 1
    
    # Order the users by rank by least to greatest
    sorted_users = sorted(unsorted_users, key=lambda user:-user_rank[user])

    for sat, sat_pos in sats.items():
        # Find potential users
        potential_users = [
            user for user in sorted_users
            if user not in solution and is_beam_within_45_degrees(users[user], sat_pos)
        ]

        for user in potential_users:
            assigned = False  # Track if user is assigned

            # Attempt to assign the user to a color
            for color in colors:
                # Check interference with all users in the current color bucket
                if all(
                    not is_user_within_10_degrees(sat_pos, users[user], users[color_user])
                    for color_user in color_buckets[color]
                ):
                    # Assign user to satellite and color
                    solution[user] = (sat, color)
                    color_buckets[color].append(user)
                    assigned = True
                    break  # Stop checking other colors once assigned

    return solution


def is_beam_within_45_degrees(user_position, satellite_position):
    """
    Determines if a satellite's beam serving a user is within 45 degrees of vertical
    from the user's perspective.
    """
    # Calculate the vector from the user to the satellite
    user_to_satellite = satellite_position - user_position
    
    # Calculate the dot product of user_position and user_to_satellite
    dot_product = user_position.dot(user_to_satellite)
    
    # Calculate magnitudes of the vectors
    user_magnitude = user_position.mag()
    satellite_magnitude = user_to_satellite.mag()
    
    # Avoid division by zero
    if user_magnitude == 0 or satellite_magnitude == 0:
        return False
    
    # Calculate the cosine of the angle
    cos_theta = dot_product / (user_magnitude * satellite_magnitude)
    
    # Clamp the value to account for floating-point precision issues
    cos_theta = max(min(cos_theta, 1.0), -1.0)
    
    # Define a small epsilon for floating-point comparison
    epsilon = 1e-9
    threshold = math.sqrt(2) / 2
    
    # Check if cos_theta is within the threshold, allowing for small tolerance
    return cos_theta >= threshold - epsilon

def is_user_within_10_degrees(sat, user1, user2):
    """
    Determines if the angle between the beams from the satellite to two users is within 10 degrees.

    Args:
        sat (Vector3): The satellite position.
        user1 (Vector3): Position of the first user.
        user2 (Vector3): Position of the second user.

    Returns:
        bool: True if the angle is within 10 degrees, False otherwise.
    """
    # Calculate the vectors from the satellite to each user
    vec1 = user1 - sat 
    vec2 = user2 - sat 
    
    # Calculate the dot product of the vectors
    dot_product = vec1.dot(vec2)
    
    # Calculate the magnitudes of the vectors
    magnitude1 = vec1.mag()
    magnitude2 = vec2.mag()
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return False

    # Calculate the cosine of the angle between the vectors
    cos_theta = dot_product / (magnitude1 * magnitude2)
    
    # Clamp cos_theta to account for floating-point precision issues
    cos_theta = max(min(cos_theta, 1.0), -1.0)
    
    # Calculate the angle in degrees
    angle_in_degrees = math.degrees(math.acos(cos_theta))
    
    # Return True if the angle is within 10 degrees
    return angle_in_degrees <= 10
