from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="jwt-test-user",
            password="test-password-123",
        )

    @override_settings(DEBUG=False)
    def test_jwt_login_refresh_and_logout(self):
        login_response = self.client.post(
            "/auth/token/",
            {"username": "jwt-test-user", "password": "test-password-123"},
            format="json",
        )

        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertNotIn("refresh", login_response.data)
        self.assertTrue(login_response.cookies["refresh_token"]["httponly"])
        self.assertTrue(login_response.cookies["refresh_token"]["secure"])
        self.assertEqual(login_response.cookies["refresh_token"]["samesite"], "None")

        self.client.cookies["refresh_token"] = login_response.cookies[
            "refresh_token"
        ].value
        refresh_response = self.client.post(
            "/auth/token/refresh/", {}, format="json", secure=True
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
        self.assertIn("refresh_token", refresh_response.cookies)
        self.assertTrue(refresh_response.cookies["refresh_token"]["secure"])
        self.assertEqual(refresh_response.cookies["refresh_token"]["samesite"], "None")

        rotated_refresh = refresh_response.cookies["refresh_token"].value
        logout_response = self.client.post(
            "/logout/",
            HTTP_AUTHORIZATION=f"Bearer {refresh_response.data['access']}",
            secure=True,
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            str(logout_response.cookies["refresh_token"]["max-age"]), "0"
        )
        self.assertTrue(logout_response.cookies["refresh_token"]["secure"])
        self.assertEqual(logout_response.cookies["refresh_token"]["samesite"], "None")

        self.client.cookies["refresh_token"] = rotated_refresh
        rejected_refresh = self.client.post(
            "/auth/token/refresh/", {}, format="json", secure=True
        )
        self.assertEqual(rejected_refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(DEBUG=True)
    def test_refresh_cookie_is_usable_over_local_http(self):
        response = self.client.post(
            "/auth/token/",
            {"username": "jwt-test-user", "password": "test-password-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cookie = response.cookies["refresh_token"]
        self.assertFalse(cookie["secure"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_password_reset_remains_public_and_revokes_refresh_tokens(self):
        login_response = self.client.post(
            "/auth/token/",
            {"username": "jwt-test-user", "password": "test-password-123"},
            format="json",
        )
        self.client.cookies["refresh_token"] = login_response.cookies[
            "refresh_token"
        ].value

        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        weak_password_response = self.client.post(
            f"/password_recovery/confirm/{uidb64}/{token}/",
            {"password": "12345678", "password2": "12345678"},
            format="json",
        )
        self.assertEqual(
            weak_password_response.status_code, status.HTTP_400_BAD_REQUEST
        )

        response = self.client.post(
            f"/password_recovery/confirm/{uidb64}/{token}/",
            {"password": "new-password-123", "password2": "new-password-123"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password-123"))

        refresh_response = self.client.post(
            "/auth/token/refresh/", {}, format="json"
        )
        self.assertEqual(
            refresh_response.status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_legacy_token_authentication_and_login_are_disabled(self):
        response = self.client.get(
            "/me/",
            HTTP_AUTHORIZATION="Token legacy-token",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        login_response = self.client.post(
            "/login/",
            {"username": "jwt-test-user", "password": "test-password-123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_404_NOT_FOUND)
