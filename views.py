import json

from rest_framework import viewsets, generics
from journal.models import Journal, Issue
from submission.models import Section, Article
from core.models import Account
from plugins.cdl_janeway_plugin import serializers

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
            try:
                return queryset.filter(**parents_query_dict)
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


class TransporterViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    http_method_names = ['get', 'post']


class JournalViewSet(TransporterViewSet):
    queryset = Journal.objects.all()
    lookup_field = "code"
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
