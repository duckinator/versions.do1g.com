def info_command(packages):
    cmd = 'sudo pkg update --quiet && sudo pkg rquery "%n %v %dn=%dv" {}'.format(' '.join(packages))

    # HACK/TODO: Figure out why the hell clang isn't an actual package?!
    if 'clang' in packages:
        cmd += ' && clang --version | head -n 1 | cut -d " " -f 2,4,9'

    return cmd


def parse_info(output):
    info = {}

    output = output.strip()
    lines = output.split("\n")
    for line in lines:
        pkg, version, dep = line.split(' ')
        if dep.startswith(pkg):
            version = dep.split('=')[1]
        version = version.split('_')[0]
        info[pkg] = version
    return info
