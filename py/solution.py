from typing import Dict, List, Tuple 
from util import Color, Sat, User, Vector3

# Constants
MAX_USERS_PER_SAT = 32  # Maximum users a satellite can handle simultaneously
MIN_BEAM_INTERFERENCE = 10  # Minimum angle in degrees to avoid beam interference
COLORS = [Color.A, Color.B, Color.C, Color.D]  # Available beam colors

# Aliases for clarity
UserID = User
SatelliteId = Sat

def solve(users: Dict[UserID, Vector3], sats: Dict[SatelliteId, Vector3]) -> Dict[UserID, Tuple[SatelliteId, Color]]:
    """
    Solves the beam assignment problem by assigning users to satellites and colors
    while adhering to angle and interference constraints.

    Args:
        users (Dict[UserID, Vector3]): Mapping of user IDs to their 3D positions.
        sats (Dict[SatelliteId, Vector3]): Mapping of satellite IDs to their 3D positions.

    Returns:
        Dict[UserID, Tuple[SatelliteId, Color]]: Mapping of user IDs to their assigned satellite and color.
    """
    solution = {}

    # Initialize User objects with vectors and store them globally
    for user_id in users:
        user_vector = users[user_id]
        User.users[user_id] = User(user_id, user_vector)

    # Initialize Satellite objects with vectors and store them globally
    for satellite_id in sats:
        satellite_vector = sats[satellite_id]
        Satellite.satellites[satellite_id] = Satellite(satellite_id, satellite_vector)

    # First pass: Assign available users to satellites
    for satellite in Satellite.satellites.values():
        for user_id in satellite.available_users:  
            for color in COLORS:
                if satellite.available(user_id, color):  
                    satellite.assign(user_id, color)  
                    solution[user_id] = (satellite.id, color)
                    break  

    # Second pass: Reassign conflicting users to make room for unassigned users
    for satellite in Satellite.satellites.values():
        for user_id in satellite.available_users: 
            for color in COLORS:
                if satellite.can_make_room_for(user_id, color):  
                    reassignments = satellite.make_room_for(user_id, color)    
                    for conflicting_user_id, new_color in reassignments.items():
                        satellite.reassign(conflicting_user_id, new_color)  
                        solution[conflicting_user_id] = (satellite.id, new_color)
                    satellite.assign(user_id, color)  
                    solution[user_id] = (satellite.id, color)
        
    return solution

class User:
    """
    Represents a user in the beam planning system.

    Attributes:
        users (Dict[UserID, User]): Global registry of all users.
        id (UserID): Unique identifier for the user.
        vector (Vector3): The 3D position of the user.
        assigned (bool): Whether the user has been assigned to a satellite.
        color (Color): The color of the beam assigned to the user (if any).
    """
    users = {}

    def __init__(self, id: User, vector: Vector3) -> None:
        self.id = id
        self.vector = vector
        self.assigned = False
        self.color = None

