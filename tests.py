from django.test import TestCase

from .serializers import *
from .views import *

from core.models import Account, Interest, File, SupplementaryFile, WorkflowElement, Workflow
from review.models import ReviewRound
from utils.testing import helpers
from utils import setting_handler
from submission.models import ArticleAuthorOrder
from cron.models import Reminder

import datetime
from django.utils import timezone

from django.core.files.uploadedfile import SimpleUploadedFile

import re, json

DATETIME1 = datetime.datetime(2023, 1, 1, tzinfo=timezone.get_current_timezone())
DATETIME2 = datetime.datetime(2023, 2, 2, tzinfo=timezone.get_current_timezone())

def to_datetime_str(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S%z')

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
        notice = "<p><strong>I grant <em>Clinical Practice and Cases in Emergency Medicine </em>(the \"Journal\") on behalf of The Regents of the University of California (\"The Regents\") the non-exclusive right to make any material submitted by the Author to the Journal (the \"Work\") available in any format in perpetuity, and to authorize others to do the same. </strong></p> <p>The Author and the Journal agree that eScholarship will publish the article under a <strong>Creative Commons Attribution</strong> license, which is incorporated herein by reference and is further specified at <a href=\"http://creativecommons.org/licenses/by/4.0/\">http://creativecommons.org/licenses/by/4.0/</a>, or later versions of the same license. A brief summary of the license agreement as presented to users is listed below:</p> <p>You are free to:</p> <ul><li>Share - copy and redistribute the material in any      medium or format; </li><li>Adapt - remix, transform, and build upon the material;</li><li>for any purpose, even commercially.</li></ul><p>Under the following terms:</p> <ul><li>Attribution - You must give appropriate credit, provide      a link to the license, and indicate if changes were made. You may do so in      any reasonable manner, but not in any way that suggests the licensor      endorses you or your use.</li></ul><p>The Author warrants as follows:<br><br> (a) that the Author has the full power and authority to make this agreement;<br> (b) that the Work does not infringe any copyrights or trademarks, nor violate any proprietary rights, nor contain any libelous matter, nor invade the privacy of any person or third party; and<br> (c) that no right in the Work has in any way been sold, mortgaged, or otherwise disposed of, and that the Work is free from all liens and claims.<br><br> The Author understands that once the Work is deposited in eScholarship, a full bibliographic citation to the Work will remain visible in perpetuity, even if the Work is updated or removed.<br><br><strong>For authors who are not employees of the University of California:</strong><br> The Author agrees to hold The Regents of the University of California, the California Digital Library, the Journal, and its agents harmless for any losses, claims, damages, awards, penalties, or injuries incurred, including any reasonable attorney's fees that arise from any breach of warranty or for any claim by any third party of an alleged infringement of copyright or any other intellectual property rights arising from the Depositor's submission of materials with the California Digital Library or of the use by the University of California or other users of such materials.</p>"
        data = {"path": "testj", "title": "Test Journal", "copyright_notice": notice}
        s = JournalSerializer(data=data)
        s.context["view"] = JournalViewSet(kwargs={})

        self.assertTrue(s.is_valid())

        j = s.save()

        self.assertEqual(setting_handler.get_setting('general', 'copyright_notice', j).value, notice)

    def test_journal_default(self):
        data = {"path": "testj", "title": "Test Journal"}
        s = JournalSerializer(data=data)
        s.context["view"] = JournalViewSet(kwargs={})

        self.assertTrue(s.is_valid())

        j = s.save()
        self.assertTrue(j.disable_front_end)
        self.assertTrue(j.is_remote)
        self.assertEqual(j.remote_view_url, "https://escholarship.org/uc/testj")

        self.assertEqual(Reminder.objects.filter(journal=j).count(), 3)
        w = Workflow.objects.get(journal=j)
        self.assertEqual(w.elements.count(), 4)

class ReviewRoundASerializerTest(TestCase):
    def setUp(self):
        self.journal, _ = helpers.create_journals()
        self.article = helpers.create_article(self.journal)

    def validate_serializer(self, data):
        s = JournalArticleRoundSerializer(data=data)
        s.context["view"] = JournalArticleRoundViewSet(kwargs={})

        self.assertTrue(s.is_valid())
        # typically this is set by the view but since we're
        # circumventing that just set it manually
        s.validated_data['article_id'] = self.article.pk
        return s

    def test_date_started(self):
        date_started = "2022-03-28T18:03:34+0000"
        data = {'round': 1, 'date': date_started}
        s = self.validate_serializer(data)
        round = s.save()

        self.assertEqual(to_datetime_str(round.date_started), date_started)

class RevisionRequestSerializerTest(TestCase):
    def setUp(self):
        self.journal, _ = helpers.create_journals()
        self.article = helpers.create_article(self.journal)

    def validate_serializer(self, data):
        s = JournalArticleRevisionRequestSerializer(data=data)
        s.context["view"] = JournalArticleRevisionRequestViewSet(kwargs={})

        self.assertTrue(s.is_valid())
        # typically this is set by the view but since we're
        # circumventing that just set it manually
        s.validated_data['article_id'] = self.article.pk
        return s

    def test_resubmit(self):
        editor = helpers.create_user("ed@test.edu")
        data = {"decision":"resubmit",
                "comment": "This is the reviewer comment",
                "date":"2022-10-21T02:22:38+00:00",
                "date_requested":"2022-10-30T02:22:38+00:00",
                "editor_id": editor.pk}
        s = self.validate_serializer(data)
        revision = s.save()

        self.assertEqual(revision.type, "major_revisions")
        self.assertEqual(revision.article, self.article)
        self.assertEqual(revision.editor, editor)

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
        date_assigned = to_datetime_str(DATETIME1)

        s = self.validate_serializer({'date_assigned': date_assigned})

        a = s.save()

        self.assertEqual(to_datetime_str(a.date_requested), date_assigned)
        self.assertEqual(a.date_due.strftime("%Y-%m-%d"), "2023-01-01")
        x = re.search('[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', a.access_code)
        self.assertIsNotNone(x)

    def test_date_due(self):
        date_due = datetime.date(2023, 1, 1).strftime("%Y-%m-%d")
        date_assigned = to_datetime_str(DATETIME2)
        data = {"date_due": date_due, "date_assigned": date_assigned}

        s = self.validate_serializer(data)

        a = s.save()
        self.assertEqual(to_datetime_str(a.date_requested), date_assigned)
        self.assertEqual(a.date_due.strftime("%Y-%m-%d"), "2023-01-01")

    def test_no_dates(self):
        s = self.validate_serializer({})
        a = s.save()
        self.assertEqual(a.date_due.strftime("%Y-%m-%d"), datetime.date.today().strftime('%Y-%m-%d'))

    def test_declined(self):
        date_confirmed = to_datetime_str(DATETIME1)
        data = {"date_confirmed": date_confirmed, "declined": True}
        s = self.validate_serializer(data)

        a = s.save()

        self.assertIsNone(a.date_accepted)
        self.assertEqual(to_datetime_str(a.date_declined), date_confirmed)

    def test_accepted(self):
        date_confirmed = to_datetime_str(DATETIME1)
        data = {"date_confirmed": date_confirmed, "declined": False}
        s = self.validate_serializer(data)

        a = s.save()

        self.assertIsNone(a.date_declined)
        self.assertEqual(to_datetime_str(a.date_accepted), date_confirmed)

    def test_accepted_default(self):
        date_confirmed = to_datetime_str(DATETIME1)
        data = {"date_confirmed": date_confirmed}
        s = self.validate_serializer(data)

        a = s.save()

        self.assertIsNone(a.date_declined)
        self.assertEqual(to_datetime_str(a.date_accepted), date_confirmed)

    def test_cancelled(self):
        data = {"cancelled": True}
        s = self.validate_serializer(data)
        a = s.save()
        self.assertEqual(a.decision, 'withdrawn')

    def test_not_cancelled(self):
        data = {"cancelled": False}
        s = self.validate_serializer(data)
        a = s.save()
        self.assertIsNone(a.decision)

    def test_cancelled_default(self):
        s = self.validate_serializer({})
        a = s.save()
        self.assertIsNone(a.decision)

    def test_supp_files(self):
        reviewer = helpers.create_user("reviewer@test.edu")
        editor = helpers.create_user("ed@test.edu")
        round, _ = ReviewRound.objects.get_or_create(article=self.article, round_number=1)

        review_file = File.objects.create(article_id=self.article.pk,
                                          mime_type="application/pdf",
                                          original_filename="test.pdf",
                                          uuid_filename="0000.pdf",
                                          label="Test Review File",
                                          sequence=1)
        other_file = File.objects.create(article_id=self.article.pk,
                                          mime_type="application/pdf",
                                          original_filename="test.pdf",
                                          uuid_filename="0000.pdf",
                                          label="Test Supplementary File",
                                          sequence=1)
        supp_file = SupplementaryFile.objects.create(file=other_file)
        data = {"reviewer_id": reviewer.pk,
                "editor_id": editor.pk,
                "round_review_file_ids": [review_file.pk],
                "supplementary_file_ids": [supp_file.file.pk]}
        s = self.validate_serializer(data)
        s.validated_data['review_round_id'] = round.pk
        a = s.save()

        self.assertEquals(a.review_round.review_files.count(), 2)

    def test_review_comments(self):
        data = {"comments": [{"comments": "Author Comment 1", "visible_to_author": True},
                             {"comments": "Author Comment 2", "visible_to_author": True},
                             {"comments": "Editor <b>Comment</b> 1", "visible_to_author": False},
                             {"comments": "Editor Comment 2", "visible_to_author": False}]}
        s = self.validate_serializer(data)
        a = s.save()
        self.assertEqual(a.comments_for_editor, "Editor \nComment\n 1")
        self.assertEqual(a.reviewassignmentanswer_set.count(), 3)

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

    def test_is_editor(self):
        assigned = to_datetime_str(DATETIME1)
        data = {'editor_id': self.user.pk, 'date_notified': assigned, 'is_editor': False, 'notified': True}
        a = self.validate_serializer(data).save()

        self.assertEqual(a.editor.pk, self.user.pk)
        self.assertEqual(a.article.pk, self.article.pk)
        self.assertEqual(a.editor_type, 'section-editor')
        self.assertEqual(a.notified, True)
        self.assertEqual(to_datetime_str(a.assigned), assigned)

    def test_duplicates(self):
        date_assigned1 = to_datetime_str(DATETIME1)
        data1 = {'editor_id': self.user.pk, 'date_notified': date_assigned1, 'editor_type': "section-editor", 'notified': True}
        a1 = self.validate_serializer(data1).save()

        date_assigned2 = to_datetime_str(DATETIME2)
        data2 = {'editor_id': self.user.pk, 'date_notified': date_assigned2, 'editor_type': "editor", 'notified': False}
        a2 = self.validate_serializer(data2).save()

        self.assertEqual(a1, a2)
        self.assertEqual(a1.editor.pk, self.user.pk)
        self.assertEqual(a1.article.pk, self.article.pk)
        self.assertEqual(a1.editor_type, 'section-editor')
        self.assertEqual(a1.notified, True)
        self.assertEqual(to_datetime_str(a1.assigned), date_assigned1)

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

        self.assertEqual(to_datetime_str(article.date_started), date_started)

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

class ArticleFileSerializerTest(TestCase):

    def setUp(self):
        self.journal, _ = helpers.create_journals()
        self.article = helpers.create_article(self.journal)
        self.user = helpers.create_user("author@test.edu")

    def validate_serializer(self, data):
        s = JournalArticleFileSerializer(data=data)
        s.context["view"] = JournalArticleFileViewSet(kwargs={'parent_lookup_article__id': self.article.pk})
        s.article = self.article

        self.assertTrue(s.is_valid())
        return s

    def test_supp_file(self):
        pdf_file = SimpleUploadedFile("test.pdf", b"\x00\x01\x02\x03")
        data = {"file": pdf_file,
                "file_name":"56915-269222-3-SM.docx",
                "file_type":"application\/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "original_filename":"Grit and resident well being West JEM.docx",
                "date_uploaded":"2022-03-28T17:50:05+00:00",
                "type":"supp",
                "round":1,
                "parent_source_record_key":None,
                "is_galley_file":False,
                "is_supplementary_file":True}

        s = self.validate_serializer(data)
        f = s.save()

        self.assertEqual(SupplementaryFile.objects.filter(file=f).count(), 1)
        self.assertEqual(self.article.supplementary_files.count(), 1)
        self.assertEqual(self.article.manuscript_files.count(), 0)

    def test_file_label(self):
        pdf_file = SimpleUploadedFile("test.pdf", b"\x00\x01\x02\x03")
        data = {"file": pdf_file,
                "file_name":"56915-269222-3-SM.docx",
                "file_type":"application\/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "original_filename":"Grit and resident well being West JEM.docx",
                "date_uploaded":"2022-03-28T17:50:05+00:00",
                "type":"submission\/original",
                "round":1,
                "parent_source_record_key":None,
                "is_galley_file":False,
                "is_supplementary_file":False,
                "title":"",
                "description":None,
                "creator":None,"publisher":None,"source":None,"type_other":None}

        s = self.validate_serializer(data)
        f = s.save()

        self.assertEqual(f.label, data["file_name"])

    def test_file_history_label(self):
        parent_file = File.objects.create(article_id=self.article.pk,
                                          mime_type="application/pdf",
                                          original_filename="parent_file.pdf",
                                          uuid_filename="0000.pdf",
                                          label="Parent File Label",
                                          sequence=1)

        pdf_file = SimpleUploadedFile("test.pdf", b"\x00\x01\x02\x03")
        data = {"file": pdf_file,
                "file_name":"file_name.pdf",
                "file_type":"application/pdf",
                "original_filename":"original_filename.pdf",
                "date_uploaded":"2022-03-28T17:50:05+00:00",
                "type":"submission/original",
                "round":1,
                "parent_target_record_key":f"ArticleFile:{self.article.pk}:{parent_file.pk}"}

        s = self.validate_serializer(data)
        f = s.save()

        self.assertEqual(f.label, data["file_name"])

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
        self.assertTrue(user.is_active)

    def test_existing_user_active(self):
        user = helpers.create_user("user@test.edu")
        self.assertFalse(user.is_active)

        data = {"email": "user@test.edu", "first_name": "User", "last_name": "One"}
        serializer = UserSerializer(data=data)
        serializer.context["view"] = UserViewSet(kwargs={})

        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertTrue(user.is_active)

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

