class CloudExternalFileProcessorMixin(object):
    def get_input_path(self, in_file):
        return in_file.instance.file.url