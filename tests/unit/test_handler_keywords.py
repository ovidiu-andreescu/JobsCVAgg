import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the source directory to the Python path to allow for correct module imports
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'cv_handling', 'src'))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Import the main function from the handler script
from services.cv_handling.src.cv_handling.handler_keywords import main

class TestMainHandlerKeywordsUnit(unittest.TestCase):
    """
    Unit tests for the main function in the handler_keywords script.
    """

    @patch('services.cv_handling.src.handler_keywords.boto3.client')
    @patch('services.cv_handling.src.handler_keywords.secrets_loader.get_json_secret')
    @patch('services.cv_handling.src.handler_keywords.parse_cv_from_s3')
    @patch('services.cv_handling.src.handler_keywords.extract_keywords')
    @patch('services.cv_handling.src.handler_keywords.upload_keywords_to_s3')
    @patch.dict(os.environ, {"S3_BUCKET": "test-bucket", "S3_KEY": "cv_uploads/my_cv.pdf"})
    def test_main_success(self, mock_upload, mock_extract, mock_parse, mock_secrets, mock_boto_client):
        """
        Test the main function for a successful execution path.
        Mocks all external dependencies and environment variables.
        """
        # --- Mocks Setup ---
        # Mock AWS credentials/config from Secrets Manager
        mock_secrets.return_value = {"AWS_REGION": "eu-central-1"}

        # Mock S3 client from boto3
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client

        # Mock the return values of the core processing functions
        mock_parse.return_value = "This is the parsed CV text with skills like Python and AWS."
        mock_extract.return_value = ["Python", "AWS", "CV", "text", "skill"]
        # upload_keywords_to_s3 doesn't return anything, so no return_value needed

        # --- Function Execution ---
        # The main function should run to completion without raising an exception
        main()

        # --- Assertions ---
        # Check that secrets were loaded
        mock_secrets.assert_called_once_with("aws/credentials")

        # Check that the S3 client was initialized correctly (without hardcoded keys)
        mock_boto_client.assert_called_once_with("s3", region_name="eu-central-1")

        # Check that the CV parsing function was called with correct arguments from env vars
        mock_parse.assert_called_once_with(mock_s3_client, 'test-bucket', 'cv_uploads/my_cv.pdf')

        # Check that keyword extraction was called with the parsed text
        mock_extract.assert_called_once_with("This is the parsed CV text with skills like Python and AWS.")

        # Check that the keyword upload function was called with the correct details
        expected_keywords_key = "cv_keywords/my_cv_keywords.json"
        mock_upload.assert_called_once_with(
            mock_s3_client,
            'test-bucket',
            expected_keywords_key,
            ["Python", "AWS", "CV", "text", "skill"]
        )

    @patch('services.cv_handling.src.handler_keywords.secrets_loader.get_json_secret')
    @patch.dict(os.environ, {"S3_BUCKET": "test-bucket", "S3_KEY": "cv_uploads/my_cv.pdf"})
    def test_main_exception_on_secrets(self, mock_secrets):
        """
        Test that main raises an exception if secrets_loader fails.
        """
        # --- Mock Setup ---
        # Simulate an exception when trying to retrieve secrets
        error_message = "Could not retrieve secrets"
        mock_secrets.side_effect = Exception(error_message)

        # --- Function Execution & Assertion ---
        # Verify that the exception is caught and re-raised by main()
        with self.assertRaises(Exception) as context:
            main()
        self.assertIn(error_message, str(context.exception))

    @patch.dict(os.environ, {}, clear=True)
    def test_main_missing_env_vars(self):
        """
        Test that main raises a ValueError if required environment variables are not set.
        """
        # --- Function Execution & Assertion ---
        # The 'clear=True' in patch.dict ensures no existing env vars interfere
        with self.assertRaises(ValueError) as context:
            main()
        self.assertIn("S3_BUCKET and S3_KEY environment variables must be set", str(context.exception))