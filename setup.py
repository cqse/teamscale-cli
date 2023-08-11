from setuptools import setup

setup(
    name="teamscale-cli",
    version="8.8.0",
    author="Thomas Kinnen - CQSE GmbH",
    author_email="kinnen@cqse.eu",
    description=("Client for performing precommit analysis with Teamscale."),
    license="Apache",
    keywords="teamscale client precommit",
    url="https://github.com/cqse/teamscale-cli",
    packages=['teamscale_precommit_client'],
    long_description="Command line client for performing precommit analysis with Teamscale.",
    classifiers=[
        "Topic :: Utilities",
    ],
    entry_points={
        'console_scripts': [
            'teamscale-cli=teamscale_precommit_client.precommit_client:run'
        ]
    },
    install_requires=[
        'teamscale-client==7.1.1',
        'gitpython==3.1.32',

        # Required for gitpython, build fails without specifying a fixed version.
        # 2.0.6 is the latest version working with python 2.7 according to
        # https://github.com/gitpython-developers/gitdb/issues/61#issuecomment-590275845
        'gitdb2==2.0.6',

        # Required to compile to a native binary
        'nuitka==1.5.5'
    ],
    tests_require=[
        'teamscale-client',
        'pytest',
        'responses',
        'mock'
    ],
    setup_requires=["pytest-runner"]
)
