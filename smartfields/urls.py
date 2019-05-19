from django.conf.urls import url

from smartfields.views import FileUploadView

app_name = 'smartfields'
urlpatterns = [
    url(r'upload/(?P<app_label>\w+)/(?P<model>\w+)/(?P<field_name>\w+)/(?:(?P<pk>\d+)/)?'
        r'(?:(?P<parent_field_name>\w+)/(?P<parent_pk>\d+)/)?$',
        FileUploadView.as_view(), name='upload'),
]
