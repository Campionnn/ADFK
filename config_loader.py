import types
import tomllib


_config = None


def load_config():
    global _config
    if _config is None:
        _config = types.ModuleType('config')
        with open("config.toml", "rb") as f:
            toml_data = tomllib.load(f)
        _config.__dict__.update(toml_data)
    return _config
