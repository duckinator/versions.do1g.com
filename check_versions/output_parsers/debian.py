from .linux_common import common_parse_info


def setup_command():
    return 'apt-get update'


def info_command(packages):
    return 'apt-cache show {}'.format(' '.join(packages))


def parse_info(output):
    return common_parse_info('apt', output)
