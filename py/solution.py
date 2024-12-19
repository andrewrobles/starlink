from typing import Dict, List, Tuple

from util import Color, Sat, User, Vector3

MAX_USERS_PER_SAT = 32
MIN_BEAM_INTERFERENCE = 10
COLORS = [Color.A, Color.B, Color.C, Color.D]

def solve(users: Dict[User, Vector3], sats: Dict[Sat, Vector3]) -> Dict[User, Tuple[Sat, Color]]:

    Database.load(users, sats)

    for satellite_id, satellite in Database.satellites.items():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if satellite.available(user=user_id, color=color):
                    satellite.assign(user_id, color)
                    break  

    for satellite_id, satellite in Database.satellites.items():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if satellite.can_make_room_for(user_id, color):
                    reassignments = satellite.make_room_for(user_id, color)
                    for user_to_reassign, color_to_reassign_to in reassignments.items():
                        satellite.reassign(user_to_reassign, color_to_reassign_to)
                    satellite.assign(user_id, color)
                      
    return Database.solution

class Database:
    users = {}
    satellites = {}
    solution = {}

    @classmethod
    def load(self, users: Dict[User, Vector3], sats: Dict[Sat, Vector3]):
        for user_id in users:
            user_vector = users[user_id]
            Database.users[user_id] = User(user_id, user_vector)

        for satellite_id in sats:
            satellite_vector = sats[satellite_id]
            Database.satellites[satellite_id] = Satellite(satellite_id, satellite_vector)

class User:
    def __init__(self, id: User, vector: Vector3):
        self.id = id
        self.assigned = False
        self.vector = vector

class Satellite:
    def __init__(self, id: Sat, vector: Vector3):
        self.id = id
        self.vector = vector 
        self.assignments = []

    @property
    def viable_users(self):
        return [
            user_id for user_id in Database.users
            if not Database.users[user_id].assigned
            and self._is_beam_within_45_degrees(Database.users[user_id].vector, self.vector)
        ]

    def available(self, **kwargs):
        if 'user' in kwargs and 'color' in kwargs:
            return len(self.assignments) < MAX_USERS_PER_SAT and all(
            not self._is_user_within_10_degrees(
                self.vector,
                Database.users[kwargs['user']].vector,
                Database.users[assignment['user']].vector
            )
            for assignment in self.assignments if assignment['color'] == kwargs['color']
        )

        return len(self.assignments) < MAX_USERS_PER_SAT

    def reassign(self, user_id: User, color: Color):
        self._unassign(user_id)
        self.assign(user_id, color)

    def assign(self, user_id: User, color: Color):
        Database.users[user_id].assigned = True
        Database.solution[user_id] = (self.id, color)
        self.assignments.append({ 'user': user_id, 'color': color })

    def can_make_room_for(self, user_id: User, color: Color):
        conflicts = self._conflicts(user_id, color)
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
    
    def make_room_for(self, user_id: User, color: Color):
        reassignments = {}
        for conflict in self._conflicts(user_id, color):
            for other_color in COLORS:
                if color == other_color:
                    continue
                if self.available(user=conflict, color=other_color):
                    reassignments[conflict] = other_color
                    break  
        return reassignments

    def _is_beam_within_45_degrees(self, user: Vector3, satellite: Vector3):
        return 180 - user.angle_between(Vector3(0, 0, 0), satellite) <= 45

    def _is_user_within_10_degrees(self, satellite: Vector3, user_1: Vector3, user_2: Vector3):
        vec1 = user_1 - satellite 
        vec2 = user_2 - satellite

        if vec1.mag() == 0 or vec2.mag() == 0:
            return False

        return satellite.angle_between(user_1, user_2) < MIN_BEAM_INTERFERENCE 

    def _conflicts(self, user_id: User, color: Color):
        return [
            assignment['user'] for assignment in self.assignments
            if assignment['color'] == color and self._is_user_within_10_degrees(
                self.vector,
                Database.users[user_id].vector,
                Database.users[assignment['user']].vector
            )
        ]

    def _unassign(self, user_id: User):
        for index, assignment in enumerate(self.assignments):
            if assignment['user'] == user_id:
                self.assignments.pop(index)