from typing import Dict, List, Tuple 

from util import Color, Sat, User, Vector3

MAX_USERS_PER_SAT = 32
MIN_BEAM_INTERFERENCE = 10
COLORS = [Color.A, Color.B, Color.C, Color.D]

UserID = User
SatelliteId = Sat

def solve(users: Dict[UserID, Vector3], sats: Dict[SatelliteId, Vector3]) -> Dict[UserID, Tuple[SatelliteId, Color]]:

    solution = {}

    # TODO: move users and satellites back into the static methods for each class
    Database.load(users, sats)

    for satellite in Database.satellites.values():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if satellite.available(user_id=user_id, color=color):
                    satellite.assign(user_id, color)
                    solution[user_id] = (satellite.id, color)
                    break  

    for satellite in Database.satellites.values():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if satellite.can_make_room_for(user_id, color):
                    reassignments = satellite.make_room_for(user_id, color)
                    for conflicting_user_id, new_color in reassignments.items():
                        satellite.reassign(conflicting_user_id, new_color)
                        solution[conflicting_user_id] = (satellite.id, new_color)
                    satellite.assign(user_id, color)
                    solution[user_id] = (satellite.id, color)
        
    return solution

class Database:
    users = {}
    satellites = {}

    @classmethod
    def load(self, users: Dict[User, Vector3], sats: Dict[Sat, Vector3]) -> None:
        for user_id in users:
            user_vector = users[user_id]
            Database.users[user_id] = User(user_id, user_vector)

        for satellite_id in sats:
            satellite_vector = sats[satellite_id]
            Database.satellites[satellite_id] = Satellite(satellite_id, satellite_vector)

class User:
    def __init__(self, id: User, vector: Vector3) -> None:
        self.id = id
        self.assigned = False
        self.vector = vector
        self.color = None

class Satellite:
    def __init__(self, id: Sat, vector: Vector3) -> None:
        self.id = id
        self.vector = vector 
        self.assignments = []

    @property
    def viable_users(self) -> List[UserID]:
        # TODO: optimize this function by only computing beams within 45 degrees once then filtering out the users that are assigned
        return [
            user_id for user_id in Database.users
            if not Database.users[user_id].assigned
            and self._is_beam_within_45_degrees(Database.users[user_id].vector, self.vector)
        ]

    def available(self, **kwargs) -> bool:
        if 'user_id' in kwargs and 'color' in kwargs:
            return len(self.assignments) < MAX_USERS_PER_SAT and all(
            not self._is_user_within_10_degrees(
                self.vector,
                Database.users[kwargs['user_id']].vector,
                Database.users[user_id].vector
            )
            for user_id in self.assignments if Database.users[user_id].color == kwargs['color']
        )

        return len(self.assignments) < MAX_USERS_PER_SAT

    def assign(self, user_id: User, color: Color) -> None:
        user = Database.users[user_id]
        user.assigned = True
        user.color = color
        self.assignments.append(user_id)

    def reassign(self, user_id: User, color: Color) -> None:
        self._unassign(user_id)
        self.assign(user_id, color)

    def can_make_room_for(self, user_id: User, color: Color) -> bool:
        # TODO: try to refactor this
        conflicts = self._conflicts(user_id, color)
        reassignment_is_feasible = len(conflicts) > 0
        for conflict in conflicts:
            reassignment_possible = False
            for other_color in COLORS:
                if color == other_color:
                    continue
                if self.available(user_id=conflict, color=other_color):
                    reassignment_possible = True
                    break
            if not reassignment_possible:
                reassignment_is_feasible = False
                break
        return reassignment_is_feasible 
    
    def make_room_for(self, user_id: User, color: Color) -> None:
        reassignments = {}
        for conflict_user_id in self._conflicts(user_id, color):
            for other_color in COLORS:
                if color == other_color:
                    continue
                if self.available(user_id=conflict_user_id, color=other_color):
                    reassignments[conflict_user_id] = other_color
                    break  
        return reassignments

    def _is_beam_within_45_degrees(self, user: Vector3, satellite: Vector3) -> bool:
        return 180 - user.angle_between(Vector3(0, 0, 0), satellite) <= 45

    def _is_user_within_10_degrees(self, satellite: Vector3, user_1: Vector3, user_2: Vector3) -> bool:
        vec1 = user_1 - satellite 
        vec2 = user_2 - satellite

        if vec1.mag() == 0 or vec2.mag() == 0:
            return False

        return satellite.angle_between(user_1, user_2) < MIN_BEAM_INTERFERENCE 

    def _conflicts(self, user_id: User, color: Color) -> List[UserID]:
        return [
            id for id in self.assignments
            if Database.users[id].color == color and self._is_user_within_10_degrees(
                self.vector,
                Database.users[user_id].vector,
                Database.users[id].vector
            )
        ]

    def _unassign(self, user_id: User) -> None:
        for index, id in enumerate(self.assignments):
            if id == user_id:
                self.assignments.pop(index)
    