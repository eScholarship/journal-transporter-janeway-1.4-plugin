from django.conf.urls import url, include

from rest_framework import routers

from plugins.cdl_janeway_plugin import views

router = routers.DefaultRouter()
router.register(r'journals', views.JournalViewSet, 'journal')

# Wire up our API using automatic URL routing.
urlpatterns = [
    url(r'^', include(router.urls))
]
