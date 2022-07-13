from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter, Route

from plugins.journal_transporter import views

# Adapted from chibisov's wonderful drf-extensions module
# See https://github.com/chibisov/drf-extensions/blob/master/rest_framework_extensions/routers.py
class NestedRegistryItem:
    def __init__(self, router, parent_prefix, parent_item=None, parent_viewset=None):
        self.router = router
        self.parent_prefix = parent_prefix
        self.parent_item = parent_item
        self.parent_viewset = parent_viewset


    def compose_parent_pk_kwarg_name(self, value):
        return '{0}{1}'.format(
            'parent_lookup_',
            value
        )

    def register(self, prefix, viewset, basename, parents_query_lookups):
        self.router._register(
            prefix=self.get_prefix(
                current_prefix=prefix,
                parents_query_lookups=parents_query_lookups),
            viewset=viewset,
            basename=basename,
        )
        return NestedRegistryItem(
            router=self.router,
            parent_prefix=prefix,
            parent_item=self,
            parent_viewset=viewset
        )


    def get_prefix(self, current_prefix, parents_query_lookups):
        return '{0}/{1}'.format(
            self.get_parent_prefix(parents_query_lookups),
            current_prefix
        )


    def get_parent_prefix(self, parents_query_lookups):
        prefix = '/'
        current_item = self
        i = len(parents_query_lookups) - 1
        while current_item:
            parent_lookup_value_regex = getattr(
                current_item.parent_viewset, 'lookup_value_regex', '[^/.]+')
            prefix = '{parent_prefix}/(?P<{parent_pk_kwarg_name}>{parent_lookup_value_regex})/{prefix}'.format(
                parent_prefix=current_item.parent_prefix,
                parent_pk_kwarg_name=self.compose_parent_pk_kwarg_name(
                    parents_query_lookups[i]),
                parent_lookup_value_regex=parent_lookup_value_regex,
                prefix=prefix
            )
            i -= 1
            current_item = current_item.parent_item
        return prefix.strip('/')


class NestedRouterMixin:
    def _register(self, *args, **kwargs):
        return super().register(*args, **kwargs)

    def register(self, *args, **kwargs):
        self._register(*args, **kwargs)
        return NestedRegistryItem(
            router=self,
            parent_prefix=self.registry[-1][0],
            parent_viewset=self.registry[-1][1]
        )

class TransporterRouter(NestedRouterMixin, DefaultRouter):
    """
    A router for the Transporter API.

    In addition to the rest framework DefaultRouter, this router
    supports nested resources and lookups by journal code.
    """


router = TransporterRouter()

journal_routes = router.register(r'journals', views.JournalViewSet)

journal_review_form_routes = journal_routes.register(r'review_forms', views.JournalReviewFormViewSet, 'journal-review-forms', parents_query_lookups=['journal__id'])
journal_review_form_element_routes = journal_review_form_routes.register(r'elements', views.JournalReviewFormElementViewSet, 'journal-review-form-elements', parents_query_lookups=['journal__id', 'review_form__id'])

journal_role_routes = journal_routes.register(r'roles', views.JournalRoleViewSet, 'journal-roles', parents_query_lookups=['journal__id'])

issue_routes = journal_routes.register(r'issues', views.JournalIssueViewSet, 'journal-issues', parents_query_lookups=['journal__id'])
section_routes = journal_routes.register(r'sections', views.JournalSectionViewSet, 'journal-sections', parents_query_lookups=['journal__id'])

# Holy nested routes, Batman
article_routes = journal_routes.register(r'articles', views.JournalArticleViewSet, 'journal-articles', parents_query_lookups=['journal__id'])
article_editor_routes = article_routes.register(r'editors', views.JournalArticleEditorViewSet, 'journal-article-editors', parents_query_lookups=['journal__id', 'article__id'])
article_file_routes = article_routes.register(r'files', views.JournalArticleFileViewSet, 'journal-article-files', parents_query_lookups=['journal__id', 'article__id'])
article_authors_routes = article_routes.register(r'authors', views.JournalArticleAuthorViewSet, 'journal-article-authors', parents_query_lookups=['journal__id', 'article__id'])
article_revision_request_routes = article_routes.register(r'revision_requests', views.JournalArticleRevisionRequestViewSet, 'journal-article-revision-requests', parents_query_lookups=['journal__id', 'article__id'])
article_rounds_routes = article_routes.register(r'rounds', views.JournalArticleRoundViewSet, 'journal-article-rounds', parents_query_lookups=['journal__id', 'article__id'])
article_rounds_assignments_routes = article_rounds_routes.register(r'assignments', views.JournalArticleRoundAssignmentViewSet, 'journal-article-round-assignments', parents_query_lookups=['journal__id', 'article__id', 'review_round__id'])
article_rounds_assignment_response_routes = article_rounds_assignments_routes.register(r'response', views.JournalArticleRoundAssignmentResponseViewSet, 'journal-article-round-assignment-response', parents_query_lookups=['journal__id', 'article__id', 'review_round__id', 'assignment__id'])


user_routes = router.register(r'users', views.UserViewSet)

# Apply routers to URL patterns
urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^manager', views.manager, name="transporter_manager")
]
