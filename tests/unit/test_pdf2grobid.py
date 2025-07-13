import unittest
from unittest.mock import patch, MagicMock
import os
from verrific.pdf2grobid import pdf_to_grobid

class TestPdf2Grobid(unittest.TestCase):

    def setUp(self):
        # Create a dummy PDF file for testing
        self.pdf_path = "dummy.pdf"
        with open(self.pdf_path, "w") as f:
            f.write("dummy pdf content")

    def tearDown(self):
        # Clean up the dummy PDF file
        if os.path.exists(self.pdf_path):
            os.remove(self.pdf_path)

    @patch('requests.post')
    def test_pdf2grobid_success(self, mock_post):
        # Mock the response from the GROBID server
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<xml>mocked grobid output</xml>"
        mock_post.return_value = mock_response

        # Call the function with the dummy PDF
        result = pdf_to_grobid(self.pdf_path)

        # Assert that the function returns the expected XML
        self.assertEqual(result, "<xml>mocked grobid output</xml>")

        # Assert that requests.post was called correctly
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_pdf2grobid_failure(self, mock_post):
        # Mock a failed response from the GROBID server
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Assert that the function raises an exception or handles the error as expected
        with self.assertRaises(Exception): # Or a more specific exception
            pdf_to_grobid(self.pdf_path)

