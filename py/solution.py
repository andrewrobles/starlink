from typing import Dict, List, Tuple

from util import Color, Sat, User, Vector3
import math

COLORS = [Color.A, Color.B, Color.C, Color.D]

def solve(users: Dict[User, Vector3], sats: Dict[Sat, Vector3]) -> Dict[User, Tuple[Sat, Color]]:
    solution = {}

    for satellite_id in sats:
        Satellite.satellites[satellite_id] = Satellite(satellite_id, sats, users)

    for user_id in users:
        User.users[user_id] = User(user_id, users)

    for satellite_id in Satellite.satellites.keys():
        for user_id in Satellite.satellites[satellite_id].viable_users:
            for color in COLORS:
                if Satellite.satellites[satellite_id].available(user=user_id, color=color):
                    solution[user_id] = (satellite_id, color)
                    User.users[user_id].assigned = True
                    Satellite.satellites[satellite_id].assign(user_id, color)
                    break  

    for satellite_id, satellite in Satellite.satellites.items():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if Satellite.satellites[satellite_id].available(user=user_id, color=color):
                    solution[user_id] = (satellite_id, color)
                    User.users[user_id].assigned = True
                    Satellite.satellites[satellite_id].assign(user_id, color)
                    break

    for satellite_id, satellite in Satellite.satellites.items():
        for user_id in satellite.viable_users:
            for color in COLORS:
                if satellite.can_make_room_for(user_id, color):
                    reassignments = satellite.make_room_for(user_id, color)
                    for user_to_reassign, color_to_reassign_to in reassignments.items():
                        if Satellite.satellites[satellite_id].available():
                            solution[user_to_reassign] = (satellite_id, color_to_reassign_to)
                            Satellite.satellites[satellite_id].unassign(user_to_reassign)
                            Satellite.satellites[satellite_id].assign(user_to_reassign, color_to_reassign_to)

                    if Satellite.satellites[satellite_id].available():
                        solution[user_id] = (satellite_id, color)
                        User.users[user_id].assigned = True
                        Satellite.satellites[satellite_id].assign(user_id, color)
                      
    return solution

MAX_USERS_PER_SAT = 32

class Satellite:
    satellites = {}

    def __init__(self, id, satellites, users):
        self.id = id
        self.vector = satellites[id] 
        self.users = users
        self.assignments = []

    @property
    def viable_users(self):
        return [user_id for user_id in self.users if not User.users[user_id].assigned and self.is_beam_within_45_degrees(self.users[user_id], self.vector)]

    def available(self, **kwargs):
        if 'user' in kwargs and 'color' in kwargs:
            return len(self.assignments) < MAX_USERS_PER_SAT and all(
            not self.is_user_within_10_degrees(self.vector, self.users[kwargs['user']], self.users[assignment['user']])
            for assignment in self.assignments if assignment['color'] == kwargs['color']
        )

        return len(self.assignments) < MAX_USERS_PER_SAT

    def conflicts(self, user, color):
        return [
            assignment['user'] for assignment in self.assignments
            if assignment['color'] == color and self.is_user_within_10_degrees(self.vector, self.users[user], self.users[assignment['user']])
        ]

    def assign(self, user, color):
        self.assignments.append({ 'user': user, 'color': color })

    def unassign(self, user):
        for index, assignment in enumerate(self.assignments):
            if assignment['user'] == user:
                self.assignments.pop(index)

    def can_make_room_for(self, user_id, color):
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
                    break  # Stop checking other colors once a valid reassignment is found
            if not reassignment_possible:
                reassignment_is_feasible = False
                break  # Stop checking conflicts if one cannot be reassigned
        return reassignments

    def is_beam_within_45_degrees(self, user, satellite):
        return 180 - user.angle_between(Vector3(0, 0, 0), satellite) <= 45

    def is_user_within_10_degrees(self, satellite, user_1, user_2):
        vec1 = user_1 - satellite 
        vec2 = user_2 - satellite

        if vec1.mag() == 0 or vec2.mag() == 0:
            return False

        return satellite.angle_between(user_1, user_2) < 10

class User:
    users = {}

    def __init__(self, id, users):
        self.assigned = False

