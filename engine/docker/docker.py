import os
import docker

from base import DATABASE_DIR
from common import settings
from engine.docker.image import Image
from engine.docker.parser import TarFileParser


def path_name(name):
    return name.replace(":", "_").replace('/', "-")


class DockerEngine(object):
    def __init__(self):
        self.client = None

        if settings.DOCKER.get("LOCAL"):
            self.client = docker.from_env()

        else:
            self.client = docker.DockerClient(base_url=settings.DOCKER.get('REMOTE')["URL"],
                                              timeout=settings.DOCKER.get('REMOTE')["TIMEOUT"])

    def get_image(self, name):
        image_path_name = path_name(name)

        image = self.client.images.get(name)

        self_database_path = os.path.join(DATABASE_DIR, image_path_name, image.id.replace("sha256:", ""))
        tarfile_path = os.path.join(self_database_path, "os.tar")

        if not os.path.exists(self_database_path):
            os.makedirs(self_database_path)

        if not os.path.exists(tarfile_path):
            with open(tarfile_path, "wb") as f:
                for chunk in image.save():
                    f.write(chunk)
                f.close()

        print("[+] Database path: ", self_database_path)

        return Image.parse(TarFileParser.open(tarfile_path, "r:tar"), self_database_path)
