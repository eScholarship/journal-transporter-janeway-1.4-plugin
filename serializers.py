from datetime import datetime, timedelta
from types import LambdaType

from django.db.models import Model, FieldDoesNotExist
from django.utils import timezone

from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField, IntegerField, DateTimeField, EmailField, FileField, SlugRelatedField

from journal.models import Journal, Issue, IssueType
from submission.models import Section, Article, FrozenAuthor
from core.models import Account, File, Galley, Country, COUNTRY_CHOICES, SALUTATION_CHOICES
from core import files

from utils import shared as utils
from submission import logic as submission_logic

import re

opt_str_field = { "required": False, "allow_null": True, "allow_blank": True }
opt_field = { "required": False, "allow_null": True }

class TransporterSerializer(ModelSerializer):
    """
    Base serializer class for creating and ingesting Transporter data structures.
    """

    class Meta:
        # dict of key -> model attribute/setter name, or a lambda that accepts the model
        # as an argument and applies the value.
        setting_values = {}


    source_record_key = SerializerMethodField()


    def get_source_record_key(self, obj: Model) -> str:
        """Builds a source record key from model class name and model PK."""
        return "{0}:{1}".format(obj.__class__.__name__, obj.pk)


    def is_valid(self, raise_exception=False):
        self.before_validation(self.initial_data)
        return super().is_valid(raise_exception)


    def create(self, validated_data: dict) -> Model:
        """
        Create and return a new model instance, given the validated data.

        Any model-specific logic should be encapsulated in #pre_process and #post_process.
        """
        data = validated_data
        self.apply_parent_id(data)
        self.pre_process(data)

        setting_values = self.extract_setting_values(data)
        instance = self.Meta.model.objects.create(**data)

        for key, value in setting_values.items():
            if value: setattr(instance, key, value)
        instance.save()

        self.post_process(instance, data)

        return instance


    def extract_setting_values(self, data: dict) -> list:
        """
        Removes values from the data dict that are not attributes of the model.

        These values are later assigned to the model using either the model's
        setter methods (if method_name_or_lambda is a string) or
        a lambda (if method_name_or_lambda is a lambda).
        """
        if not hasattr(self.Meta, "setting_values") : return {}

        ret = {}
        for key in self.Meta.setting_values:
            if key in data : ret[key] = data.pop(key)
        return ret


    def apply_parent_id(self, data) -> None:
        viewset = self.context['view']
        parent_kwargs = viewset.get_parents_query_dict()

        for (key, value) in parent_kwargs.items():
            fk_record_name, fk_lookup_key = re.split("__?", key)

            if hasattr(self.Meta.model, fk_record_name):
                fk_model = getattr(self.Meta.model, fk_record_name).field.rel.to
                lookup = { fk_lookup_key: value }
                found = fk_model.objects.get(**lookup)

                if found:
                    setattr(self, fk_record_name, found)
                    data["{0}_id".format(fk_record_name)] = found.pk


    def before_validation(self, data: dict) -> None:
        """
        Allow serializer subclasses to adjust the data before it is validated and remapped.

        Mutating data directly will change the values passed to the serializer validator/mapper.

        Note that this function must operate on the Transporter JSON structure directly, not the
        mapped Janeway fields.
        """
        pass


    def pre_process(self, data: dict) -> None:
        """
        Performs any necessary pre-processing of the data dict.

        Runs after validation and mapping, but before save.

        Can be used to ensure required values exist, change dict keys, etc. Should mutate the
        data dict directly.
        """
        pass


    def post_process(self, model: Model, data: dict) -> None:
        """
        Performs any necessary post-processing on the model after it is created.

        This method is responsible for any changes to the model, and must save it for those
        changes to persist.
        """
        pass


    def apply_default_value(self, data, field, default) -> None:
        if not field in data or not data[field]:
            data[field] = default


    ## Utilities


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


