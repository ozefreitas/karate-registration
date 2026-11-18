from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="jwt-test-user",
            password="test-password-123",
        )

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

        self.client.cookies["refresh_token"] = login_response.cookies[
            "refresh_token"
        ].value
        refresh_response = self.client.post(
            "/auth/token/refresh/", {}, format="json", secure=True
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)
        self.assertIn("refresh_token", refresh_response.cookies)

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

        self.client.cookies["refresh_token"] = rotated_refresh
        rejected_refresh = self.client.post(
            "/auth/token/refresh/", {}, format="json", secure=True
        )
        self.assertEqual(rejected_refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_legacy_login_rejects_incorrect_password(self):
        response = self.client.post(
            "/login/",
            {"username": "jwt-test-user", "password": "incorrect-password"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
