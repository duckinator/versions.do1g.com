import os
from pathlib import Path
from subprocess import check_output, check_call

import vagrant.freebsd
import vagrant.dragonflybsd


class VagrantBox:
    def __init__(self, name):
        file_dir = Path(__file__).resolve().parent

        self.name = name
        self.folder = file_dir / '..' / '..' / 'vagrant-config' / name

    def up(self):
        check_call(["vagrant", "up"])

    def halt(self):
        check_call(["vagrant", "halt"])

    def destroy(self):
        check_call(["vagrant", "destroy"])

    def run(self, command):
        return check_output(["vagrant", "ssh", "-c", command]).decode()

    def get_info(self, packages):
        old_cwd = os.getcwd()
        os.chdir(self.folder)
        try:
            self.up()

            shortname = self.name.replace(' BSD ', 'BSD ').split(' ')[0].lower()

            module = {
                'dragonflybsd': dragonflybsd,
                'freebsd': freebsd,
            #    'netbsd': netbsd,
            #    'openbsd': openbsd,
            }[shortname]

            command = module.info_command(packages)
            output = self.run(command)

            result = module.parse_info(output)
        finally:
            self.halt()
            os.chdir(old_cwd)

        return result

def get_info(image, packages):
    return VagrantBox(image).get_info(packages)
