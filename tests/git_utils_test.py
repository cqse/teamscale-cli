import os
import unittest

from teamscale_precommit_client.git_utils import filter_changed_files


class GitUtilsTest(unittest.TestCase):
    """ Unit tests for git_utils.py """

    def test_filter_binary_files(self):
        """ Test that binary files are filtered before precommit analysis """
        test_dir = os.path.dirname(os.path.abspath(__file__))
        binary_file_name = "binary.png"
        files_for_precommit_analysis = filter_changed_files([binary_file_name], test_dir)
        self.assertEqual(files_for_precommit_analysis, [])
