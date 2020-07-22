from setuptools import setup

setup(
    name="teamscale-cli",
    version="5.8.4",
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
        'teamscale-client',
        'gitpython==2.1.8'
    ],
    tests_require=[
        'teamscale-client',
        'gitpython==2.1.8',
        'pytest',
        'responses',
        'mock'
    ],
    setup_requires=["pytest-runner"]
)
