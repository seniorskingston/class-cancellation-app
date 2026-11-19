import unittest

import locations_admin


class LocationAdminTests(unittest.TestCase):
    def test_new_location_is_added_beside_the_original_list(self):
        builtin = {"SC - Seniors Centre": "56 Francis Street"}
        updated, error = locations_admin.add_place(builtin, {}, "Hall - New Room", "12 Main Street")
        self.assertEqual(error, "")
        self.assertEqual(updated["Hall - New Room"], "12 Main Street")
        self.assertNotIn("SC - Seniors Centre", updated)

    def test_duplicate_and_center_names_are_refused(self):
        builtin = {"SC - Seniors Centre": "56 Francis Street"}
        extra = {"Hall - New Room": "12 Main Street"}
        same, error = locations_admin.add_place(builtin, extra, "hall - new room", "Other")
        self.assertEqual(same, extra)
        self.assertIn("already", error)
        hidden, hidden_error = locations_admin.add_place(builtin, extra, "New Center", "12 Main Street")
        self.assertEqual(hidden, extra)
        self.assertIn("Centre", hidden_error)

    def test_only_an_added_location_can_be_removed(self):
        extra = {"Hall - New Room": "12 Main Street"}
        kept, error = locations_admin.remove_place(extra, "SC - Seniors Centre")
        self.assertEqual(kept, extra)
        self.assertIn("added on this page", error)
        removed, removed_error = locations_admin.remove_place(extra, "Hall - New Room")
        self.assertEqual(removed_error, "")
        self.assertEqual(removed, {})


if __name__ == "__main__":
    unittest.main()
