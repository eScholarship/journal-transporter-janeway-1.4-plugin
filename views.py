import json

from rest_framework import viewsets, generics
from journal.models import Journal
from plugins.cdl_janeway_plugin import serializers

class JournalViewSet(viewsets.ModelViewSet):
    queryset = Journal.objects.all()
    serializer_class = serializers.JournalSerializer
    http_method_names = ['get', 'post']

    def perform_create(self, serializer):
        instance = serializer.save()
