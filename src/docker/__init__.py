from subprocess import check_output, check_call

import docker.package_info


package_managers = {
    'archlinux': 'pacman',
    'debian': 'apt',
    'fedora': 'dnf',
    'opensuse': 'zypper',
    'ubuntu': 'apt',
}


def package_info_command(pkgman, packages):
    if pkgman == 'apt':
        return 'apt-get update && apt-cache show {}'.format(' '.join(packages))
    if pkgman == 'dnf':
        packages = list(map(lambda x: x + '.x86_64', packages))
        return 'dnf info --color=false {}'.format(' '.join(packages))
    if pkgman == 'pacman':
        # ArchLinux calls their python 3.x package 'python', not 'python3'.
        # Unlike basically everything else I've ever encountered.
        if 'python3' in packages:
            packages_copy = packages.copy()
            packages_copy[packages_copy.index('python3')] = 'python'
        return 'pacman -Syi --noprogressbar {}'.format(' '.join(packages_copy))
    if pkgman == 'zypper':
        return 'zypper --xmlout info {}'.format(' '.join(packages))

    raise Exception("Unknown package manager: {}".format(pkgman))


def docker_snippet(image_and_tag, packages):
    # <image name>:<tag> => <image name>
    image = image_and_tag.split(':')[0].split('/')[0]
    setup_snippet = package_info_command(package_managers[image], packages)
    return "printf -- '--START--\\n' && " + setup_snippet + " && printf -- '\\n--END--'"


def docker_run(image, command):
    full_command = ['docker', 'run', '--rm', '-t', image, 'sh', '-c', command]
    #return check_call(full_command)
    return check_output(full_command).decode()


def get_raw_info(image, packages):
    pkgman = package_managers[image.split(':')[0].split('/')[0]]
    command = docker_snippet(image, packages)
    raw_output = docker_run(image, command).replace('\r', '')
    info_output = raw_output.split("--START--\n")[1].split("\n--END--")[0]
    return package_info.parse(pkgman, info_output)


def get_info(image, packages):
    package_info = {}
    raw_info = get_raw_info(image, packages)
    for name in raw_info.keys():
        package_info[name] = raw_info[name]
    return package_info
