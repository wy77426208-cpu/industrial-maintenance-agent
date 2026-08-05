import yaml

def load_config(
    config_path,
    encoding: str = "utf-8"
) -> dict:
    """读取 YAML 配置文件。"""

    with open(config_path, "r", encoding=encoding) as file:
        config = yaml.load(
            file,
            Loader=yaml.FullLoader
        )

    return config