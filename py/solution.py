from typing import Dict, List, Tuple

from util import Color, Sat, User, Vector3
import math

MAX_USERS_PER_SAT = 32

def solve(users: Dict[User, Vector3], sats: Dict[Sat, Vector3]) -> Dict[User, Tuple[Sat, Color]]:
    solution = {}

    colors = {}
    for color in [Color.A, Color.B, Color.C, Color.D]:
        colors[color] = {
            'users': []
        }

    satellites = {}
    for satellite in sats:
        satellites[satellite] = {
            'viable_users': [user for user in users if is_beam_within_45_degrees(users[user], sats[satellite])],
            'assigned_users': []
        }

    user_data = {}
    for user in users:
        user_data[user] = {
            'assigned': False,
        }
    
    for satellite in sats:
        potential_users = [user for user in satellites[satellite]['viable_users'] if not user_data[user]['assigned']]

        for user in potential_users:
            # Attempt to assign the user to a color
            for color in colors.keys():
                # Check interference with all users in the current color bucket
                color_users = [user for user in colors[color]['users'] if user in satellites[satellite]['viable_users']]
                if all(
                    not is_user_within_10_degrees(sats[satellite], users[user], users[color_user])
                    for color_user in color_users
                ) and len(satellites[satellite]['assigned_users']) < MAX_USERS_PER_SAT:
                    # Assign user to satellite and color
                    solution[user] = (satellite, color)
                    colors[color]['users'].append(user)
                    user_data[user]['assigned'] = True
                    satellites[satellite]['assigned_users'].append(user)
                    break  # Stop checking other colors once assigned

    unassigned_users = [user for user, data in user_data.items() if not data['assigned']]
    for user in unassigned_users:
        for satellite in sats:
            if is_beam_within_45_degrees(users[user], sats[satellite]):
                for color in colors.keys():
                    color_users = [user for user in colors[color]['users'] if user in satellites[satellite]['assigned_users']]
                    conflict_count = sum(
                        is_user_within_10_degrees(sats[satellite], users[user], users[color_user])
                        for color_user in color_users
                    )
                    conflict_list = [
                        color_user for color_user in color_users if is_user_within_10_degrees(sats[satellite], users[user], users[color_user])
                    ]
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    # DETERMINE IF REASSIGNMENT IS FEASIBLE
                    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    reassignment_is_feasible = len(conflict_list) > 0
                    reassignments = {}
                    for conflict in conflict_list:
                        reassignment_possible = False
                        for other_color in colors.keys():
                            if color == other_color:
                                continue
                            other_color_user_list = [
                                other_user for other_user in colors[other_color]['users']
                                if conflict in satellites[satellite]['assigned_users']
                            ]

                            # Check if conflict can fit in another color bucket without interference
                            if all(
                                not is_user_within_10_degrees(sats[satellite], users[conflict], users[other_color_user])
                                for other_color_user in other_color_user_list
                            ):
                                reassignments[conflict] = other_color
                                reassignment_possible = True
                                break  # Stop checking other colors once a valid reassignment is found
                        if not reassignment_possible:
                            reassignment_is_feasible = False
                            break  # Stop checking conflicts if one cannot be reassigned
                    if reassignment_is_feasible:
                        for user_to_reassign, color_to_reassign_to in reassignments.items():
                            if len(satellites[satellite]['assigned_users']) < MAX_USERS_PER_SAT:
                                prev_color = solution[user_to_reassign][1]
                                prev_satellite = solution[user_to_reassign][0]
                                solution[user_to_reassign] = (satellite, color_to_reassign_to)
                                colors[prev_color]['users'].remove(user_to_reassign)
                                colors[color_to_reassign_to]['users'].append(user_to_reassign)

                        if len(satellites[satellite]['assigned_users']) < MAX_USERS_PER_SAT:
                            solution[user] = (satellite, color)
                            colors[color]['users'].append(user)
                            user_data[user]['assigned'] = True
                            satellites[satellite]['assigned_users'].append(user) 
                      
                    else:
                        if conflict_count == 0 and len(satellites[satellite]['assigned_users']) < MAX_USERS_PER_SAT:
                            solution[user] = (satellite, color)
                            colors[color]['users'].append(user)
                            user_data[user]['assigned'] = True
                            satellites[satellite]['assigned_users'].append(user) 

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