class Satellite:
    """
    Represents a satellite in the beam planning system.

    Attributes:
        satellites (Dict[SatelliteId, Satellite]): Global registry of all satellites.
        id (SatelliteId): Unique identifier for the satellite.
        vector (Vector3): The 3D position of the satellite.
        assignments (List[UserID]): List of user IDs assigned to this satellite.
        visible_users (List[UserID]): List of users visible to this satellite based on beam angle constraints.
    """
    satellites = {}

    def __init__(self, id: Sat, vector: Vector3) -> None:
        self.id = id
        self.vector = vector 
        self.assignments = []  # Track assigned users
        self.visible_users = [
            user_id for user_id, user in User.users.items()
            if self._is_beam_within_45_degrees(user.vector)  # Visibility check
        ]

    @property
    def available_users(self) -> List[UserID]:
        """
        Get the list of users that are visible to this satellite and not yet assigned.

        Returns:
            List[UserID]: List of available user IDs.
        """
        return [
            user_id for user_id in self.visible_users
            if not User.users[user_id].assigned
        ]

    def available(self, user_id, color) -> bool:
        """
        Checks if a user can be assigned to this satellite on a specific color.

        Args:
            user_id (UserID): ID of the user to check.
            color (Color): The color to check.

        Returns:
            bool: True if the user can be assigned without interference, False otherwise.
        """
        return len(self.assignments) < MAX_USERS_PER_SAT and all(
            not self._is_user_within_10_degrees(
                User.users[user_id].vector,
                User.users[other_user_id].vector
            )
            for other_user_id in self.assignments if User.users[other_user_id].color == color
        )

    def assign(self, user_id: User, color: Color) -> None:
        """
        Assigns a user to this satellite on the specified color.

        Args:
            user_id (UserID): ID of the user to assign.
            color (Color): The color of the beam.
        """
        user = User.users[user_id]
        user.assigned = True
        user.color = color
        self.assignments.append(user_id)

    def reassign(self, user_id: User, color: Color) -> None:
        """
        Reassigns a user to a new color on this satellite.

        Args:
            user_id (UserID): ID of the user to reassign.
            color (Color): The new color for the user.
        """
        self._unassign(user_id)
        self.assign(user_id, color)

    def can_make_room_for(self, user_id: User, color: Color) -> bool:
        """
        Checks if conflicts can be resolved to make room for a new user.

        Args:
            user_id (UserID): ID of the new user.
            color (Color): The color to assign to the new user.

        Returns:
            bool: True if all conflicts can be resolved, False otherwise.
        """
        conflicting_users = self._conflicts(user_id, color)
        reassignment_is_feasible = len(conflicting_users) > 0
        for conflicting_user_id in conflicting_users:
            if not any(
                color != other_color
                and self.available(conflicting_user_id, other_color)
                for other_color in COLORS
            ):
                reassignment_is_feasible = False
                break
        return reassignment_is_feasible 
    
    def make_room_for(self, user_id: User, color: Color) -> None:
        """
        Resolves conflicts by reassigning conflicting users to new colors.

        Args:
            user_id (UserID): ID of the new user.
            color (Color): The color for the new user.

        Returns:
            Dict[UserID, Color]: Mapping of conflicting users to their new colors.
        """
        reassignments = {}
        for conflict_user_id in self._conflicts(user_id, color):
            for other_color in COLORS:
                if color == other_color:
                    continue
                if self.available(conflict_user_id, other_color):
                    reassignments[conflict_user_id] = other_color
                    break  
        return reassignments

    def _is_beam_within_45_degrees(self, user: Vector3) -> bool:
        """
        Checks if the beam angle between the user and satellite is within 45 degrees.

        Args:
            user (Vector3): User's 3D position.

        Returns:
            bool: True if the beam angle is within 45 degrees, False otherwise.
        """
        return 180 - user.angle_between(Vector3(0, 0, 0), self.vector) <= 45

    def _is_user_within_10_degrees(self, user_1: Vector3, user_2: Vector3) -> bool:
        """
        Checks if two users are within 10 degrees of each other relative to the satellite.

        Args:
            user_1 (Vector3): Position of the first user.
            user_2 (Vector3): Position of the second user.

        Returns:
            bool: True if the users are within 10 degrees, False otherwise.
        """
        vec1 = user_1 - self.vector 
        vec2 = user_2 - self.vector 

        if vec1.mag() == 0 or vec2.mag() == 0:  # Prevent division by zero
            return False

        return self.vector.angle_between(user_1, user_2) < MIN_BEAM_INTERFERENCE 

    def _conflicts(self, user_id: User, color: Color) -> List[UserID]:
        """
        Identifies users that conflict with the given user and color.

        Args:
            user_id (UserID): ID of the user to check.
            color (Color): The color to check.

        Returns:
            List[UserID]: List of conflicting user IDs.
        """
        return [
            id for id in self.assignments
            if User.users[id].color == color and self._is_user_within_10_degrees(
                User.users[user_id].vector,
                User.users[id].vector
            )
        ]

    def _unassign(self, user_id: User) -> None:
        """
        Unassigns a user from this satellite.

        Args:
            user_id (UserID): ID of the user to unassign.
        """
        for index, id in enumerate(self.assignments):
            if id == user_id:
                self.assignments.pop(index)