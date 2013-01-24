
django-smart-fields
===================

Django Model Fields that are smart. Currently only file fields.

Features
--------

* Cleanup of orphan files after the entry in database was deleted or if file was replaced with a different one
* Image files conversion and/or resizing (requires PIL)
* Video files conversion (requires avconv or ffmpeg)
* Automatic addition of the converted FileFields to the model. (For instance if a particular ImageField defined in the model with a name 'image', using custom settings for that field named 'png' each instance of that model will be initialized with an addidional field 'image_png'.)
* Custom file upload form fields that feature:
    * displaying of initial value (displaying currently saved image or video)
    * upload progress (requires plupload, works in all browsers)
    * file size display and limit before uploading (requires plupload)
    * queueing of multiple files to be uploaded (requires plupload)

Dependancies
------------
* `Django <https://docs.djangoproject.com/en/dev/>`_ (currently works with development 1.6 version and possibly with 1.5 RC, couple methods used for widget rendering needs to be ported from development verision for it to work in earlier version <= 1.4)
* `Python PIL <http://pypi.python.org/pypi/PIL>`_ used for image conversion/resizing
* `avconv <http://libav.org/avconv.html>`_ for video conversion (should also work with ffmpeg, will require settings modifications though. has not been tested with ffmpeg yet)
* `Plupload <http://www.plupload.com/>`_ for using smartfields in forms (free for development, license for production is ~$14. Totally worth it.)

How to use it
-------------

For any of the features to work yuo have to extend the base abstract model ``smart_fields.models.SmartFieldsBaseModel``. If for some reason it is not feasible (lets say you are using GeoDjango or something) you can extend ``smart_fields.models.SmartFieldsHandler`` and add required methods. Here is an example:

    class SmartFieldsModel(models.Model, smart_fields.models.SmartFieldsHandler):
        ... 
	fields
	...

        def __init__(self, *args, **kwargs):
            super(SmartFieldsModel, self).__init__(*args, **kwargs)
            self.smart_fields_init() ## !important. after the super call

        def save(self, old=None, *args, **kwargs):
            super(SmartFieldsModel, self).save(*args, **kwargs)
            self.smart_fields_save()  ## !important. after the super call

        def delete(self, *args, **kwargs):
            self.smart_fields_delete()  ## !important. before the super call
            super(SmartFieldsModel, self).delete(*args, **kwargs)

Now we need to specify what settings needs to be applied and to which fields. Here is an example: