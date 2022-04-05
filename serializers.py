from datetime import datetime, timedelta
from types import LambdaType

from django.db.models import Model, FieldDoesNotExist
from django.utils import timezone

from rest_framework.serializers import ModelSerializer, SerializerMethodField
from rest_framework.fields import CharField, IntegerField, DateTimeField, EmailField

from journal.models import Journal, Issue, IssueType
from submission.models import Section, Article
from core.models import Account


class TransporterSerializer(ModelSerializer):
    """
    Base serializer class for creating and ingesting Transporter data structures.
    """

    class Meta:
        # dict of key -> model attribute/setter name, or a lambda that accepts the model
        # as an argument and applies the value.
        non_attribute_values = {}


    source_record_key = SerializerMethodField()


    def extract_non_attribute_values(self, data: dict) -> list:
        """
        Removes values from the data dict that are not attributes of the model.

        These values are later assigned to the model using either the model's
        setter methods (if method_name_or_lambda is a string) or
        a lambda (if method_name_or_lambda is a lambda).
        """
        if not hasattr(self.Meta, "non_attribute_values") : return {}

        ret = {}
        for key in self.Meta.non_attribute_values:
            if key in data : ret[key] = data.pop(key)
        return ret


    def get_source_record_key(self, obj: Model) -> str:
        """Builds a source record key from model class name and model PK."""
        return "{0}:{1}".format(obj.__class__.__name__, obj.pk)


    def create(self, validated_data: dict) -> Model:
        """
        Create and return a new model instance, given the validated data.

        Any model-specific logic should be encapsulated in #pre_process and #post_process.
        """
        data = validated_data
        self.apply_parent_id(data)
        self.pre_process(data)

        non_attribute_values = self.extract_non_attribute_values(data)
        instance = self.Meta.model.objects.create(**data)

        for key, value in non_attribute_values.items():
            if value: setattr(instance, key, value)
        instance.save()

        self.post_process(instance, data)

        return instance


    def apply_parent_id(self, data) -> None:
        viewset = self.context['view']
        parent_kwargs = viewset.get_parents_query_dict()

        for (key, value) in parent_kwargs.items():
            fk_record_name, fk_lookup_key = key.split("__")

            if hasattr(self.Meta.model, fk_record_name):
                fk_model = getattr(self.Meta.model, fk_record_name).field.rel.to
                lookup = { fk_lookup_key: value }
                found = fk_model.objects.get(**lookup)

                if found:
                    self.parent = found
                    data["{0}_id".format(fk_record_name)] = found.pk


    def pre_process(self, data: dict) -> None:
        """
        Performs any necessary pre-processing of the data dict.

        Can be used to ensure required values exist, change dict keys, etc. Should mutate the
        data dict directly. Return value is not used.
        """
        pass


    def post_process(self, model: Model, data: dict) -> None:
        """
        Performs any necessary post-processing on the model after it is created and
        non-attribute-values are applied and saved.
        """
        pass


    def apply_default_value(self, data, field, default) -> None:
        if not field in data or not data[field]:
            data[field] = default


    @classmethod
    def setup_fields(cls):
        for json_field, source in cls.Meta.field_map.items():
            args = TransporterSerializer.field_options_for(cls.Meta.model, json_field)
            if json_field != source : args["source"] = source

            try:
                field_method = getattr(fields, cls.Meta.model._meta.get_field(source).get_internal_type())
                setattr(cls, json_field, field_method(**args))
            except FieldDoesNotExist:
                setattr(cls, json_field, fields.CharField(**args))

    @staticmethod
    def _field_options_for(self, model, field) -> dict:
        try:
            field_def = model._meta.get_field(field)
            return {
                "allow_null": field_def.null,
                "allow_blank": field_def.blank
            }
        except FieldDoesNotExist:
            return {
                "allow_null": True,
                "allow_blank": True
            }


class JournalSerializer(TransporterSerializer):

    class Meta:
        model = Journal
        field_map = {
            "source_record_key": None,
            "path": "code",
            "title": "name",
            "description": "description",
            "online_issn": "issn",
            "print_issn": "print_issn"
        }
        fields = tuple(field_map.keys())
        non_attribute_values = (
            "name",
            "issn",
            "print_issn"
        )

    path = CharField(source="code")
    title = CharField(source="name")
    description = CharField(allow_null=True, allow_blank=True)
    online_issn = CharField(source="issn", allow_null=True, allow_blank=True)
    print_issn = CharField(allow_null=True, allow_blank=True)


    def pre_process(self, data: dict) -> None:
        self.apply_default_value(data, "domain", "https://example.com/{0}".format(data["code"]))


    def post_process(self, journal: Journal, data: dict) -> None:
        journal.setup_directory()
        IssueType.objects.create(journal=journal, code="issue", pretty_name="Issue")


