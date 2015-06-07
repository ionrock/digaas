try:
    from setuptools import setup
    from setuptools.command.build_py import build_py
except ImportError:
    from distutils.core import setup
    from distutils.command.build_py import build_py

import os
import re

class my_build_py(build_py):
    def run(self):
        if not self.dry_run:
            # mkpath is a distutils helper to create directories
            target_dir = '/etc/digaas'
            self.mkpath(target_dir)

            # generate the environment file for the init script
            environment = re.sub(
                pattern="DIGAAS_DIR=.*",
                repl="DIGAAS_DIR=%s" % os.path.dirname(os.path.realpath(__file__)),
                string=open('digaas.env', 'r').read())

            with open(os.path.join(target_dir, 'environment'), 'w') as f:
                f.write(environment)

        # distutils uses old-style classes, so no super()
        build_py.run(self)

setup(
    cmdclass={'build_py': my_build_py},
    name='digaas',
    version='0.0.1',
    packages=['digaas'],
    install_requires=[
        'dnspython',
        'gevent',
        'Cython',
        'falcon',
        'redis',
        'uwsgi',
    ],
    data_files=[('/etc/init', ['digaas-server.conf'])],
)
