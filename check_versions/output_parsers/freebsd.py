def info_command(packages):
    if 'clang' in packages:
        packages[packages.index('clang')] = 'llvm'

    return 'sudo pkg rquery "%n %v %dn=%dv" {}'.format(' '.join(packages))


def parse_info(output):
    info = {}

    output = output.strip()
    lines = output.split("\n")
    for line in lines:
        pkg, version, dep = line.split(' ')
        if dep.startswith(pkg):
            realpkg, version = dep.split('=')
        version = version.split('_')[0]
        info[pkg] = {
            'version': version,
            'via': None,
        }

        # clang is provided by the 'llvm<version>' package, in FreeBSD
        if pkg == 'llvm':
            info['clang'] = {
                'version': version,
                'via': pkg,
            }
            #info['clang'] = '{}:via={}'.format(version, pkg)

    return info
