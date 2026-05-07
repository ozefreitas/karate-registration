from django.test import TestCase
from django.utils import timezone
import events.models as event_models


class EventModelTestCase(TestCase):
    """"""

    def test_create_event(self):
        pass


class AnnoucementModelTestCase(TestCase):
    """Test suite for the Announcement model"""

    def test_create_announcement(self):
        annoucement = event_models.Announcement.objects.create(
            message="Welcome to FightTech platform!"
        )

        # Should be the same as above
        self.assertEqual(annoucement.message, "Welcome to FightTech platform!")
        # Should default to True
        self.assertTrue(annoucement.is_active)
        # Should be set
        self.assertIsNotNone(annoucement.created_at)
        # Should save the instance
        self.assertIsNotNone(annoucement.id)