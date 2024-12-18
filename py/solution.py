from typing import Dict, List, Tuple

from util import Color, Sat, User, Vector3
import math

COLORS = [Color.A, Color.B, Color.C, Color.D]

def solve(users: Dict[User, Vector3], sats: Dict[Sat, Vector3]) -> Dict[User, Tuple[Sat, Color]]:
    """
    Solves the beam assignment problem by assigning users to satellites and beam colors 
    while adhering to constraints on beam angles and interference.

    Args:
        users (Dict[User, Vector3]): A dictionary mapping user IDs to their 3D coordinates.
        sats (Dict[Sat, Vector3]): A dictionary mapping satellite IDs to their 3D coordinates.

    Returns:
        Dict[User, Tuple[Sat, Color]]: A dictionary mapping user IDs to their assigned satellite ID 
        and beam color.
    """
    solution = {}

    for satellite_id in sats:
        Satellite.satellites[satellite_id] = Satellite(satellite_id, sats, users)

    for user_id in users:
        User.users[user_id] = User(user_id)

    for satellite_id, satellite in Satellite.satellites.items():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if satellite.available(user=user_id, color=color):
                    solution[user_id] = (satellite_id, color)
                    User.users[user_id].assigned = True
                    satellite.assign(user_id, color)
                    break  

    for satellite_id, satellite in Satellite.satellites.items():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if satellite.can_make_room_for(user_id, color):
                    reassignments = satellite.make_room_for(user_id, color)
                    for user_to_reassign, color_to_reassign_to in reassignments.items():
                        if satellite.available():
                            solution[user_to_reassign] = (satellite_id, color_to_reassign_to)
                            satellite.unassign(user_to_reassign)
                            satellite.assign(user_to_reassign, color_to_reassign_to)
                    solution[user_id] = (satellite_id, color)
                    User.users[user_id].assigned = True
                    satellite.assign(user_id, color)
                      
    return solution

MAX_USERS_PER_SAT = 32
MIN_BEAM_INTERFERENCE = 10

class User:
    """
    Represents a user in the beam assignment problem.

    Attributes:
        users (Dict[int, User]): A class-level dictionary storing all user instances by ID.
        assigned (bool): Indicates whether the user has been assigned to a satellite.
    """
    users = {}

    def __init__(self, id):
        """
        Initializes a User instance.

        Args:
            id (int): The unique ID of the user.
        """
        self.assigned = False

