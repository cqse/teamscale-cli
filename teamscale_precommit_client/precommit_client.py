from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function

import datetime
import time
import os
import argparse

from teamscale_precommit_client.git_utils import get_current_branch, get_current_timestamp
from teamscale_precommit_client.git_utils import get_changed_files_and_content, get_deleted_files
from teamscale_precommit_client.data import PreCommitUploadData
from teamscale_client import TeamscaleClient
from teamscale_precommit_client.teamscale_config import TeamscaleConfig
from teamscale_precommit_client.git_utils import get_repo_root_from_file_in_repo

_PRECOMMIT_CONFIG_FILENAME = '.teamscale-precommit.config'

class PrecommitClient:
    """Client for precommit analysis"""
    def __init__(self, teamscale_config, repository_path, analyzed_file=None, verify=True):
        """Constructor"""
        self.repository_path = repository_path
        self.teamscale_client = TeamscaleClient(teamscale_config.url, teamscale_config.username,
                                                teamscale_config.access_token, teamscale_config.project_id,
                                                verify)
        self.analyzed_file = analyzed_file

    def upload_precommit_data(self):
        """Uploads the currently changed files for precommit analysis."""
        current_branch = get_current_branch(self.repository_path)
        self.teamscale_client.branch = current_branch
        parent_commit_timestamp = get_current_timestamp(self.repository_path)

        changed_files = get_changed_files_and_content(self.repository_path)
        deleted_files = get_deleted_files(self.repository_path)

        if not changed_files and not deleted_files:
            print("No changed files found. Forgot to `git add` new files?")
            exit(0)

        print("Uploading changes on branch '%s' in '%s'..." % (current_branch, self.repository_path))
        precommit_data = PreCommitUploadData(uniformPathToContentMap=changed_files, deletedUniformPaths=deleted_files)
        self.teamscale_client.upload_files_for_precommit_analysis(
            datetime.datetime.fromtimestamp(int(parent_commit_timestamp)), precommit_data)

    def wait_and_get_precommit_result(self):
        """Gets the current precommit results. Waits synchronously until server is ready. """
        return self.teamscale_client.get_precommit_analysis_results()

    def print_precommit_results_as_error_string(self, include_findings_in_changed_code=True,
                                                include_existing_findings=False, include_all_findings=False):
        """Print the current precommit results formatting them in a way, most text editors understand.

        Returns:
            `True`, if RED findings were among the new findings. `False`, otherwise.
        """
        added_findings, removed_findings, findings_in_changed_code = self.wait_and_get_precommit_result()

        print('New findings:')
        for formatted_finding in self._format_findings(added_findings):
            print(formatted_finding)

        if include_findings_in_changed_code:
            print('')
            print('Findings in changed code:')
            for formatted_finding in self._format_findings(findings_in_changed_code):
                print(formatted_finding)

        uniform_path = os.path.relpath(self.analyzed_file, self.repository_path)
        if include_all_findings:
            uniform_path = ''

        if include_existing_findings or include_all_findings:
            existing_findings = self.teamscale_client.get_findings(
                uniform_path=uniform_path,
                timestamp=datetime.datetime.fromtimestamp(int(get_current_timestamp(self.repository_path))))
            print('')
            print('Existing findings:')
            for formatted_finding in self._format_findings(existing_findings):
                print(formatted_finding)

        red_added_findings = list(filter(lambda finding: finding.assessment == "RED", added_findings))
        return len(red_added_findings) > 0

    def _format_findings(self, findings):
        """Formats the given findings as error or warning strings."""
        if len(findings) == 0:
            return ['> No findings.']
        sorted_findings = sorted(findings)
        return [os.path.join(self.repository_path, finding.uniformPath) + ':' + str(finding.startLine) + ':0: ' +
                self._severity_string(finding=finding) + ': ' + finding.message for finding in sorted_findings]

    def _severity_string(self, finding):
        """Formats the given finding's assessment as severity."""
        return 'error' if finding.assessment == 'RED' else 'warning'

def _parse_args():
    """Parses the precommit client command line arguments."""
    parser = argparse.ArgumentParser(description='Precommit analysis client for Teamscale.')
    parser.add_argument('path', metavar='path', type=str, nargs=1,
                        help='path to any file in the repository')
    parser.add_argument('--exclude-findings-in-changed-code', dest='exclude_findings_in_changed_code',
                        action='store_const', const=True, default=False,
                        help='Determines whether to exclude findings in changed code (default: False)')
    parser.add_argument('--fetch-existing-findings', dest='fetch_existing_findings', action='store_const',
                        const=True, default=False,
                        help='When this option is set, existing findings in the specified file are fetched in addition '
                             'to precommit findings. (default: False)')
    parser.add_argument('--fetch-all-findings', dest='fetch_all_findings', action='store_const',
                        const=True, default=False,
                        help='When this option is set, all existing findings in the repo are fetched in addition '
                             'to precommit findings. (default: False)')
    parser.add_argument('--fail-on-red-findings', dest='fail_on_red_findings', action='store_const',
                        const=True, default=False,
                        help='When this option is set, the precommit client will exit with a non-zero return value '
                             'whenever RED findings were among the precommit findings. (default: False)')
    parser.add_argument('--verify', default=True, type=_bool_or_string,
                        help="Path to different certificate file. See requests' verify parameter in"
                             "http://docs.python-requests.org/en/latest/user/advanced/#ssl-cert-verification"
                             "Other possible values: True, False (default: True)")
    return parser.parse_args()

def _bool_or_string(string):
    if string in ['t', 'true', 'True']:
        return True
    if string in ['f', 'false', 'False']:
        return False
    return string

def configure_precommit_client(config_file, repo_path, parsed_args):
    """Reads the precommit analysis configuration and creates a precommit client with the corresponding config."""
    return PrecommitClient(teamscale_config=TeamscaleConfig(config_file), repository_path=repo_path,
                           analyzed_file=parsed_args.path[0], verify=parsed_args.verify)

def run():
    """Performs precommit analysis."""
    parsed_args = _parse_args()
    repo_path = get_repo_root_from_file_in_repo(os.path.normpath(parsed_args.path[0]))
    if not repo_path or not os.path.exists(repo_path) or not os.path.isdir(repo_path):
        raise RuntimeError('Invalid path to file in repository: %s' % repo_path)

    config_file = os.path.join(repo_path, _PRECOMMIT_CONFIG_FILENAME)
    if not os.path.exists(config_file) or not os.path.isfile(config_file):
        raise RuntimeError('Config file could not be found: %s' % config_file)
    precommit_client = configure_precommit_client(config_file=config_file, repo_path=repo_path, parsed_args=parsed_args)

    precommit_client.upload_precommit_data()

    # We need to wait for the analysis to pick up the new code otherwise we get old findings.
    # This might not be needed in future releases of Teamscale.
    time.sleep(2)

    print('Waiting for precommit analysis results...')
    print('')
    red_findings_found = precommit_client.print_precommit_results_as_error_string(
        include_findings_in_changed_code=not parsed_args.exclude_findings_in_changed_code,
        include_existing_findings=parsed_args.fetch_existing_findings,
        include_all_findings=parsed_args.fetch_all_findings)

    if parsed_args.fail_on_red_findings and red_findings_found:
        exit(1)

if __name__ == '__main__':
    run()
