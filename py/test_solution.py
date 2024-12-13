import unittest
from util import Vector3

from solution import is_beam_within_45_degrees, is_user_within_10_degrees, solve
from util import *

# class TestIsBeamWithin45Degrees(unittest.TestCase):

#     def test_true_1(self):
#         result = is_beam_within_45_degrees(Vector3(0, 1, 0), Vector3(0, 2, 0))
#         self.assertEqual(result, True)

#     def test_true_2(self):
#         result = is_beam_within_45_degrees(Vector3(0, 1, 0), Vector3(1, 2, 0))
#         self.assertEqual(result, True)

#     # def test_true_3(self):
#     #     result = is_beam_within_45_degrees(Vector3(1, 1, 0), Vector3(0, 2, 0))
#     #     self.assertEqual(result, True)

#     def test_false(self):
#         result = is_beam_within_45_degrees(Vector3(0, 1, 0), Vector3(1, 1.5, 0))
#         self.assertEqual(result, False)

# class TestIsUserWithin10Degrees(unittest.TestCase):

#     def test_true_1(self):
#         sat = Vector3(0, 2, 0)
#         user1 = Vector3(0, 1, 0)
#         user2 = Vector3(0.1, 1, 0)  # Adjusted to create an angle less than 10 degrees
#         result = is_user_within_10_degrees(sat, user1, user2)
#         self.assertEqual(True, result)

#     def test_true_2(self):
#         sat = Vector3(0, 2, 0)
#         user1 = Vector3(6371.000, 0, 0)
#         user2 = Vector3(6372.000, 0, 0)
#         result = is_user_within_10_degrees(sat, user1, user2)
#         self.assertEqual(True, result)

#     def test_false(self):
#         sat = Vector3(0, 2, 0)
#         user1 = Vector3(0, 1, 0)
#         user2 = Vector3(2, 1, 0)  # Angle is much greater than 10 degrees
#         result = is_user_within_10_degrees(sat, user1, user2)
#         self.assertEqual(False, result)

class TestSolve(unittest.TestCase):

    def test_1(self):
        user_1_pos = Vector3(6371.000, 0, 0)
        user_2_pos = Vector3(6372.000, 0, 0)
        users = {User(1): user_1_pos, User(2): user_2_pos}
        sats = {Sat(1): Vector3(6921.000, 0, 0)}
        result = solve(users, sats)
        print("Result:", result)
        self.assertEqual(2, len(result))  # Both users should be assigned

if __name__ == '__main__':
    unittest.main()