from setuptools import setup

setup(
    name='digaas',
    version='0.0.2',
    packages=['digaas'],
    install_requires=[
        "dnspython",
        "SQLAlchemy",
        "falcon",
        "oslo.config",
    ],
)