class IssueSerializer(TransporterSerializer):

    class Meta:
        model = Issue
        fields = (
            "source_record_key",
            "title",
            "volume",
            "number",
            "date_published",
            "description",
            "sequence",
            "issue_type",
            "issue_type_id"
        )

    title = CharField(source = "issue_title", allow_blank=True, allow_null=True)
    volume = IntegerField(default=1, allow_null=True)
    number = CharField(source = "issue", default="1", allow_blank=True, allow_null=True)
    date_published = DateTimeField(source = "date", allow_null=True)
    description = CharField(source = "issue_description", allow_blank=True, allow_null=True)
    sequence = IntegerField(source = "order", allow_null=True)
    issue_type_id = IntegerField(write_only=True, required=False)
    issue_type = CharField(source="issue_type.code", default="issue", read_only=True)


    def pre_process(self, data) -> None:
        # We can't create a field out of issue_type, so grab it from the initial data, if it exists
        issue_type, _created = IssueType.objects.get_or_create(journal=self.parent, code=self.initial_data.get("issue_type", "issue"))

        self.apply_default_value(data, "date", str(timezone.now()))
        self.apply_default_value(data, "order", len(self.parent.issues))
        self.apply_default_value(data, "issue_type_id", issue_type.pk)


class SectionSerializer(TransporterSerializer):

    class Meta:
        model = Section
        fields = (
            "source_record_key",
            "title",
            "sequence"
        )

    title = CharField(source="name", allow_blank=True, allow_null=True)
    sequence = IntegerField(default=0, allow_null=True)


class ArticleSerializer(TransporterSerializer):

    class Meta:
        model = Article
        field_map = {
            "source_record_key": None,
            "title": "title",
            "abstract": "abstract",
            "language": "language",
            "date_started": "date_started",
            "date_accepted": "date_accepted",
            "date_declined": "date_declined",
            "date_submitted": "date_submitted",
            "date_published": "date_published",
            "date_updated": "date_updated",
            "stage": "stage"
        }
        fields = tuple(field_map.keys())
        stage_map = {
            "draft": "Unsubmitted",
            "submitted": "Unassigned",
            "assigned": "Assigned to Editor",
            "review": "Peer Review",
            "revision": "Revision",
            "rejected": "Rejected",
            "accepted": "Accepted",
            "copyediting": "Editor Copyediting",
            "typesetting": "Typesetting",
            "proofing": "Proofing",
            "published": "Published"
        }


    title = CharField()
    abstract = CharField(required=False, allow_null=True)
    language = CharField(required=False, allow_null=True)
    date_started = DateTimeField(allow_null=True)
    date_accepted = DateTimeField(required=False, allow_null=True)
    date_declined = DateTimeField(required=False, allow_null=True)
    date_submitted = DateTimeField(required=False, allow_null=True)
    date_published = DateTimeField(required=False, allow_null=True)
    date_updated = DateTimeField(required=False, allow_null=True)
    stage = CharField(default="published", allow_null=True)

    def pre_process(self, data: dict) -> None:
        data["stage"] = self.Meta.stage_map[data["stage"]]
        data["date_published"] = datetime.today() - timedelta(days=1)


class UserSerializer(TransporterSerializer):

    class Meta:
        model = Account
        field_map = {
            "source_record_key": None,
            "pk": None,
            "email": "email",
            "first_name": "first_name",
            "last_name": "last_name",
            "middle_name": "middle_name",
            "affiliation": "institution",
            "salutation": "salutation",
            # "country_code": "country",
            "biography": "biography",
            "signature": "signature"
        }
        fields = tuple(field_map.keys())

    pk = IntegerField(write_only=True, required=False)
    email = EmailField()
    first_name = CharField()
    last_name = CharField()
    middle_name = CharField(required=False, allow_null=True, allow_blank=True)
    affiliation = CharField(source="institution", max_length=1000, required=False, allow_null=True)
    salutation = CharField(required=False, allow_null=True, allow_blank=True)
    # country_code = CharField(source="country", required=False, allow_null=True, allow_blank=True)
    biography = CharField(required=False, allow_null=True, allow_blank=True)
    signature = CharField(required=False, allow_null=True, allow_blank=True)

    def pre_process(self, data: dict) -> None:
        # Look up users by email - if they exist, add PK to data so we update instead of create
        try:
            existing = Account.objects.get(email=data["email"].lower())
            data["pk"] = existing.pk
        except Account.DoesNotExist:
            pass
