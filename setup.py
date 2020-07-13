from setuptools import setup

setup(
    name="teamscale-cli",
    version="6.0.5",
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
          'pygit2'
    ],
    tests_require=[
          'teamscale-client',
          'pygit2',
          'pytest',
          'responses',
          'mock'
    ],
    setup_requires=["pytest-runner"]
)