class UserSerializer(TransporterSerializer):

    class Meta:
        model = Account
        field_map = {
            "source_record_key": None,
            "email": "email",
            "first_name": "first_name",
            "last_name": "last_name",
            "middle_name": "middle_name",
            "affiliation": "institution",
            "department": "department",
            "salutation": "salutation",
            "country_code": "country",
            "biography": "biography",
            "signature": "signature"
        }
        fields = tuple(field_map.keys())


    email = EmailField()
    first_name = CharField(**opt_str_field)
    last_name = CharField(**opt_str_field)
    middle_name = CharField(**opt_str_field)
    affiliation = CharField(source="institution", default="None", max_length=1000, **opt_str_field)
    department = CharField(**opt_str_field)
    salutation = CharField(**opt_str_field)
    country_code = SlugRelatedField(source="country", slug_field="code", queryset=Country.objects.all(), **opt_field)
    biography = CharField(**opt_str_field)
    signature = CharField(**opt_str_field)


    def before_validation(self, data: dict) -> None:
        # Ensure country_code (country) is a valid code from COUNTRY_CHOICES list
        if data.get("country_code"):
            matches = [code for code, country_name in COUNTRY_CHOICES if data["country_code"].casefold() in [code.casefold(), country_name.casefold()]]
            data["country_code"] = matches[0] if len(matches) else None
        else:
            data["country_code"] = None

        # Ensure affiliation (institution) is not null
        if not data.get("affiliation") : data["affiliation"] = "None"
        if not data.get("affiliation"):
            import pdb; pdb.set_trace()

        # Ensure salutation fits SALUTATION_CHOICES list
        if data.get("salutation"):
            normalized_salutations = [re.sub("\W", "", sal[0]).lower() for sal in SALUTATION_CHOICES]
            for salutation_tuple in SALUTATION_CHOICES:
                if re.sub("\W", "", salutation_tuple[0]).lower() in normalized_salutations:
                    data["salutation"] = salutation_tuple[0]
                    break



    def create(self, validated_data: dict) -> Account:
        """
        If a user already exists (by email), skip.
        """
        try:
            existing = Account.objects.get(email=validated_data["email"].lower())
            return existing
        except Account.DoesNotExist:
            return super().create(validated_data)


class AuthorSerializer(UserSerializer):

    class Meta(UserSerializer.Meta):
        model = FrozenAuthor
        field_map = {
            "source_record_key": None,
            "email": "frozen_emailß",
            "first_name": "first_name",
            "last_name": "last_name",
            "middle_name": "middle_name",
            "affiliation": "institution",
            "department": "department",
            "salutation": "name_prefix",
            "country_code": "country",
            "order": "order"
        }
        fields = tuple(field_map.keys())

    email = EmailField(source="frozen_email", **opt_str_field)
    first_name = CharField(**opt_str_field)
    last_name = CharField(**opt_str_field)
    middle_name = CharField(**opt_str_field)
    affiliation = CharField(source="institution", default="None", max_length=1000, **opt_str_field)
    department = CharField(**opt_str_field)
    salutation = CharField(source="name_prefix", **opt_str_field)
    country_code = SlugRelatedField(source="country", slug_field="code", queryset=Country.objects.all(), **opt_field)
    biography = CharField(**opt_str_field)
    signature = CharField(**opt_str_field)

    def before_validation(self, data: dict) -> None:
        self.article = Article.objects.get(pk=data.pop("article_id")) if "article_id" in data else None
        super().before_validation(data)


    def create(self, validated_data: dict) -> FrozenAuthor:
        return FrozenAuthor.objects.create(article=self.article, **validated_data)


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
        setting_values = (
            "name",
            "issn",
            "print_issn"
        )

    path = CharField(source="code")
    title = CharField(source="name")
    description = CharField(**opt_str_field)
    online_issn = CharField(source="issn", **opt_str_field)
    print_issn = CharField(**opt_str_field)


    def pre_process(self, data: dict) -> None:
        self.apply_default_value(data, "domain", "https://example.com/{0}".format(data["code"]))


    def post_process(self, journal: Journal, data: dict) -> None:
        ## TEMPORARY - Need to look into importing article images if they exist
        journal.disable_article_images = True

        journal.setup_directory()
        IssueType.objects.create(journal=journal, code="issue", pretty_name="Issue")

        journal.save()


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

    title = CharField(source = "issue_title", **opt_str_field)
    volume = IntegerField(default=1, **opt_field)
    number = CharField(source = "issue", default="1", **opt_str_field)
    date_published = DateTimeField(source = "date", **opt_field)
    description = CharField(source = "issue_description", **opt_str_field)
    sequence = IntegerField(source = "order", **opt_field)

    issue_type = CharField(source="issue_type.code", default="issue", read_only=True)
    issue_type_id = IntegerField(write_only=True, required=False)

    def before_validation(self, data: dict) -> None:
        # Title (issue_title) is not allowed to be null, it is allowed to be blank
        if not data.get("title") : data["title"] = ""


    def pre_process(self, data: dict) -> None:
        # We can't create a field out of issue_type, so grab it from the initial data, if it exists
        issue_type, _created = IssueType.objects.get_or_create(journal=self.journal, code=self.initial_data.get("issue_type", "issue"))
        data["issue_type_id"] = issue_type.pk

        self.apply_default_value(data, "date", str(timezone.now()))
        self.apply_default_value(data, "order", len(self.journal.issues))


