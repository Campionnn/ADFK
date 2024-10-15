import sys
import types


_config = None


def load_config():
    global _config
    if _config is None:
        if getattr(sys, 'frozen', False):
            _config = types.ModuleType('config')
            exec(open("config.py").read(), _config.__dict__)
        else:
            import config
            _config = config
    return _config
