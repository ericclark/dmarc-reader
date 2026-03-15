import unittest
from unittest.mock import patch, MagicMock
import os
from dmarc import process_dmarc_report

class TestDmarc(unittest.TestCase):
    def setUp(self):
        self.xml_file = 'sample_report.xml'

    @patch('dmarc.DbIpCity')
    def test_process_dmarc_report_success(self, mock_db):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.country = 'US'
        mock_db.get.return_value = mock_response

        html_snippet = process_dmarc_report(self.xml_file)

        # Check for expected content in HTML snippet
        self.assertIn('<h2>Org Name: google.com</h2>', html_snippet)
        self.assertIn('<p>Report ID: 1234567890</p>', html_snippet)
        self.assertIn('<td>1.2.3.4</td>', html_snippet)
        self.assertIn('<td>US</td>', html_snippet)
        self.assertIn('<td>1</td>', html_snippet)
        self.assertIn('<td>pass</td>', html_snippet)
        self.assertIn('<td>5.6.7.8</td>', html_snippet)
        self.assertIn('<td>fail</td>', html_snippet)

        # Verify mock was called for each IP
        self.assertEqual(mock_db.get.call_count, 2)
        mock_db.get.assert_any_call('1.2.3.4', api_key='free')
        mock_db.get.assert_any_call('5.6.7.8', api_key='free')

    @patch('dmarc.DbIpCity')
    def test_process_dmarc_report_ip_lookup_error(self, mock_db):
        # Setup mock to raise exception
        mock_db.get.side_effect = Exception("Lookup failed")

        html_snippet = process_dmarc_report(self.xml_file)

        # Check that country is "Unknown"
        self.assertIn('<td>Unknown</td>', html_snippet)
        self.assertIn('<td>1.2.3.4</td>', html_snippet)

    @patch('dmarc.DbIpCity', None)
    def test_process_dmarc_report_no_ip2geotools(self):
        # Test behavior when ip2geotools is not installed
        html_snippet = process_dmarc_report(self.xml_file)

        # Check that country is "Unknown"
        self.assertIn('<td>Unknown</td>', html_snippet)

if __name__ == '__main__':
    unittest.main()
