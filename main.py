from engine.docker import DockerEngine

image = DockerEngine().get_image("docker.io/vulhub/fastjson:1.2.24")
print(image.get_history())
