import json, types

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.forms import ModelForm
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.views.generic import View

__all__ = (
    "FileUploadView", "FileQueueUploadView",
)

def json_response(context, status_code=200):
    return HttpResponse(json.dumps(context), mimetype="application/json",
                        status=status_code)

class FileUploadView(View):
    model = None
    model_form = None
    field_name = None
    prefix = None
    has_permission = None

    @property
    def UploadForm(self):
        Meta = types.ClassType("Meta", (), {
            'model': self.model,
            'fields': (self.field_name,)
        })
        properties = {
            "Meta": Meta
        }
        cleaner_name = "clean_%s" % self.field_name
        if self.model_form is not None:
            properties[self.field_name] = self.model_form.base_fields[self.field_name]
            if hasattr(self.model_form, cleaner_name):
                properites[cleaner_name] = getattr(self.model_form, cleaner_name)
        Form = types.ClassType("UploadForm", (ModelForm,), properties)
        return Form


    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, pk=None, obj=None, *args, **kwargs):
        self.model = self.model or self.model_form._meta.model
        if obj is None:
            if pk is None:
                raise Http404
            obj = get_object_or_404(self.model, pk=pk)
        if not (self.has_permission and callable(self.has_permission) and
                self.model and self.field_name):
            return HttpResponse("Missing required implementation", status=501)
        if not self.has_permission(obj, request.user):
            return HttpResponseForbidden()
        return super(FileUploadView, self).dispatch(
            request, obj, *args, **kwargs)

    def complete(self, obj, status):
        field_file = getattr(obj, self.field_name)
        if field_file:
            status.update({
                'file_name': field_file.name_base,
                'file_url': field_file.url,
                'html_tag': field_file.html_tag
            })
        return json_response(status)


    def post(self, request, obj):
        status = obj.smartfield_status(self.field_name)
        if status['state'] != 'ready':
            return json_response(status)

        created = False # necessary hack for progress reporting
        if not obj.pk:
            created = True
            obj.save()

        form = self.UploadForm(
            instance=obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            #obj.save()
            obj = form.save()
            return self.get(request, obj)

        if created:
            obj.delete()

        status.update({
            'task': 'uploading',
            'task_name': "Uploading",
            'state': 'error',
            'messages': form.errors.get(self.field_name)
        })
        return json_response(status)

    def get(self, request, obj):
        status = obj.smartfield_status(self.field_name)
        if status['state'] == 'complete':
            return self.complete(obj, status)
        return json_response(status)


class FileQueueUploadView(View):
    model_form = None

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super(FileQueueUploadView, self).dispatch(*args, **kwargs)

    def pre_valid(request, plupload_form, *args, **kwargs):
        return None

    def pre_save(request, obj, *args, **kwargs):
        return None

    def delete(request, obj, *args, **kwargs):
        return None

    def post(self, request, *args, **kwargs):
        task = request.POST.get('task', 'uploading')
        context = {'task': task, 'task_name': task.title()}
        errors = []
        plupload_form = self.model_form(data=request.POST, files=request.FILES)
        if task == "delete":
            pk = request.POST.get('pk', None)
            custom_errors = []
            try:
                obj = get_object_or_404(self.model_form._meta.model, pk=pk)
                custom_errors = self.delete(request, obj, *args, **kwargs)
            except Http404, e:
                custom_errors.append(e.message)
            if custom_errors:
                errors.extend(custom_errors)
            else:
                context.update({'status': 'complete',
                                 'file_elem_id': plupload_form.get_file_elem_id(
                            plupload_form.file_field_name, pk)
                                 })
                return json_response(context)
        if errors:
            context.update({'status': 'failed',
                            'errors': errors})
            return json_response(context)
        custom_errors = self.pre_valid(request, plupload_form, *args, **kwargs)
        if custom_errors:
            errors.extend(custom_errors)
        if not errors and plupload_form.is_valid():
            obj = plupload_form.save(commit=False)
            custom_errors = self.pre_save(request, obj, *args, **kwargs)
            if custom_errors:
                errors.extend(custom_errors)
            else:
                obj.save()
                context.update({
                        'status': 'complete',
                        'file_elem_id': plupload_form.get_file_elem_id(
                            plupload_form.file_field_name, obj.pk),
                        'rendered_result': plupload_form.get_file_elem_rendered(obj)})
                return json_response(context)
        for key, e in plupload_form.errors.iteritems():
            errors.extend(e)
        context.update({'status': 'failed', 'errors': errors})
        return json_response(context)