class SectionSerializer(TransporterSerializer):

    class Meta:
        model = Section
        fields = (
            "source_record_key",
            "title",
            "sequence"
        )

    title = CharField(source="name", **opt_str_field)
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
            "stage": "stage",
            "section": "section",
            "section_id": "section_id",
            "authors": "authors"
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


    title = CharField(**opt_str_field)
    abstract = CharField(**opt_str_field)
    language = CharField(**opt_str_field)
    date_started = DateTimeField(allow_null=True)
    date_accepted = DateTimeField(required=False, allow_null=True)
    date_declined = DateTimeField(required=False, allow_null=True)
    date_submitted = DateTimeField(required=False, allow_null=True)
    date_published = DateTimeField(required=False, allow_null=True)
    date_updated = DateTimeField(required=False, allow_null=True)
    stage = CharField(default="published", **opt_str_field)

    section = CharField(source="section.name", read_only=True, **opt_str_field)
    section_id = IntegerField(write_only=True, required=False)

    authors = AuthorSerializer(many=True)

    def before_validation(self, data: dict) -> None:
        # Title is required
        if not data.get("title") : data["title"] = "Untitled Article"


    def pre_process(self, data: dict) -> None:
        section, _created = Section.objects.get_or_create(journal=self.journal, name=data.get("section", "Articles"))

        data["section_id"] = section.pk
        data["stage"] = self.Meta.stage_map[data["stage"]]


    def create(self, data: dict) -> Article:
        authors = data.pop("authors")
        article = super().create(data)
        for index, author_data in enumerate(authors):
            if author_data.get("email"):
                author = UserSerializer(**author_data).save()
                if not author.password : author.set_password(utils.generate_password())
                author.save()
                submission_logic.add_user_as_author(author, article)
            else:
                author = AuthorSerializer(data={ "article_id": article.pk, "order": index, **author_data })
                if author.is_valid() : author.save()

        return article


class FileSerializer(TransporterSerializer):

    class Meta:
        model = File
        field_map = {
            "source_record_key": None,
            "file": None,
            "description": "description",
            "label": "label",
            "filename": "original_filename"
        }
        fields = tuple(field_map.keys())

    file = FileField(write_only=True, use_url=False)
    description = CharField(**opt_str_field)
    label = CharField(**opt_str_field)
    filename = CharField(source="original_filename", max_length=1000, **opt_str_field)


    def create(self, validated_data: dict) -> Model:
        article = self.get_article()

        raw_file = validated_data.pop("file")
        # TEST - this needs to become a real user reference
        user = Account.objects.all()[0]
        file = files.save_file_to_article(raw_file, article, user, validated_data.get("label"), description=validated_data.get("description"), is_galley=True)

        galley = Galley.objects.create(article=article, file=file)

        return file


    def get_article(self) -> Article:
        # The File model's article reference is not a foreign key, so regular parent
        # look ups won't work. Get the artice here.
        viewset = self.context['view']
        kwargs = viewset.get_parents_query_dict()

        return Article.objects.get(pk=kwargs["article_id"])
