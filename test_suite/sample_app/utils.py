import os, shutil
from django.conf import settings

def add_base(path):
    return os.path.join(settings.BASE_PATH, path)

def remove_folder_content(folder):
    # removes all of the content, but not the folder itself.
    for file in os.listdir(folder):
        file_path = os.path.join("media", file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            else:
                shutil.rmtree(file_path)
        except Exception as e:
            print(e)