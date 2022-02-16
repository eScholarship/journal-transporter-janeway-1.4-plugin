from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField

from journal.models import Journal

class JournalSerializer(ModelSerializer):

    class Meta:
        model = Journal
        fields = ("id", "path", "title")

    id = SerializerMethodField()
    path = CharField(source="code")
    title = CharField(source="name")

    def get_id(self, obj):
        return "Journal:%s" % obj.pk

    def create(self, validated_data):
        """
        Create and return a new Journal instance, given the validated data
        """
        data = validated_data
        if not "domain" in data:
            data["domain"] = "https://example.com/%s" % data["code"]

        name = data.pop("name")
        instance = Journal.objects.create(**data)
        if name:
            instance.name = name

        instance.save()
        return instance
