from django.test import TestCase

from .serializers import *
from .views import *

from core.models import Account, Interest
from review.models import ReviewRound, EditorAssignment
from utils.testing import helpers
from utils import setting_handler
from submission.models import ArticleAuthorOrder

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

    def test_copyright_html(self):
        notice = "<p><strong>I grant <em>Clinical Practice and Cases in Emergency Medicine </em>(the \u201cJournal\u201d) on behalf of The Regents of the University of California (\u201cThe Regents\u201d) the non-exclusive right to make any material submitted by the Author to the Journal (the \u201cWork\u201d) available in any format in perpetuity, and to authorize others to do the same. </strong></p> <p>The Author and the Journal agree that eScholarship will publish the article under a <strong>Creative Commons Attribution</strong> license, which is incorporated herein by reference and is further specified at <a href=\"http://creativecommons.org/licenses/by/4.0/\">http://creativecommons.org/licenses/by/4.0/</a>, or later versions of the same license. A brief summary of the license agreement as presented to users is listed below:</p> <p>You are free to:</p> <ul><li>Share \u2013 copy and redistribute the material in any      medium or format; </li><li>Adapt \u2013 remix, transform, and build upon the material;</li><li>for any purpose, even commercially.</li></ul><p>Under the following terms:</p> <ul><li>Attribution \u2014 You must give appropriate credit, provide      a link to the license, and indicate if changes were made. You may do so in      any reasonable manner, but not in any way that suggests the licensor      endorses you or your use.</li></ul><p>The Author warrants as follows:<br /><br /> (a) that the Author has the full power and authority to make this agreement;<br /> (b) that the Work does not infringe any copyrights or trademarks, nor violate any proprietary rights, nor contain any libelous matter, nor invade the privacy of any person or third party; and<br /> (c) that no right in the Work has in any way been sold, mortgaged, or otherwise disposed of, and that the Work is free from all liens and claims.<br /><br /> The Author understands that once the Work is deposited in eScholarship, a full bibliographic citation to the Work will remain visible in perpetuity, even if the Work is updated or removed.<br /><br /><strong>For authors who are not employees of the University of California:</strong><br /> The Author agrees to hold The Regents of the University of California, the California Digital Library, the Journal, and its agents harmless for any losses, claims, damages, awards, penalties, or injuries incurred, including any reasonable attorney's fees that arise from any breach of warranty or for any claim by any third party of an alleged infringement of copyright or any other intellectual property rights arising from the Depositor\u2019s submission of materials with the California Digital Library or of the use by the University of California or other users of such materials.</p>"
        data = {"path": "testj", "title": "Test Journal", "copyright_notice": notice}
        s = JournalSerializer(data=data)
        s.context["view"] = JournalViewSet(kwargs={})

        self.assertTrue(s.is_valid())

        j = s.save()

        self.assertEqual(setting_handler.get_setting('general', 'copyright_notice', j).value, notice)

class ReviewAssignmentSerializerTest(TestCase):

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

    def test_no_dates(self):
        s = self.validate_serializer({})
        a = s.save()
        self.assertEqual(a.date_due.strftime("%Y-%m-%d"), datetime.date.today().strftime('%Y-%m-%d'))

class EditorAssignmentSerializerTest(TestCase):

    def setUp(self):
        self.journal, _ = helpers.create_journals()
        self.article = helpers.create_article(self.journal)
        self.user = helpers.create_user("ed@test.edu")

    def validate_serializer(self, data):
        s = JournalArticleEditorSerializer(data=data)
        s.context["view"] = JournalArticleEditorViewSet(kwargs={})
        s.article = self.article

        self.assertTrue(s.is_valid())
        # typically this is set by the view but since we're
        # circumventing that just set it manually
        s.validated_data['article_id'] = self.article.pk
        return s

    def test_duplicates(self):
        dtformat = '%Y-%m-%dT%H:%M:%S%z'

        date_assigned1 = datetime.datetime(2023, 1, 1, tzinfo=timezone.get_current_timezone()).strftime(dtformat)
        data1 = {'editor_id': self.user.pk, 'date_notified': date_assigned1, 'editor_type': "section-editor", 'notified': True}
        a1 = self.validate_serializer(data1).save()

        date_assigned2 = datetime.datetime(2023, 2, 2, tzinfo=timezone.get_current_timezone()).strftime(dtformat)
        data2 = {'editor_id': self.user.pk, 'date_notified': date_assigned2, 'editor_type': "editor", 'notified': False}
        a2 = self.validate_serializer(data2).save()

        self.assertEqual(a1, a2)
        self.assertEqual(a1.editor.pk, self.user.pk)
        self.assertEqual(a1.article.pk, self.article.pk)
        self.assertEqual(a1.editor_type, 'section-editor')
        self.assertEqual(a1.notified, True)
        self.assertEqual(a1.assigned.strftime(dtformat), date_assigned1)

class ArticleSerializerTest(TestCase):

    def setUp(self):
        self.journal, _ = helpers.create_journals()

    def validate_serializer(self, data):
        s = JournalArticleSerializer(data=data)
        s.context["view"] = JournalArticleViewSet(kwargs={})
        s.journal = self.journal
        self.assertTrue(s.is_valid())
        return s

    def test_date_started(self):
        date_started = "2022-03-28T18:03:34+0000"
        data = {'title': "Title 1", 'date_started': date_started}
        s = self.validate_serializer(data)
        article = s.save()

        self.assertEqual(article.date_started.strftime('%Y-%m-%dT%H:%M:%S%z'), date_started)

class AuthorAssignmentSerializerTest(TestCase):

    def setUp(self):
        self.journal, _ = helpers.create_journals()
        self.article = helpers.create_article(self.journal)
        self.user = helpers.create_user("author@test.edu")

    def validate_serializer(self, data):
        s = JournalArticleAuthorSerializer(data=data)
        s.context["view"] = JournalArticleAuthorViewSet(kwargs={})
        s.article = self.article

        self.assertTrue(s.is_valid())
        # typically this is set by the view but since we're
        # circumventing that just set it manually
        s.validated_data['article_id'] = self.article.pk
        return s

    def test_multiple_objects(self):
        data = {'user_id': self.user.pk, 'email': self.user.email, 'first_name': 'Author', 'last_name': 'Test', 'sequence': 2}
        s = self.validate_serializer(data)
        a1 = s.save()
        data['sequence'] = 3
        s = self.validate_serializer(data)
        a2 = s.save()

        self.assertEqual(ArticleAuthorOrder.objects.filter(article=self.article, author=self.user).count(), 1)
        self.assertEqual(ArticleAuthorOrder.objects.get(article=self.article, author=self.user).order, 2)

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

    def test_user_serializer_invalid_user_missing_first_name(self):
        user_data = {"username": "invalid_user", "email": "invaliduser@example.com", "first_name": None, "last_name": "Sam"}
        serializer = UserSerializer(data=user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)

    def test_user_serializer_invalid_user_missing_last_name(self):
        user_data = {"username": "invalid_user", "email": "invaliduser@example.com", "first_name": "Sam", "last_name": None}
        serializer = UserSerializer(data=user_data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)
