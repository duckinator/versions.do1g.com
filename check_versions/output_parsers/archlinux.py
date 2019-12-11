from .linux_common import common_parse_info


def setup_command():
    return None


def info_command(packages):
    # ArchLinux calls their python 3.x package 'python', not 'python3'.
    # Unlike basically everything else I've ever encountered.
    if 'python3' in packages:
        packages_copy = packages.copy()
        packages_copy[packages_copy.index('python3')] = 'python'
    return 'pacman -Syi --noprogressbar {}'.format(' '.join(packages_copy))


def parse_info(output):
    return common_parse_info('apt', output)
