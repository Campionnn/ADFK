import os
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

    new_config = config_template.strip()
    for key, value in current_config.items():
        if key == "config_version":
            continue
        try:
            if isinstance(value, str):
                new_config = new_config.replace(f'{key} = "{template_config[key]}"', f'{key} = "{value}"')
            else:
                new_config = new_config.replace(f'{key} = {template_config[key]}', f'{key} = {value}')
        except KeyError:
            pass

    with open("config.toml", "w") as f:
        f.write(new_config)

    print("Please fill in the new config.toml file")
    input("Press any key to exit")
    os._exit(0)


def load_config():
    global _config
    if _config is None:
        if not os.path.exists("config.toml"):
            from utils.templates import config_template
            with open("config.toml", "w") as f:
                f.write(config_template.strip())
            print("Config file created. Please fill in the necessary fields then relaunch.")
            input("Press enter to exit.")
            os._exit(0)

        update_config()

        _config = types.ModuleType('config')
        with open("config.toml", "rb") as f:
            toml_data = tomllib.load(f)
        _config.__dict__.update(toml_data)
    return _config
