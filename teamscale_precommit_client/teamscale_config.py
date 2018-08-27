from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

from configparser import ConfigParser

class TeamscaleConfig:
    """Configuration parameters for connections to Teamscale"""
    def __init__(self, config_file):
        """Constructor
        """
        parser = ConfigParser()
        parser.read(config_file)

        self.url = parser.get('teamscale', 'url')
        self.username = parser.get('teamscale', 'username')
        self.access_token = parser.get('teamscale', 'access_token')
        self.project_id = parser.get('project', 'id')
