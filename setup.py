from setuptools import setup

setup(
    name="teamscale-cli",
    version="9.1.1",
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
        'gitpython==3.1.35',

        'gitdb2==4.0.10',

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
