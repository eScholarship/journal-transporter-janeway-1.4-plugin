import json

from rest_framework import viewsets, generics, parsers
from journal.models import Journal, Issue
from submission.models import Section, Article
from core.models import Account, File
from core import files
from plugins.cdl_janeway_plugin import serializers
from django.http import HttpResponse, FileResponse
from django.utils.encoding import smart_str

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
            filtered_query = { key: parents_query_dict[key] for key in self.parent_keys } if hasattr(self, "parent_keys") else parents_query_dict
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

    def delete(self, request, *args, **kwargs):
        """Deleting resources through this plugin is not allowed."""
        return HttpResponse(status=405)


class JournalViewSet(TransporterViewSet):
    queryset = Journal.objects.all()
    serializer_class = serializers.JournalSerializer


class IssueViewSet(TransporterViewSet):
    queryset = Issue.objects.all()
    serializer_class = serializers.IssueSerializer


class SectionViewSet(TransporterViewSet):
    queryset = Section.objects.all()
    serializer_class = serializers.SectionSerializer


class ArticleViewSet(TransporterViewSet):
    queryset = Article.objects.all()
    serializer_class = serializers.ArticleSerializer


class UserViewSet(TransporterViewSet):
    queryset = Account.objects.all()
    serializer_class = serializers.UserSerializer


class ArticleFileViewSet(TransporterViewSet):
    """
    Handles files for a journal/article set.

    The list route returns a list of all article file metadata. The retrieve route returns
    the file itself.
    """
    queryset = File.objects.all()
    serializer_class = serializers.FileSerializer
    parent_keys = ["article_id"]
    parser_classes = [parsers.MultiPartParser]

    def retrieve(self, request, *args, **kwargs):
        article = Article.objects.get(pk=kwargs["parent_lookup_article_id"])
        file = File.objects.get(pk=kwargs["pk"])
        return files.serve_file(request, file, article)
