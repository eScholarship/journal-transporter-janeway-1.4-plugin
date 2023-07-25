from django.test import TestCase

from .serializers import UserSerializer, JournalArticleRoundAssignmentSerializer, JournalSerializer
from .views import UserViewSet, JournalArticleRoundViewSet, JournalViewSet

from core.models import Account, Interest
from review.models import ReviewRound
from utils.testing import helpers
from utils import setting_handler

import datetime
from django.utils import timezone

class TestJournalSerializerTest(TestCase):

    def setUp(self):
        self.journal, _ = helpers.create_journals()

    def test_copyright_notice(self):
        notice = 'This is the copyright notice'
        data = {"path": "testj", "title": "Test Journal", "copyright_notice": notice}
        s = JournalSerializer(data=data)
        s.context["view"] = JournalViewSet(kwargs={})

        self.assertTrue(s.is_valid())

        j = s.save()

        self.assertEqual(setting_handler.get_setting('general', 'copyright_notice', j).value, notice)

class AssignmentSerializerTest(TestCase):

    def setUp(self):
        self.journal, _ = helpers.create_journals()
        self.article = helpers.create_article(self.journal)
        self.round = ReviewRound.objects.create(article=self.article, round_number=1)

    def validate_serializer(self, data):
        s = JournalArticleRoundAssignmentSerializer(data=data)
        s.context["view"] = JournalArticleRoundViewSet(kwargs={})

        self.assertTrue(s.is_valid())
        # typically this is set by the view but since we're
        # circumventing that just set it manually
        s.validated_data['article_id'] = self.article.pk
        return s

    def test_date_requested(self):
        dtformat = '%Y-%m-%dT%H:%M:%S%z'
        date_assigned = datetime.datetime(2023, 1, 1, tzinfo=timezone.get_current_timezone()).strftime(dtformat)

        s = self.validate_serializer({'date_assigned': date_assigned})

        a = s.save()

        self.assertEqual(a.date_requested.strftime(dtformat), date_assigned)
        self.assertEqual(a.date_due.strftime("%Y-%m-%d"), "2023-01-01")

    def test_date_due(self):
        date_due = datetime.date(2023, 1, 1).strftime("%Y-%m-%d")
        dtformat = '%Y-%m-%dT%H:%M:%S%z'
        date_assigned = datetime.datetime(2023, 2, 2, tzinfo=timezone.get_current_timezone()).strftime(dtformat)
        data = {"date_due": date_due, "date_assigned": date_assigned}

        s = self.validate_serializer(data)

        a = s.save()
        self.assertEqual(a.date_requested.strftime(dtformat), date_assigned)
        self.assertEqual(a.date_due.strftime("%Y-%m-%d"), "2023-01-01")

class UserSerializerTest(TestCase):
    """
    Test UserSerializer
    """

    def test_user_serializer_valid_user(self):
        valid_user_data = {"username": "valid_user", "email": "validuser@example.com", "first_name": "Imma", "last_name": "Perfect"}
        serializer = UserSerializer(data=valid_user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(user.email, valid_user_data['email'])
        self.assertEqual(user.first_name, valid_user_data['first_name'])
        self.assertEqual(user.last_name, valid_user_data['last_name'])

    def test_user_serializer_invalid_user_missing_email(self):
        user_data = {"username": "invalid_user", "email": "", "first_name": "Sam", "last_name": "Sam"}
        serializer = UserSerializer(data=user_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_add_interests(self):
        data = {"username": "valid_user", 
                "email": "validuser@example.com", 
                "first_name": "Imma", 
                "last_name": "Perfect", 
                "interests": "Cats, Dogs"}
        serializer = UserSerializer(data=data)
        serializer.context["view"] = UserViewSet(kwargs={})
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(Interest.objects.count(), 2)
        self.assertEqual(user.interest.count(), 2)        

    # For some reason first and last name are not required by the serializer
    # but if they are not filled out serializer.save will return None
    # DRF does NOT like this. We should probably just make them required but
    # I'm just not sure why the code was written this way in the first place.
    def test_user_serializer_invalid_user_missing_first_name(self):
        user_data = {"username": "invalid_user", "email": "invaliduser@example.com", "first_name": None, "last_name": "Sam"}
        serializer = UserSerializer(data=user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertTrue(serializer.is_valid())

    def test_user_serializer_invalid_user_missing_last_name(self):
        user_data = {"username": "invalid_user", "email": "invaliduser@example.com", "first_name": "Sam", "last_name": None}
        serializer = UserSerializer(data=user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertTrue(serializer.is_valid())
