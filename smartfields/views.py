import json

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404, HttpResponse
from django.forms.models import modelform_factory
from django.utils.decorators import method_decorator
from six import text_type
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.views.generic import View

from smartfields.utils import apps

__all__ = (
    "FileUploadView",
)

class FileUploadView(View):
    _model = None
    _field_name = None
    _parent_field_name = None
    instance_method_name = 'has_upload_permission'

    @property
    def model(self):
        """
        Return model instance.

        Args:
            self: (todo): write your description
        """
        if self._model is None:
            app_label = self.kwargs.get('app_label', None)
            model = self.kwargs.get('model', None)
            if app_label and model:
                self._model = apps.get_model(app_label, model)
        if self._model is not None:
            return self._model
        raise ImproperlyConfigured("'model' is a required property")

    @model.setter
    def model(self, value):
        """
        Set the model.

        Args:
            self: (todo): write your description
            value: (str): write your description
        """
        self._model = value

    @property
    def field_name(self):
        """
        Returns the name of the field.

        Args:
            self: (todo): write your description
        """
        if self._field_name is None:
            self._field_name = self.kwargs.get('field_name', None)
        if self._field_name is not None:
            return self._field_name
        raise ImproperlyConfigured("'field_name' is a required property")

    @field_name.setter
    def field_name(self, value):
        """
        Set the name of the field.

        Args:
            self: (todo): write your description
            value: (str): write your description
        """
        self._field_name = value

    @property
    def field(self):
        """
        Returns the field of the model

        Args:
            self: (todo): write your description
        """
        return self.model._meta.get_field(self.field_name)

    @property
    def parent_field_name(self):
        """
        Get the parent name for this field.

        Args:
            self: (todo): write your description
        """
        if self._parent_field_name is not None:
            return self._parent_field_name
        if self._parent_field_name is None:
            self._parent_field_name = self.kwargs.get('parent_field_name', None)
        if self._parent_field_name is None and hasattr(self.model, 'parent_field_name'):
            self._parent_field_name = getattr(self.model, 'parent_field_name')
        return self._parent_field_name

    @parent_field_name.setter
    def parent_field_name(self, value):
        """
        Set the parent name.

        Args:
            self: (todo): write your description
            value: (str): write your description
        """
        self._parent_field_name = value

    def has_permission(self, obj, user):
        """
        Returns true if the current user has permission.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            user: (todo): write your description
        """
        # by raising 404 we make sure that fields that haven't been configured for 
        # uploading look like the don't have an uploading url
        if not settings.DEBUG:
            raise Http404
        raise ImproperlyConfigured(
            "'has_permission' is a required method. You can also add '%s' method "
            "to the model directly, instead of to this view." % 
            self.instance_method_name)

    def get_form_class(self):
        """
        Returns the form class for the given form.

        Args:
            self: (todo): write your description
        """
        return modelform_factory(self.model, fields=(self.field_name,))

    def get_object(self, pk=None, parent_pk=None):
        """
        Retrieve an object from the parent.

        Args:
            self: (todo): write your description
            pk: (str): write your description
            parent_pk: (str): write your description
        """
        kwargs = {}
        model = self.model
        manager = model._default_manager
        if parent_pk is not None and self.parent_field_name is not None:
            parent_field = model._meta.get_field(self.parent_field_name)
            parent_model = parent_field.rel.to
            parent_pk_field_name = "%s_%s" % (
                self.parent_field_name, parent_model._meta.pk.name)
            kwargs = {parent_pk_field_name: parent_pk}
            manager = manager.select_related(self.parent_field_name)
        if pk is None and self.request.method == 'GET':
            pk = self.request.GET.get('pk', None)
        if pk is None:
            obj = model(**kwargs)
        else:
            try:
                obj = manager.get(pk=pk, **kwargs)
            except model.DoesNotExist: 
                raise Http404
        return obj

    def json_response(self, context, status=200):
        """
        Returns a json response.

        Args:
            self: (todo): write your description
            context: (todo): write your description
            status: (str): write your description
        """
        response = HttpResponse(json.dumps(context), 
                                content_type="application/json; charset=utf-8",
                                status=status)
        return response

    @method_decorator(never_cache)
    @method_decorator(csrf_protect)
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        This decorator.

        Args:
            self: (todo): write your description
            request: (todo): write your description
        """
        obj = self.get_object(pk=kwargs.get('pk', None),
                              parent_pk=kwargs.get('parent_pk', None))
        has_permission = None if self.instance_method_name is None else \
                         getattr(obj, self.instance_method_name, None)
        if (callable(has_permission) and \
            not has_permission(request.user, field_name=self.field_name)) or \
            (has_permission is None and not self.has_permission(obj, request.user)):
            raise PermissionDenied
        return super(FileUploadView, self).dispatch(request, obj, *args, **kwargs)

    def complete(self, obj, status):
        """
        Complete an html response.

        Args:
            self: (todo): write your description
            obj: (todo): write your description
            status: (str): write your description
        """
        field_file = getattr(obj, self.field_name)
        if field_file:
            status.update({
                'task': 'uploading',
                'task_name': "Uploading",
                'file_name': field_file.name_base,
                'file_url': field_file.url
            })
            html_tag = getattr(obj, "%s_html_tag" % self.field_name, None)
            if html_tag is not None:
                status['html_tag'] = text_type(html_tag)
        return self.json_response(status)

    def get(self, request, obj, *args, **kwargs):
        """
        Handles get requests.

        Args:
            self: (todo): write your description
            request: (todo): write your description
            obj: (todo): write your description
        """
        status = obj.smartfields_get_field_status(self.field_name)
        if status['state'] == 'complete':
            return self.complete(obj, status)
        return self.json_response(status)

    def post(self, request, obj, *args, **kwargs):
        """
        Handles post requests.

        Args:
            self: (todo): write your description
            request: (todo): write your description
            obj: (todo): write your description
        """
        status = obj.smartfields_get_field_status(self.field_name)
        if status['state'] != 'ready':
            return self.json_response(status)
        form_class = self.get_form_class()
        form = form_class(
            instance=obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            is_new = obj.pk is None
            obj = form.save(commit=is_new)
            field = self.field
            if not is_new:
                obj.save(update_fields=[field.name])
            if field.manager is None or not field.manager.should_process:
                status = obj.smartfields_get_field_status(self.field_name)
                status['state'] = 'complete'
                return self.complete(obj, status)
            return self.get(request, obj, *args, **kwargs)
        status.update({
            'task': 'uploading',
            'task_name': "Uploading",
            'state': 'error',
            'messages': form.errors.get(self.field_name)
        })
        return self.json_response(status)

    def delete(self, request, obj, *args, **kwargs):
        """
        Delete an object

        Args:
            self: (todo): write your description
            request: (todo): write your description
            obj: (todo): write your description
        """
        field_file = getattr(obj, self.field_name)
        if field_file:
            field_file.delete()
        return self.json_response({'task': 'delete', 'state': 'complete'})