class Satellite:
    """
    Represents a satellite in the beam assignment problem.

    Attributes:
        satellites (Dict[int, Satellite]): A class-level dictionary storing all satellite instances by ID.
        id (int): The unique ID of the satellite.
        vector (Vector3): The 3D coordinate of the satellite.
        users (Dict[User, Vector3]): A dictionary mapping user IDs to their 3D coordinates.
        assignments (List[Dict]): A list of dictionaries containing user and color assignments.
    """

    satellites = {}

    def __init__(self, id, satellites, users):
        """
        Initializes a Satellite instance.

        Args:
            id (int): The unique ID of the satellite.
            satellites (Dict[Sat, Vector3]): A dictionary of satellite coordinates.
            users (Dict[User, Vector3]): A dictionary of user coordinates.
        """
        self.id = id
        self.vector = satellites[id] 
        self.users = users
        self.assignments = []

    @property
    def viable_users(self):
        """
        Gets the list of users that are viable for this satellite based on beam constraints.

        Returns:
            List[User]: A list of user IDs that are not assigned and whose beams fall within 45 degrees of the satellite.
        """
        return [user_id for user_id in self.users if not User.users[user_id].assigned and self.is_beam_within_45_degrees(self.users[user_id], self.vector)]

    def available(self, **kwargs):
        """
        Checks if the satellite has available beams for a new user and color.

        Args:
            **kwargs: 
                - user (int): The user ID to check.
                - color (Color): The color to check.

        Returns:
            bool: True if the satellite has capacity and the new user does not interfere 
            with existing beams of the same color.
        """
        if 'user' in kwargs and 'color' in kwargs:
            return len(self.assignments) < MAX_USERS_PER_SAT and all(
            not self.is_user_within_10_degrees(self.vector, self.users[kwargs['user']], self.users[assignment['user']])
            for assignment in self.assignments if assignment['color'] == kwargs['color']
        )

        return len(self.assignments) < MAX_USERS_PER_SAT

    def conflicts(self, user, color):
        """
        Identifies users in conflict with the given user for a specific beam color.

        Args:
            user (int): The user ID to check.
            color (Color): The beam color to check.

        Returns:
            List[int]: A list of user IDs that conflict with the specified user on this color.
        """
        return [
            assignment['user'] for assignment in self.assignments
            if assignment['color'] == color and self.is_user_within_10_degrees(self.vector, self.users[user], self.users[assignment['user']])
        ]

    def assign(self, user, color):
        """
        Assigns a user to a specific beam color on this satellite.

        Args:
            user (int): The user ID to assign.
            color (Color): The beam color to assign.
        """
        self.assignments.append({ 'user': user, 'color': color })

    def unassign(self, user):
        """
        Removes a user from the satellite's assignments.

        Args:
            user (int): The user ID to unassign.
        """
        for index, assignment in enumerate(self.assignments):
            if assignment['user'] == user:
                self.assignments.pop(index)

    def can_make_room_for(self, user_id, color):
        """
        Checks if conflicts can be resolved to make room for the specified user and color.

        Args:
            user_id (int): The user ID to add.
            color (Color): The beam color to add.

        Returns:
            bool: True if all conflicts can be resolved through reassignment.
        """
        conflicts = self.conflicts(user_id, color)
        reassignment_is_feasible = len(conflicts) > 0
        for conflict in conflicts:
            reassignment_possible = False
            for other_color in COLORS:
                if color == other_color:
                    continue
                if self.available(user=conflict, color=other_color):
                    reassignment_possible = True
                    break
            if not reassignment_possible:
                reassignment_is_feasible = False
                break
        return reassignment_is_feasible 
    
    def make_room_for(self, user_id, color):
        """
        Resolves conflicts to make room for the specified user and color.

        Args:
            user_id (int): The user ID to add.
            color (Color): The beam color to add.

        Returns:
            Dict[int, Color]: A dictionary mapping conflicting user IDs to their new colors.
        """
        conflicts = self.conflicts(user_id, color)
        reassignment_is_feasible = len(conflicts) > 0
        reassignments = {}
        for conflict in conflicts:
            reassignment_possible = False
            for other_color in COLORS:
                if color == other_color:
                    continue

                if self.available(user=conflict, color=other_color):
                    reassignments[conflict] = other_color
                    reassignment_possible = True
                    break  
            if not reassignment_possible:
                reassignment_is_feasible = False
                break  
        return reassignments

    def is_beam_within_45_degrees(self, user, satellite):
        """
        Checks if the beam angle between the user and satellite is within 45 degrees.

        Args:
            user (Vector3): The user's position vector.
            satellite (Vector3): The satellite's position vector.

        Returns:
            bool: True if the beam angle is within 45 degrees, False otherwise.
        """
        return 180 - user.angle_between(Vector3(0, 0, 0), satellite) <= 45

    def is_user_within_10_degrees(self, satellite, user_1, user_2):
        """
        Checks if two users are within 10 degrees of each other with respect to the satellite.

        Args:
            satellite (Vector3): The satellite's position vector.
            user_1 (Vector3): The first user's position vector.
            user_2 (Vector3): The second user's position vector.

        Returns:
            bool: True if the users are within 10 degrees of each other, False otherwise.
        """
        vec1 = user_1 - satellite 
        vec2 = user_2 - satellite

        if vec1.mag() == 0 or vec2.mag() == 0:
            return False

        return satellite.angle_between(user_1, user_2) < MIN_BEAM_INTERFERENCE 
