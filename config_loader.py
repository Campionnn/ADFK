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

    updated_config = template_config.copy()
    updated_config.update(current_config)

    with open("config.toml", "w") as f:
        for key, value in updated_config.items():
            if isinstance(value, str):
                f.write(f'{key} = "{value}"\n')
            else:
                f.write(f'{key} = {value}\n')


def load_config():
    global _config
    if _config is None:
        update_config()
        _config = types.ModuleType('config')
        with open("config.toml", "rb") as f:
            toml_data = tomllib.load(f)
        _config.__dict__.update(toml_data)
    return _config
