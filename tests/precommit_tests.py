import responses
import re
from unittest.mock import Mock
from unittest import TestCase
from teamscale_client.teamscale_client_config import TeamscaleClientConfig
from teamscale_precommit_client import PrecommitClient
from teamscale_client.utils import to_json

URL = 'http://localhost:8080'
PROJECT = 'test_project'
SUCCESS = 'success'
USERNAME = 'johndoe'
ACCESS_TOKEN = 'secret'
REPO_PATH = 'path/to/repo/'
ANALYZED_FILE = REPO_PATH + 'file.ext'
CURRENT_BRANCH ='my_feature_branch'


class PrecommitClientTest(TestCase):
    """Tests for the precommit client"""

    def __init__(self, methodName):
        super().__init__(methodName)
        self.precommit_client = None

    @responses.activate
    def test_two_added_precommit_findings(self):
        """Tests that changed files provoke the client to upload changes and interpret precommit results."""
        self.precommit_client = self._get_precommit_client(self._get_two_changed_files(), self._get_no_deleted_files())

        self.mock_precommit_findings_churn(added_findings=[1, 2])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [1, 2])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])

    @responses.activate
    def test_two_removed_precommit_findings(self):
        """Tests that removed findings are interpreted correctly."""
        self.precommit_client = self._get_precommit_client(self._get_two_changed_files(), self._get_no_deleted_files())

        self.mock_precommit_findings_churn(removed_findings=[1, 2])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [])
        self.assert_findings_ids(self.precommit_client.removed_findings, [1, 2])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])

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
        self.precommit_client = PrecommitClientTest._get_precommit_client(self._get_two_changed_files(),
                                                                          self._get_no_deleted_files(),
                                                                          fetch_existing_findings=True)
        self.mock_precommit_findings_churn(added_findings=[1, 2])
        self.mock_existing_findings(self.precommit_client._get_precommit_branch(), existing_findings=[1, 2, 4, 5, 6, 7])
        self.precommit_client.run()

        self.assert_findings_ids(self.precommit_client.added_findings, [1, 2])
        self.assert_findings_ids(self.precommit_client.removed_findings, [])
        self.assert_findings_ids(self.precommit_client.findings_in_changed_code, [])
        self.assert_findings_ids(self.precommit_client.existing_findings, [4, 5, 6, 7])

    @staticmethod
    def mock_precommit_findings_churn(added_findings=None, findings_in_changed_code=None, removed_findings=None):
        precommit_response = to_json(PrecommitClientTest._get_findings_churn(added_findings, findings_in_changed_code,
                                                              removed_findings))
        responses.add(responses.PUT, PrecommitClientTest.get_project_service_mock('pre-commit'), body=SUCCESS,
                      status=200)
        responses.add(responses.GET, PrecommitClientTest.get_project_service_mock('pre-commit'),
                      body=precommit_response, status=200, content_type="application/json", )

    @staticmethod
    def mock_existing_findings(branch, existing_findings=None):
        existing_findings_from_current_branch = to_json(PrecommitClientTest._get_findings_as_dicts(existing_findings))
        responses.add(responses.GET, PrecommitClientTest.get_project_service_mock('findings', branch),
                      body=existing_findings_from_current_branch, status=200,
                      content_type="application/json", )

    @staticmethod
    def get_global_service_mock(service_id):
        """Returns mock global service url"""
        return re.compile(r'%s/%s/.*' % (URL, service_id))

    @staticmethod
    def get_project_service_mock(service_id, branch=''):
        """Returns mock project service url"""
        return re.compile(r'%s/p/%s/%s/.*%s.*' % (URL, PROJECT, service_id, branch))

    @staticmethod
    def _get_precommit_client(changed_files, deleted_files, fetch_existing_findings=False):
        """Gets a precommit client some of whose methods are mocked out for testing."""
        responses.add(responses.GET, PrecommitClientTest.get_global_service_mock('service-api-info'), status=200,
                      content_type="application/json", body='{"apiVersion": 6}')
        precommit_client = PrecommitClient(PrecommitClientTest._get_precommit_client_config(),
                                           repository_path=REPO_PATH, analyzed_file=ANALYZED_FILE, verify=False,
                                           omit_links_to_findings=True, fetch_existing_findings=fetch_existing_findings)
        precommit_client._calculate_modifications = Mock()
        precommit_client.current_branch = CURRENT_BRANCH
        precommit_client._retrieve_current_branch = Mock()
        precommit_client.parent_commit_timestamp = 10
        precommit_client._retrieve_parent_commit_timestamp = Mock()
        precommit_client.changed_files = changed_files
        precommit_client.deleted_files = deleted_files
        PrecommitClient.PRECOMMIT_WAITING_TIME_IN_SECONDS = 0

        return precommit_client

    @staticmethod
    def _get_precommit_client_config():
        return TeamscaleClientConfig(URL, USERNAME, ACCESS_TOKEN, PROJECT)

    @staticmethod
    def _get_no_changed_files():
        return {}

    @staticmethod
    def _get_two_changed_files():
        return {REPO_PATH + 'file1.ext': 'def foo():\n  pass'}

    @staticmethod
    def _get_no_deleted_files():
        return []

    @staticmethod
    def _get_findings_churn(added_findings=None, findings_in_changed_code=None, removed_findings=None):
        return {"addedFindings": PrecommitClientTest._get_findings_as_dicts(added_findings),
                "findingsInChangedCode": PrecommitClientTest._get_findings_as_dicts(findings_in_changed_code),
                'removedFindings': PrecommitClientTest._get_findings_as_dicts(removed_findings)}

    @staticmethod
    def _get_findings_as_dicts(findings_number_list):
        if not findings_number_list:
            return []
        findings_dicts = []
        for finding_number in findings_number_list:
            findings_dict = {'id': str(finding_number), 'typeId': 'id%i' % finding_number,
                             'message': 'message%i' % finding_number, 'assessment': 'RED',
                             'location': {'uniformPath': ANALYZED_FILE, 'rawStartLine': finding_number}}
            findings_dicts.append(findings_dict)
        return findings_dicts

    def assert_findings_ids(self, actual_findings, expected_ids):
        """Asserts that the given findings have the specified ids."""
        actual_findings_ids = [int(actual_finding.finding_id) for actual_finding in actual_findings]
        self.assertListEqual(actual_findings_ids, expected_ids)