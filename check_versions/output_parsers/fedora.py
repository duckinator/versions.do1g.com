from .linux_common import common_parse_info


def setup_command():
    return None


def info_command(packages):
    packages = list(map(lambda x: x + '.x86_64', packages))
    return 'dnf info --color=false {}'.format(' '.join(packages))


def parse_info(output):
    return common_parse_info('dnf', output)
