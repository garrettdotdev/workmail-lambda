import pytest
from workmail_create.app import generate_random_password


def test_generate_random_password_default_length():
    """Test that the default password length is 12 and only contains allowed characters."""

    # Arrange
    default_length = 12
    allowed_characters = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
        "!@#$%^&*()"
    )

    # Act
    password = generate_random_password()

    # Assert
    assert (
        len(password) == default_length
    ), "Password length is not the default 12 characters"
    assert all(
        char in allowed_characters for char in password
    ), "Password contains invalid characters"


def test_generate_random_password_custom_length():
    """Test that a custom length password is generated correctly."""

    # Arrange
    custom_length = 20

    # Act
    password = generate_random_password(length=custom_length)

    # Assert
    assert (
        len(password) == custom_length
    ), f"Password length is not {custom_length} characters"


def test_generate_random_password_randomness():
    """Test that calling the function multiple times produces different passwords."""

    # Act
    password1 = generate_random_password()
    password2 = generate_random_password()

    # Assert
    assert password1 != password2, "Two consecutive passwords should not be identical"
