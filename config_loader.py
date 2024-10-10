import sys
import types


def load_config():
    if getattr(sys, 'frozen', False):
        config = types.ModuleType('config')
        exec(open("config.py").read(), config.__dict__)
    else:
        import config
    return config
