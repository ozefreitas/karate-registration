from types import SimpleNamespace
from unittest.mock import Mock

from django.test import SimpleTestCase

from registration.serializers.serializers import get_person_next_prev


class PersonNavigationSerializerTests(SimpleTestCase):
    def setUp(self):
        self.queryset = Mock()
        self.queryset.order_by.return_value = self.queryset
        self.queryset.values_list.return_value = self.queryset
        self.queryset.distinct.return_value = ["a", "b", "c"]
        self.queryset.filter.return_value = self.queryset
        self.view = Mock()
        self.view.get_queryset.return_value = self.queryset
        self.person = SimpleNamespace(id="b")

    def get_context(self, role):
        user = SimpleNamespace(role=role, is_authenticated=True)
        return {
            "request": SimpleNamespace(user=user),
            "view": self.view,
        }

    def test_subscribed_club_navigation_uses_the_view_queryset(self):
        result = get_person_next_prev(self.person, self.get_context("subed_club"))

        self.assertEqual(result, {"prev": "c", "next": "a"})
        self.queryset.filter.assert_not_called()
        self.view.get_queryset.assert_called_once_with()

    def test_admin_navigation_excludes_people_failing_object_permission(self):
        result = get_person_next_prev(self.person, self.get_context("superuser"))

        self.assertEqual(result, {"prev": "c", "next": "a"})
        self.queryset.filter.assert_called_once_with(is_validated=True)

    def test_roles_without_person_detail_access_get_no_navigation(self):
        for role in ("free_club", "technician", "person"):
            with self.subTest(role=role):
                result = get_person_next_prev(self.person, self.get_context(role))

                self.assertEqual(result, {"prev": None, "next": None})

        self.view.get_queryset.assert_not_called()
