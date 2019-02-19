from setuptools import setup

setup(
    name="teamscale-cli",
    version="4.8.1",
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
    install_requires=[
          'teamscale-client',
          'configparser',
          'pygit2'
    ],

    tests_require=[
          'pytest',
          'responses'
    ],
    setup_requires=["pytest-runner"]
)
