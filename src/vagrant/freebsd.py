def info_command(packages):
    return 'sudo pkg update --quiet && sudo pkg rquery "%n %v %dn=%dv" {}'.format(' '.join(packages))

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
