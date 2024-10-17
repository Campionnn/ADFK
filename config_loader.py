import types
import tomllib
from utils.templates import config_template


_config = None


def update_config():
    with open("config.toml", "rb") as f:
        current_config = tomllib.load(f)

    template_config = tomllib.loads(config_template)

    if current_config.get("config_version") == template_config.get("config_version"):
        return

    print("Mismatched config version, updating config.toml")

    for key, value in current_config.items():
        if key in template_config:
            template_config[key] = value

    with open("config.toml", "wb") as f:
        f.write(config_template.strip().encode())

    with open("config.toml", "r+") as f:
        content = f.read()
        for key, value in current_config.items():
            if isinstance(value, str):
                content = content.replace(f'{key} = "{template_config[key]}"', f'{key} = "{value}"')
            else:
                content = content.replace(f'{key} = {template_config[key]}', f'{key} = {value}')
        f.seek(0)
        f.write(content)
        f.truncate()


def load_config():
    global _config
    if _config is None:
        update_config()
        _config = types.ModuleType('config')
        with open("config.toml", "rb") as f:
            toml_data = tomllib.load(f)
        _config.__dict__.update(toml_data)
    return _config
