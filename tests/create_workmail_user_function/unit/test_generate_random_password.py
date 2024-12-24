import unittest
from create_workmail_user_function.app import generate_random_password
import string


class TestGenerateRandomPassword(unittest.TestCase):

    def test_password_length(self):
        """Test if the generated password has the correct length."""
        length = 12
        password = generate_random_password(length)
        self.assertEqual(len(password), length)

    def test_password_contains_all_character_types(self):
        """Test if the generated password contains letters, digits, and special characters."""
        password = generate_random_password(12)
        self.assertTrue(
            any(c in string.ascii_lowercase for c in password),
            "Password should contain lowercase letters",
        )
        self.assertTrue(
            any(c in string.ascii_uppercase for c in password),
            "Password should contain uppercase letters",
        )
        self.assertTrue(
            any(c in string.digits for c in password), "Password should contain digits"
        )
        self.assertTrue(
            any(c in "!@#$%^&*()" for c in password),
            "Password should contain special characters",
        )

    def test_password_randomness(self):
        """Test if the generated passwords are random."""
        passwords = {generate_random_password(12) for _ in range(100)}
        self.assertEqual(len(passwords), 100, "Passwords should be unique")

    def test_password_length_variation(self):
        """Test if the function correctly handles different lengths."""
        for length in range(8, 20):
            password = generate_random_password(length)
            self.assertEqual(len(password), length)


if __name__ == "__main__":
    unittest.main()
