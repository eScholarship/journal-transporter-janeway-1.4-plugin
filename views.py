from django.http import HttpResponse, Http404

from rest_framework import viewsets, parsers
from plugins.journal_transporter.parsers import MultiPartJSONParser

from plugins.journal_transporter import serializers

from journal.models import Journal, Issue
from review.models import (ReviewForm, ReviewFormElement, ReviewRound, ReviewAssignment, ReviewFormAnswer,
                           EditorAssignment, RevisionRequest)
from submission.models import Section, Article, FrozenAuthor
from core.models import Account, AccountRole, File
from utils.models import LogEntry
from core import files

from django.contrib.contenttypes.models import ContentType

# Adapted from chibisov's drf-extensions module
# See https://github.com/chibisov/drf-extensions/blob/master/rest_framework_extensions/mixins.py
class NestedViewSetMixin:

    def get_queryset(self):
        return self.filter_queryset_by_parents_lookups(
            super().get_queryset()
        )

    def filter_queryset_by_parents_lookups(self, queryset):
        parents_query_dict = self.get_parents_query_dict()
        if parents_query_dict:
            filtered_query = {
                key: parents_query_dict[key] for key in self.parent_keys
            } if hasattr(self, "parent_keys") else parents_query_dict
            try:
                return queryset.filter(**filtered_query)
            except ValueError:
                raise Http404
        else:
            return queryset

    def get_parents_query_dict(self):
        result = {}
        for kwarg_name, kwarg_value in self.kwargs.items():
            if kwarg_name.startswith('parent_lookup_'):
                query_lookup = kwarg_name.replace(
                    'parent_lookup_',
                    '',
                    1
                )
                query_value = kwarg_value
                result[query_lookup] = query_value
        return result


def manager(request):
    return HttpResponse("OH HI")


class TransporterViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    http_method_names = ['get', 'post']
    parser_classes = [parsers.JSONParser, MultiPartJSONParser]

    def delete(self, _request, *_args, **_kwargs):
        """Deleting resources through this plugin is not allowed."""
        return HttpResponse(status=405)


class UserViewSet(TransporterViewSet):
    queryset = Account.objects.all()
    serializer_class = serializers.UserSerializer


class JournalViewSet(TransporterViewSet):
    queryset = Journal.objects.all()
    serializer_class = serializers.JournalSerializer


class JournalReviewFormViewSet(TransporterViewSet):
    queryset = ReviewForm.objects.all()
    serializer_class = serializers.JournalReviewFormSerializer


class JournalReviewFormElementViewSet(TransporterViewSet):
    queryset = ReviewFormElement.objects.all()
    serializer_class = serializers.JournalReviewFormElementSerializer

    def get_queryset(self):
        return self.queryset.filter(reviewform__pk=self.kwargs["parent_lookup_review_form__id"])

class JournalRoleViewSet(TransporterViewSet):
    queryset = AccountRole.objects.all()
    serializer_class = serializers.JournalRoleSerializer


class JournalIssueViewSet(TransporterViewSet):
    queryset = Issue.objects.all()
    serializer_class = serializers.JournalIssueSerializer


class JournalSectionViewSet(TransporterViewSet):
    queryset = Section.objects.all()
    serializer_class = serializers.JournalSectionSerializer


class JournalArticleViewSet(TransporterViewSet):
    queryset = Article.objects.all()
    serializer_class = serializers.JournalArticleSerializer


class JournalArticleEditorViewSet(TransporterViewSet):
    queryset = EditorAssignment.objects.all()
    serializer_class = serializers.JournalArticleEditorSerializer

    def get_queryset(self):
        return self.queryset.filter(article__pk=self.kwargs["parent_lookup_article__id"])


class JournalArticleAuthorViewSet(TransporterViewSet):
    queryset = FrozenAuthor.objects.all()
    serializer_class = serializers.JournalArticleAuthorSerializer

    def get_queryset(self):
        return self.queryset.filter(article__pk=self.kwargs["parent_lookup_article__id"])

class JournalArticleFileViewSet(TransporterViewSet):
    """
    Handles files for a journal/article set.

    The list route returns a list of all article file metadata. The retrieve route returns
    the file itself.
    """
    queryset = File.objects.all()
    serializer_class = serializers.JournalArticleFileSerializer
    parent_keys = ["article_id"]

    def retrieve(self, request, *args, **kwargs):
        article = Article.objects.get(pk=kwargs["parent_lookup_article__id"])
        file = File.objects.get(pk=kwargs["pk"])
        return files.serve_file(request, file, article)

    def get_queryset(self):
        return self.queryset.filter(article_id=self.kwargs["parent_lookup_article__id"])


class JournalArticleLogEntryViewSet(TransporterViewSet):
    queryset = LogEntry.objects.all()
    serializer_class = serializers.JournalArticleLogEntrySerializer

    def get_queryset(self):
        ct = ContentType.objects.get_for_model(LogEntry)
        return self.queryset.filter(content_type=ct,
                                    object_id=self.kwargs["parent_lookup_article__id"])


class JournalArticleRevisionRequestViewSet(TransporterViewSet):
    queryset = RevisionRequest.objects.all()
    serializer_class = serializers.JournalArticleRevisionRequestSerializer

    def get_queryset(self):
        return self.queryset.filter(article__pk=self.kwargs["parent_lookup_article__id"])


class JournalArticleRoundViewSet(TransporterViewSet):
    queryset = ReviewRound.objects.all()
    serializer_class = serializers.JournalArticleRoundSerializer

    def get_queryset(self):
        return self.queryset.filter(article__pk=self.kwargs["parent_lookup_article__id"])


class JournalArticleRoundAssignmentViewSet(TransporterViewSet):
    queryset = ReviewAssignment.objects.all()
    serializer_class = serializers.JournalArticleRoundAssignmentSerializer

    def get_queryset(self):
        return self.queryset.filter(article__pk=self.kwargs["parent_lookup_article__id"],
                                    review_round__pk=self.kwargs["parent_lookup_review_round__id"])


class JournalArticleRoundAssignmentResponseViewSet(TransporterViewSet):
    queryset = ReviewFormAnswer.objects.all()
    serializer_class = serializers.JournalArticleRoundAssignmentResponseSerializer

    def get_queryset(self):
        return self.queryset.filter(review_assignment__pk=self.kwargs["parent_lookup_assignment__id"])
