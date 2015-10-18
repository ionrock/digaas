from setuptools import setup

setup(
    name='digaas',
    version='0.0.2',
    packages=['digaas'],
    install_requires=[
        'dnspython3',
        'mysqlclient',
        'oslo.config',
        'SQLAlchemy',
        'aiohttp',
    ],
)
