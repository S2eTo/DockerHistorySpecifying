import json
import os.path

from engine.docker.parser import TarFileParser


def has_change(command):
    if command.find("COPY file:") != -1 or command.find("ADD file:") != -1:
        return "file"
    elif command.find("COPY dir") != -1 or command.find("ADD dir:") != -1:
        return "dir"

    return False


class Image(object):

    def __init__(self, manifest, config, database_path):
        self.manifest = manifest
        self.config = config
        self.database_path = database_path

    def get_layers(self):
        return self.manifest.get("Layers")

    def get_history(self):
        return self.config.get("history")

    def dockerfile(self, _from):

        docker_file = open(os.path.join(self.database_path, "Dockerfile"), "w")

        docker_file.write(f"FROM {_from}\n\n")

        # 国内换源
        if _from.find("ubuntu") != -1:
            docker_file.write(
                'RUN sed -i "s@/archive.ubuntu.com/@/mirrors.163.com/@g" /etc/apt/sources.list && rm -rf /var/lib/apt/lists/*\n')

        cmd = "created_by"

        i = 0
        for history in self.get_history():
            history[cmd] = history[cmd].replace("\t", "")

            if i == 0 and history[cmd].find("ADD file:") != -1:
                continue

            i += 1

            if history[cmd].startswith("/bin/sh -c"):
                history[cmd] = history[cmd].replace("/bin/sh -c #(nop)", "").strip()

                history[cmd] = history[cmd].replace("/bin/sh -c", "RUN").strip()

            if history[cmd].find("ENV") != -1:
                env = history[cmd].split("=")
                env[1] = env[1].replace(" ", "")
                history[cmd] = "=".join(env)

            docker_file.write(history[cmd] + "\n")

    @staticmethod
    def parse(image: TarFileParser, database_path):
        manifest = json.loads(image.get_file_raw("manifest.json").decode())[0]
        config = json.loads(image.get_file_raw(manifest.get("Config")).decode())

        layers = manifest["Layers"][1:]
        histories = config["history"][1:]

        i = 1
        change_index = 0
        for history in histories:
            if not history.get("empty_layer"):
                created_by = history.get("created_by")
                layer = layers[change_index]
                config["history"][i]["layer"] = layer

                change_type = has_change(created_by)
                if change_type:

                    # 将 layer 中的文件解压出来
                    image.extract(layer, database_path)
                    layer_sha256, layer_tar = layer.split("/")
                    layer_path = os.path.join(database_path, layer_sha256)
                    layer_tarfile = os.path.join(layer_path, layer_tar)
                    files = TarFileParser.open(layer_tarfile, 'r:tar')

                    source_path = ""

                    if change_type == "dir":
                        _, dst_path = created_by.split(" in ")
                        dst_path = dst_path.strip().replace("/", "")
                        source_path = os.path.join(layer_path, dst_path)
                    elif change_type == "file":
                        for file in files:
                            if int(file.type.decode()) == 0:
                                op = ""
                                for s_path in file.path.split("/"):
                                    op = os.path.join(op, s_path)
                                source_path = os.path.join(layer_path, op)
                                files.extract(file.path, layer_path)

                    files.close()
                    os.remove(layer_tarfile)

                    n = created_by.split(" ")
                    n[4] = source_path
                    config["history"][i]["created_by"] = (" ".join(n)).replace("in ", "")

                change_index += 1

            i += 1

        return Image(manifest, config, database_path)
