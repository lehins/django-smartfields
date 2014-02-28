from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.template.response import TemplateResponse
from django.forms import ModelForm

import json, types

__all__ = (
    "FileUploadView", "FileQueueUploadView",
)

def json_response(context, status=200):
    return HttpResponse(json.dumps(context), mimetype="application/json",
                        status=status)

class FileUploadView(View):
    model_form = None
    field_name = None
    prefix = None
    has_permission = None

    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, pk=None, *args, **kwargs):
        if not pk:
            raise Http404
        if not (self.has_permission and callable(self.has_permission) and
                self.model_form and self.field_name):
            return HttpResponse("Missing required implementation", status=501)
        obj = get_object_or_404(self.model_form._meta.model, pk=pk)
        if not self.has_permission(obj, request.user):
            return HttpResponseForbidden()
        return super(FileUploadView, self).dispatch(
            request, obj=obj, *args, **kwargs)

    def complete(self, request, obj=None):
        #form = self.model_form(instance=obj, prefix=self.prefix)
        #field = form.fields.get(self.field_name, None)
        #value = obj.__dict__[self.field_name]
        #if not field:
        #    raise Http404
        context = {
            'task': 'uploading',
            'task_name': "Uploading",
            'status': 'complete'
        }
        if obj:
            field = getattr(obj, self.field_name)
            if field:
                context.update({
                    'file_name': field.name,
                    'file_url': field.url
                })
        return json_response(context)

    def post(self, request, obj=None):
        status = None #obj.smart_field_status(obj.pk, self.field_name)
        if status and status['status'] != 'complete':
            return json_response({
                'task': 'uploading',
                'task_name': "Uploading",
                'status': 'busy',
                'reason': status}, status=409)
        UploadMeta = types.ClassType("UploadMeta", (), {
            'model': self.model_form._meta.model,
            'fields': (self.field_name,)
        })
        UploadForm = types.ClassType("UploadForm", (ModelForm,), {
            "Meta": UploadMeta
        })
        form = UploadForm(
            instance=obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save()
            return self.get(request, obj=obj)
        errors = form.errors.get(form.add_prefix(self.field_name))
        return json_response({
            'task': 'uploading',
            'task_name': "Uploading",
            'status': 'failed',
            'errors': errors
        })

    def get(self, request, obj=None):
        status = None #obj.smart_field_status(obj.pk, self.field_name)
        if status:
            return json_response(status)
        return self.complete(request, obj=obj)


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
