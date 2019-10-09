import responses
import re
from unittest.mock import Mock
from unittest import TestCase
from teamscale_client.teamscale_client_config import TeamscaleClientConfig
from teamscale_precommit_client import PrecommitClient

URL = 'http://localhost:8080'
PROJECT = 'test_project'
SUCCESS = 'success'
USERNAME = 'johndoe'
ACCESS_TOKEN = 'secret'
REPO_PATH = 'path/to/repo/'
ANALYZED_FILE = REPO_PATH + 'file.ext'


class TestPrecommitClient(TestCase):

    @responses.activate
    def test_two_added_precommit_findings(self):
        """Tests that changed files provoke the client to upload changes and interpret precommit results."""
        self.mock_api_calls(precommit_response=self._get_two_added_findings())
        precommit_client = self._get_precommit_client(self._get_two_changed_files(), self._get_no_deleted_files())
        precommit_client.run()
        assert len(precommit_client.added_findings) == 2
        assert len(precommit_client.removed_findings) == 0
        assert len(precommit_client.findings_in_changed_code) == 0


    @responses.activate
    def test_two_removed_precommit_findings(self):
        """Tests that removed findings are interpreted correctly."""
        self.mock_api_calls(precommit_response=self._get_two_removed_findings())
        precommit_client = self._get_precommit_client(self._get_two_changed_files(), self._get_no_deleted_files())
        precommit_client.run()
        assert len(precommit_client.added_findings) == 0
        assert len(precommit_client.removed_findings) == 2
        assert len(precommit_client.findings_in_changed_code) == 0


    @responses.activate
    def test_no_changes(self):
        """Tests that calling the precommit client without changes does not yield any precommit findings
        and exits the client."""
        self.mock_api_calls()
        precommit_client = self._get_precommit_client(self._get_no_changed_files(), self._get_no_deleted_files())
        with self.assertRaises(SystemExit):
            precommit_client.run()
        assert len(precommit_client.added_findings) == 0
        assert len(precommit_client.removed_findings) == 0
        assert len(precommit_client.findings_in_changed_code) == 0


    @responses.activate
    def test_get_existing_findings_for_no_changes(self):
        """Tests that calling the precommit client without changes, but with the flag to retrieve existing findings
        yields the existing findings."""
        self.mock_api_calls(existing_findings_response=self._get_existing_findings_from_current_branch())
        precommit_client = self._get_precommit_client(self._get_no_changed_files(), self._get_no_deleted_files(),
                                                      fetch_existing_findings=True)
        precommit_client.run()
        assert len(precommit_client.added_findings) == 0
        assert len(precommit_client.removed_findings) == 0
        assert len(precommit_client.findings_in_changed_code) == 0
        assert len(precommit_client.existing_findings) == 15


    def mock_api_calls(self, precommit_response=None, existing_findings_response=None):
        responses.add(responses.GET, self.get_global_service_mock('service-api-info'), status=200,
                      content_type="application/json", body='{"apiVersion": 6}')
        responses.add(responses.PUT, self.get_project_service_mock('pre-commit'), body=SUCCESS, status=200)
        responses.add(responses.GET, self.get_project_service_mock('pre-commit'), body=precommit_response, status=200,
                      content_type="application/json", )
        responses.add(responses.GET, self.get_project_service_mock('findings'), body=existing_findings_response, status=200,
                      content_type="application/json", )

    def get_global_service_mock(self, service_id):
        """Returns mock global service url"""
        return re.compile(r'%s/%s/.*' % (URL, service_id))

    def get_project_service_mock(self, service_id):
        """Returns mock project service url"""
        return re.compile(r'%s/p/%s/%s/.*' % (URL, PROJECT, service_id))


    def _get_precommit_client(self, changed_files, deleted_files, fetch_existing_findings=False):
        """Gets a precommit client some of whose methods are mocked out for testing."""
        precommit_client = PrecommitClient(self._get_precommit_client_config(), repository_path=REPO_PATH,
                                           analyzed_file=ANALYZED_FILE, verify=False, omit_links_to_findings=True,
                                           fetch_existing_findings=fetch_existing_findings)
        precommit_client.calculate_modifications = Mock()
        precommit_client._retrieve_current_branch = Mock()
        precommit_client._retrieve_parent_commit_timestamp = Mock(return_value=10)
        precommit_client.changed_files = changed_files
        precommit_client.deleted_files = deleted_files
        PrecommitClient.PRECOMMIT_WAITING_TIME_IN_SECONDS = 0

        return precommit_client


    def _get_precommit_client_config(self):
        return TeamscaleClientConfig(URL, USERNAME, ACCESS_TOKEN, PROJECT)


    def _get_no_changed_files(self):
        return {}


    def _get_two_changed_files(self):
        return {REPO_PATH + 'file1.ext': 'def foo():\n  pass'}


    def _get_two_added_findings(self):
        return b'{"addedFindings":[{"groupName":"Nesting Depth","categoryName":"Structure","message":"Violation of nesting depth threshold of 5: 6","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":3830,"rawEndOffset":3873,"rawStartLine":112,"rawEndLine":114},"id":"7C6A3792C1BE2E6973D12F7CF8368F72","birth":{"branchName":"__precommit__dpagano","timestamp":1570572496160,"parentCommits":[{"branchName":"master","timestamp":1569600031000}]},"assessment":"RED","properties":{"Value":6},"analysisTimestamp":-1,"typeId":"Metric Violations/Nesting Depth"},{"groupName":"Task tags","categoryName":"Documentation","message":"TODO: Left this here.","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":3713,"rawEndOffset":3733,"rawStartLine":104,"rawEndLine":104},"id":"751D5E656D1DD4C5E3297D34BBBB77CD","birth":{"branchName":"__precommit__dpagano","timestamp":1570572496160,"parentCommits":[{"branchName":"master","timestamp":1569600031000}]},"assessment":"YELLOW","properties":{},"analysisTimestamp":-1,"typeId":"Comments/Task Tags"}],"findingsInChangedCode":[],"removedFindings":[],"numberOfAddedFindings":2,"numberOfFindingsInChangedCode":0,"numberOfRemovedFindings":0}'


    def _get_two_removed_findings(self):
        return b'{"removedFindings":[{"groupName":"Nesting Depth","categoryName":"Structure","message":"Violation of nesting depth threshold of 5: 6","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":3830,"rawEndOffset":3873,"rawStartLine":112,"rawEndLine":114},"id":"7C6A3792C1BE2E6973D12F7CF8368F72","birth":{"branchName":"__precommit__dpagano","timestamp":1570572496160,"parentCommits":[{"branchName":"master","timestamp":1569600031000}]},"assessment":"RED","properties":{"Value":6},"analysisTimestamp":-1,"typeId":"Metric Violations/Nesting Depth"},{"groupName":"Task tags","categoryName":"Documentation","message":"TODO: Left this here.","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":3713,"rawEndOffset":3733,"rawStartLine":104,"rawEndLine":104},"id":"751D5E656D1DD4C5E3297D34BBBB77CD","birth":{"branchName":"__precommit__dpagano","timestamp":1570572496160,"parentCommits":[{"branchName":"master","timestamp":1569600031000}]},"assessment":"YELLOW","properties":{},"analysisTimestamp":-1,"typeId":"Comments/Task Tags"}],"findingsInChangedCode":[],"addedFindings":[],"numberOfAddedFindings":0,"numberOfFindingsInChangedCode":0,"numberOfRemovedFindings":2}'


    def _get_no_deleted_files(self):
        return []

    def _get_existing_findings_from_current_branch(self):
        return b'[{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":12356,"rawEndOffset":12413,"rawStartLine":358,"rawEndLine":358},"id":"1AEFFBFCD440BB1BD3F0EDD50030F358","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13908,"rawEndOffset":13944,"rawStartLine":410,"rawEndLine":410},"id":"32EB24F8AC74A891F58700524FEC650B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":7279,"rawEndOffset":7310,"rawStartLine":208,"rawEndLine":208},"id":"3BF0485A8FB4596664958D94817B5E5B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":2885,"rawEndOffset":2909,"rawStartLine":70,"rawEndLine":70},"id":"3D8A3E599CD69239C21C61E13BEF98DA","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13283,"rawEndOffset":13439,"rawStartLine":389,"rawEndLine":389},"id":"3E444B1910B7B2B7E26CBD118DAEE2FD","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13556,"rawEndOffset":13616,"rawStartLine":395,"rawEndLine":395},"id":"6502D12BAE18423CD364BD41DC9B3A82","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":14649,"rawEndOffset":14697,"rawStartLine":440,"rawEndLine":440},"id":"894BDAE4BD4857FE62A759721770571B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"File Size","categoryName":"Structure","message":"Violation of file size threshold (source lines of code) of 300: 302","location":{"type":"ElementLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m"},"id":"9AEB53CEFBB974692AF875B504F7E88E","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Value":302},"analysisTimestamp":-1,"typeId":"Metric Violations/SLOC"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":14029,"rawEndOffset":14069,"rawStartLine":418,"rawEndLine":418},"id":"9C7DBF6371C3BAB820FDBC177F27C777","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13451,"rawEndOffset":13544,"rawStartLine":392,"rawEndLine":392},"id":"BA353032C677898D5467298D6B8992DF","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Method Length","categoryName":"Structure","message":"Violation of method length threshold (source lines of code) of 30: 62","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":4306,"rawEndOffset":6565,"rawStartLine":120,"rawEndLine":188},"id":"BB76C1A56F894FEA5F30D35A6822D42A","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Value":62},"analysisTimestamp":-1,"typeId":"Metric Violations/LSL"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":9192,"rawEndOffset":9234,"rawStartLine":262,"rawEndLine":262},"id":"BF9C606F66FC0A76BFFED1FCAD8ABFBD","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":2827,"rawEndOffset":2840,"rawStartLine":68,"rawEndLine":68},"id":"DA07E0E43DCFD08717E4C0B990100BCE","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13630,"rawEndOffset":13656,"rawStartLine":398,"rawEndLine":398},"id":"DB5A36834A8D5B3A18269B0EB8470DBD","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":7758,"rawEndOffset":7823,"rawStartLine":219,"rawEndLine":219},"id":"E29A47A109BE0C8150E4D2092E282D4B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"}]'

    # def _get_existing_findings_from_precommit_branch(self):
    #     return b'[{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":12356,"rawEndOffset":12413,"rawStartLine":358,"rawEndLine":358},"id":"1AEFFBFCD440BB1BD3F0EDD50030F358","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13908,"rawEndOffset":13944,"rawStartLine":410,"rawEndLine":410},"id":"32EB24F8AC74A891F58700524FEC650B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":7279,"rawEndOffset":7310,"rawStartLine":208,"rawEndLine":208},"id":"3BF0485A8FB4596664958D94817B5E5B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":2885,"rawEndOffset":2909,"rawStartLine":70,"rawEndLine":70},"id":"3D8A3E599CD69239C21C61E13BEF98DA","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13283,"rawEndOffset":13439,"rawStartLine":389,"rawEndLine":389},"id":"3E444B1910B7B2B7E26CBD118DAEE2FD","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13556,"rawEndOffset":13616,"rawStartLine":395,"rawEndLine":395},"id":"6502D12BAE18423CD364BD41DC9B3A82","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":14649,"rawEndOffset":14697,"rawStartLine":440,"rawEndLine":440},"id":"894BDAE4BD4857FE62A759721770571B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"File Size","categoryName":"Structure","message":"Violation of file size threshold (source lines of code) of 300: 302","location":{"type":"ElementLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m"},"id":"9AEB53CEFBB974692AF875B504F7E88E","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Value":302},"analysisTimestamp":-1,"typeId":"Metric Violations/SLOC"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":14029,"rawEndOffset":14069,"rawStartLine":418,"rawEndLine":418},"id":"9C7DBF6371C3BAB820FDBC177F27C777","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13451,"rawEndOffset":13544,"rawStartLine":392,"rawEndLine":392},"id":"BA353032C677898D5467298D6B8992DF","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Method Length","categoryName":"Structure","message":"Violation of method length threshold (source lines of code) of 30: 62","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":4306,"rawEndOffset":6565,"rawStartLine":120,"rawEndLine":188},"id":"BB76C1A56F894FEA5F30D35A6822D42A","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Value":62},"analysisTimestamp":-1,"typeId":"Metric Violations/LSL"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":9192,"rawEndOffset":9234,"rawStartLine":262,"rawEndLine":262},"id":"BF9C606F66FC0A76BFFED1FCAD8ABFBD","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":2827,"rawEndOffset":2840,"rawStartLine":68,"rawEndLine":68},"id":"DA07E0E43DCFD08717E4C0B990100BCE","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":13630,"rawEndOffset":13656,"rawStartLine":398,"rawEndLine":398},"id":"DB5A36834A8D5B3A18269B0EB8470DBD","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"},{"groupName":"Formatting","categoryName":"Code Anomalies","message":"if statement without braces","location":{"type":"TextRegionLocation","location":"Source/SPTooltip.m","uniformPath":"Source/SPTooltip.m","rawStartOffset":7758,"rawEndOffset":7823,"rawStartLine":219,"rawEndLine":219},"id":"E29A47A109BE0C8150E4D2092E282D4B","birth":{"branchName":"master","timestamp":1546462482000},"assessment":"YELLOW","properties":{"Check":"Missing braces for block statements"},"analysisTimestamp":-1,"typeId":"Code Anomalies/Missing braces for block statements"}]'
