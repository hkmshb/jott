import configparser as cp


def open_config(filepath):
    config = cp.ConfigParser()
    try:
        config.read(filepath)
    except cp.Error:
        pass
    return config


def save_config(config, filepath):
    try:
        config.write(filepath)
    except cp.Error:
        pass
