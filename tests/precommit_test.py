import os
import re
import sys
from io import StringIO

import responses

from teamscale_precommit_client.precommit_client import DEFAULT_PROJECT_SUBPATH

# The mock package is only available from Python 3.3 onwards. Thank you, Python.
if sys.version_info >= (3, 3):
    from unittest.mock import Mock
else:
    # This package is not needed in Python >= 3.3
    from mock import Mock
from unittest import TestCase
from teamscale_client.teamscale_client_config import TeamscaleClientConfig
from teamscale_precommit_client import PrecommitClient
from teamscale_precommit_client.precommit_client import DEFAULT_PATH_PREFIX
from teamscale_client.utils import to_json

URL = 'http://localhost:8080'
PROJECT = 'test_project'
SUCCESS = 'success'
USERNAME = 'johndoe'
ACCESS_TOKEN = 'secret'
REPO_PATH = 'path/to/repo/'
ANALYZED_FILE_NAME = 'file.ext'
ANALYZED_FILE_PATH = REPO_PATH + ANALYZED_FILE_NAME
DELETED_FILE_NAME = 'deletedFile.ext'
CURRENT_BRANCH = 'my_feature_branch'
REVISION = 'mockRevision'


class PrecommitClientTest(TestCase):
    """System tests for the precommit client."""

    def setUp(self):
        """Set up for precommit client tests."""
        self.precommit_client = None

    @responses.activate
    def test_two_added_precommit_findings(self):
        """Tests that changed files provoke the client to upload changes and interpret precommit results."""
        self.precommit_client = self._get_precommit_client(self._get_changed_file(), self._get_no_deleted_files())

        self.mock_precommit_findings_churn(added_findings=[1, 2])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [1, 2])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])

    @responses.activate
    def test_two_removed_precommit_findings(self):
        """Tests that removed findings are interpreted correctly."""
        self.precommit_client = self._get_precommit_client(self._get_changed_file(), self._get_no_deleted_files())

        self.mock_precommit_findings_churn(removed_findings=[1, 2])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [])
        self.assert_findings_ids(self.precommit_client.removed_findings, [1, 2])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])

    @responses.activate
    def test_two_precommit_findings_in_changed_code(self):
        """Tests that findings in changed code are interpreted correctly."""
        self.precommit_client = self._get_precommit_client(self._get_changed_file(), self._get_no_deleted_files())

        self.mock_precommit_findings_churn(findings_in_changed_code=[1, 2])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [1, 2])

    @responses.activate
    def test_no_changes(self):
        """Tests that calling the precommit client without changes does not yield any precommit findings
        and exits the client."""
        self.precommit_client = self._get_precommit_client(self._get_no_changed_files(), self._get_no_deleted_files())

        self.mock_precommit_findings_churn()
        with self.assertRaises(SystemExit):
            self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])

    @responses.activate
    def test_get_existing_findings_for_no_changes(self):
        """Tests that calling the precommit client without changes, but with the flag to retrieve existing findings
        yields the existing findings."""
        self.precommit_client = self._get_precommit_client(self._get_no_changed_files(), self._get_no_deleted_files(),
                                                           fetch_existing_findings=True)
        self.mock_precommit_findings_churn()
        self.mock_existing_findings(CURRENT_BRANCH, existing_findings=[3, 4, 5])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])
        self.assert_findings_ids(self.precommit_client.existing_findings, [3, 4, 5])

    @responses.activate
    def test_get_added_and_existing_findings_for_changes(self):
        """Tests that calling the precommit client with changes and with the flag to retrieve existing findings
        yields the added findings plus the existing findings (with potentially different locations) on the precommit
        branch.
        We check the latter by making the server mock return a different set than on the current branch."""
        self.precommit_client = self._get_precommit_client(self._get_changed_file(),
                                                           self._get_no_deleted_files(),
                                                           fetch_existing_findings=True)
        self.mock_precommit_findings_churn(added_findings=[1, 2])
        self.mock_existing_findings(self.precommit_client._get_precommit_branch(), existing_findings=[1, 2, 4, 5, 6, 7])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [1, 2])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])
        self.assert_findings_ids(self.precommit_client.existing_findings, [4, 5, 6, 7])

    @responses.activate
    def test_get_added_and_existing_findings_in_changes_for_changes(self):
        """Tests that calling the precommit client with changes and with the flag to retrieve existing findings
        yields the added findings plus the existing findings (with potentially different locations) on the precommit
        branch.
        We check the latter by making the server mock return a different set than on the current branch."""
        self.precommit_client = self._get_precommit_client(self._get_changed_file(),
                                                           self._get_no_deleted_files(),
                                                           fetch_existing_findings_in_changes=True)
        self.mock_precommit_findings_churn(added_findings=[1, 2])
        self.mock_existing_findings(self.precommit_client._get_precommit_branch(), existing_findings=[1, 2, 4, 5, 6, 7])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [1, 2])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])
        self.assert_findings_ids(self.precommit_client.existing_findings, [4, 5, 6, 7])

    @responses.activate
    def test_only_upload_files_in_project_subpath(self):
        project_subpath = 'project'
        path_outside_project = 'another_path'

        changed_file_in_project = os.path.join(project_subpath, ANALYZED_FILE_NAME)
        changed_file_outside_project = os.path.join(path_outside_project, ANALYZED_FILE_NAME)
        deleted_file_in_project = os.path.join(project_subpath, DELETED_FILE_NAME)
        deleted_file_outside_project = os.path.join(path_outside_project, DELETED_FILE_NAME)

        self.precommit_client = self._get_precommit_client(
            {changed_file_in_project: '',
             changed_file_outside_project: ''},
            [deleted_file_in_project, deleted_file_outside_project],
            project_subpath=project_subpath)
        self.mock_precommit_findings_churn()

        self.precommit_client.run()

        precommit_request = next(call.request for call in responses.calls if call.request.method == 'PUT')
        
        # Unescaping double slashes for the tests to succeed on windows 
        precommit_request_body = precommit_request.body.replace('\\\\', '\\')

        self.assertIn(changed_file_in_project, precommit_request_body)
        self.assertNotIn(changed_file_outside_project, precommit_request_body)
        self.assertIn(deleted_file_in_project, precommit_request_body)
        self.assertNotIn(deleted_file_outside_project, precommit_request_body)

    @responses.activate
    def test_only_print_findings_in_project_subpath(self):
        project_subpath = 'project'

        self.precommit_client = self._get_precommit_client(self._get_no_changed_files(), self._get_no_deleted_files(),
                                                           project_subpath=project_subpath, fetch_all_findings=True)
        # The mocked finding does not have the project sub-path
        self.mock_existing_findings(CURRENT_BRANCH, [1])

        captured_output = StringIO()
        sys.stdout = captured_output

        self.precommit_client.run()

        # We only mocked one finding which is not located under the project sub-path,
        # so we expect it to be removed in the output
        self.assertNotIn(ANALYZED_FILE_NAME, captured_output.getvalue())

    @responses.activate
    def test_adding_path_prefix(self):
        path_prefix = 'prefix'
        self.precommit_client = self._get_precommit_client(self._get_changed_file(),
                                                           [DELETED_FILE_NAME], path_prefix=path_prefix)
        self.mock_precommit_findings_churn(added_findings=[1], path_prefix=os.path.join(path_prefix, ''))
        self.precommit_client.run()

        changed_file_path_with_prefix = os.path.join(path_prefix, ANALYZED_FILE_NAME)
        deleted_file_path_with_prefix = os.path.join(path_prefix, DELETED_FILE_NAME)
        precommit_request = next(call.request for call in responses.calls if call.request.method == 'PUT')
        
        # Unescaping double slashes for the tests to succeed on windows
        precommit_request_body = precommit_request.body.replace('\\\\', '\\')

        # Check if the path prefix was applied and sent correctly in the request's body
        self.assertIn(changed_file_path_with_prefix, precommit_request_body)
        self.assertIn(deleted_file_path_with_prefix, precommit_request_body)

    @responses.activate
    def test_stripping_path_prefix(self):
        path_prefix = 'prefix'
        self.precommit_client = self._get_precommit_client(self._get_changed_file(),
                                                           [DELETED_FILE_NAME], path_prefix=path_prefix)
        self.mock_precommit_findings_churn(added_findings=[1], path_prefix=os.path.join(path_prefix, ''))

        captured_output = StringIO()
        sys.stdout = captured_output

        self.precommit_client.run()

        # Check if the path prefix was applied and sent correctly in the request's body
        self.assertNotIn(path_prefix, captured_output.getvalue())

    @responses.activate
    def test_apply_path_prefix_when_fetching_existing_findings(self):
        """ Tests whether the path prefix is applied when fetching existing findings in the analyzed file.
        We do this by checking if the path prefix appears in the url of the request for fetching the findings"""
        path_prefix = 'prefix'
        self.precommit_client = self._get_precommit_client(self._get_no_changed_files(), self._get_no_deleted_files(),
                                                           path_prefix=path_prefix, fetch_existing_findings=True)

        self.mock_existing_findings(CURRENT_BRANCH)
        self.precommit_client.run()
        existing_findings_request = next(
            call.request for call in responses.calls if call.request.method == 'GET' and 'findings' in call.request.url)

        self.assertIn(path_prefix, existing_findings_request.url)

    @responses.activate
    def test_apply_path_prefix_when_fetching_existing_findings_in_changes(self):
        """ Tests whether the path prefix is applied when fetching existing findings in changed files.
        We do this by checking if the path prefix appears in the url of the request for fetching the findings"""
        path_prefix = 'prefix'
        self.precommit_client = self._get_precommit_client(self._get_changed_file(), self._get_no_deleted_files(),
                                                           path_prefix=path_prefix,
                                                           fetch_existing_findings_in_changes=True)

        self.mock_precommit_findings_churn()
        self.mock_existing_findings(self.precommit_client._get_precommit_branch())
        self.precommit_client.run()
        existing_findings_request = next(
            call.request for call in responses.calls if call.request.method == 'GET' and 'findings' in call.request.url)

        self.assertIn(path_prefix, existing_findings_request.url)

    @staticmethod
    def mock_precommit_findings_churn(added_findings=None, findings_in_changed_code=None, removed_findings=None,
                                      path_prefix=DEFAULT_PATH_PREFIX):
        """Mocks returning the findings churn for the given added, removed, and findings in changed code.
        Findings can be provided as list of integers each of which represents a finding instance."""
        precommit_response = to_json(
            PrecommitClientTest._get_findings_churn(path_prefix, added_findings, findings_in_changed_code,
                                                    removed_findings))
        responses.add(responses.PUT, PrecommitClientTest.get_project_service_mock('pre-commit'), body=SUCCESS,
                      status=200)
        responses.add(responses.GET, PrecommitClientTest.get_project_service_mock('pre-commit'),
                      body=precommit_response, status=200, content_type="application/json", )

    @staticmethod
    def mock_existing_findings(branch, existing_findings=None, path_prefix=DEFAULT_PATH_PREFIX):
        """Mocks returning the given existing findings for the provided branch.
        Findings can be provided as list of integers each of which represents a finding instance."""
        existing_findings_from_current_branch = to_json(
            PrecommitClientTest._get_findings_as_dicts(existing_findings, path_prefix))
        responses.add(responses.GET,
                      PrecommitClientTest.get_project_service_mock('repository-timestamp-by-revision', REVISION),
                      body=to_json([{'branchName': branch, 'timestamp': 'HEAD'}]), status=200,
                      content_type='application/json')
        responses.add(responses.GET, PrecommitClientTest.get_project_service_mock('findings', branch),
                      body=existing_findings_from_current_branch, status=200,
                      content_type="application/json", )

    @staticmethod
    def get_global_service_mock(service_id):
        """Returns mock global service url."""
        return re.compile(r'%s/%s/.*' % (URL, service_id))

    @staticmethod
    def get_project_service_mock(service_id, branch=''):
        """Returns mock project service url."""
        return re.compile(r'%s/p/%s/%s/.*%s.*' % (URL, PROJECT, service_id, branch))

    @staticmethod
    def _get_precommit_client(changed_files, deleted_files, path_prefix=DEFAULT_PATH_PREFIX,
                              project_subpath=DEFAULT_PROJECT_SUBPATH, fetch_existing_findings=False,
                              fetch_existing_findings_in_changes=False, fetch_all_findings=False):
        """Gets a precommit client some of whose methods are mocked out for testing."""
        responses.add(responses.GET, PrecommitClientTest.get_global_service_mock('service-api-info'), status=200,
                      content_type="application/json", body='{"apiVersion": 6}')
        precommit_client = PrecommitClient(PrecommitClientTest._get_precommit_client_config(),
                                           repository_path=REPO_PATH, path_prefix=path_prefix,
                                           project_subpath=project_subpath, analyzed_file=ANALYZED_FILE_PATH,
                                           verify=False, omit_links_to_findings=True,
                                           fetch_all_findings=fetch_all_findings,
                                           fetch_existing_findings=fetch_existing_findings,
                                           fetch_existing_findings_in_changes=fetch_existing_findings_in_changes)
        precommit_client._calculate_modifications = Mock()
        precommit_client.current_branch = CURRENT_BRANCH
        precommit_client._retrieve_current_branch = Mock()
        precommit_client.parent_commit_timestamp = 10
        precommit_client._retrieve_parent_commit_timestamp = Mock()
        precommit_client.changed_files = changed_files
        precommit_client.deleted_files = deleted_files
        PrecommitClient.PRECOMMIT_WAITING_TIME_IN_SECONDS = 0
        precommit_client._get_commit_hash = Mock(return_value=REVISION)

        return precommit_client

    @staticmethod
    def _get_precommit_client_config():
        """Gets the precommit client config for the tests."""
        return TeamscaleClientConfig(URL, USERNAME, ACCESS_TOKEN, PROJECT)

    @staticmethod
    def _get_no_changed_files():
        """Helper that returns an empty dict of changed files and content."""
        return {}

    @staticmethod
    def _get_changed_file():
        """Helper that returns a single changed path and content."""
        return {ANALYZED_FILE_NAME: 'def foo():\n  pass'}

    @staticmethod
    def _get_no_deleted_files():
        """Helper that provides an empty list of deleted files."""
        return []

    @staticmethod
    def _get_findings_churn(path_prefix, added_findings=None, findings_in_changed_code=None, removed_findings=None):
        """Returns the precommit findings churn as dict for the provided findings number list.
        Findings can be provided as list of integers each of which represents a finding instance."""
        return {"addedFindings": PrecommitClientTest._get_findings_as_dicts(added_findings, path_prefix),
                "findingsInChangedCode": PrecommitClientTest._get_findings_as_dicts(findings_in_changed_code,
                                                                                    path_prefix),
                'removedFindings': PrecommitClientTest._get_findings_as_dicts(removed_findings, path_prefix)}

    @staticmethod
    def _get_findings_as_dicts(findings_number_list, path_prefix):
        """Transforms a list of integers each of which represents a finding instance into a list of dicts."""
        if not findings_number_list:
            return []
        findings_dicts = []
        for finding_number in findings_number_list:
            findings_dict = {'id': str(finding_number), 'typeId': 'id%i' % finding_number,
                             'message': 'message%i' % finding_number, 'assessment': 'RED',
                             'location': {'uniformPath': os.path.join(path_prefix, ANALYZED_FILE_NAME),
                                          'rawStartLine': finding_number}}
            findings_dicts.append(findings_dict)
        return findings_dicts

    def assert_findings_ids(self, actual_findings, expected_ids):
        """Asserts that the given findings have the specified ids."""
        actual_findings_ids = [int(actual_finding.finding_id) for actual_finding in actual_findings]
        self.assertListEqual(actual_findings_ids, expected_ids)

    def assert_findings_paths(self, actual_findings, expected_paths):
        """Asserts that the given findings have the specified paths."""
        actual_findings_paths = [actual_finding.uniformPath for actual_finding in actual_findings]
        self.assertListEqual(actual_findings_paths, expected_paths)
