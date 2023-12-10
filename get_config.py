from yaml import load, Loader, dump, Dumper
from os import getenv, makedirs
from os.path import join, exists


def get_config():
    """
    Method to read and load the config file.

    :return: The loaded config object from the config file.
    """
    # read config file
    directory = join(getenv('HOME'), '.config')
    # create a default config file is not exists
    if not exists(directory):
        makedirs(directory)
    config_file = join(directory, 'o2eb.yml')
    if not exists(config_file):
        _config = {
            "sqlite": {"db": join(getenv('HOME'), "observations.sqlite")},
            "mysql": {"db": "observations", "host": "localhost", "port": "3306"},
            "default": {"db_dialect": "sqlite"}
        }
        dump(_config, open(config_file, 'w'), Dumper=Dumper)

    try:
        return load(open(config_file, 'r'), Loader=Loader)
    except IOError:
        print('Config file not found!')
        return None


def write_config_file(new_config):
    directory = join(getenv('HOME'), '.config')
    # create a default config file is not exists
    if not exists(directory):
        makedirs(directory)
    config_file = join(directory, 'o2eb.yml')
    dump(new_config, open(config_file, 'w'), Dumper=Dumper)