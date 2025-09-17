import unittest
import json
import sys
import os
from unittest.mock import patch, MagicMock


SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'cv_handling', 'src'))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from services.cv_handling.src.handler_keywords import lambda_handler_keywords

class TestLambdaHandlerKeywordsUnit(unittest.TestCase):

    @patch('services.cv_handling.src.handler_keywords.boto3.client')
    @patch('services.cv_handling.src.handler_keywords.secrets_loader.get_json_secret')
    @patch('services.cv_handling.src.handler_keywords.parse_cv_from_s3')
    @patch('services.cv_handling.src.handler_keywords.extract_keywords')
    @patch('services.cv_handling.src.handler_keywords.upload_keywords_to_s3')
    def test_lambda_handler_keywords_success(self, mock_upload, mock_extract, mock_parse, mock_secrets, mock_boto_client):
        """
        Test the lambda_handler_keywords function for a successful execution.
        Mocks all external dependencies to test the handler logic in isolation.
        """
        # --- Mocks Setup ---
        # Mock AWS credentials
        mock_secrets.return_value = {
            #"AWS_ACCESS_KEY_ID": "test_access_key",
            #"AWS_SECRET_ACCESS_KEY": "test_secret_key",
            "AWS_REGION": "eu-central-1"
        }

        # Mock S3 client from boto3
        mock_s3_client = MagicMock()
        mock_boto_client.return_value = mock_s3_client

        # Mock the functions called by the handler
        mock_parse.return_value = "This is the parsed CV text with skills like Python and AWS."
        mock_extract.return_value = ["Python", "AWS", "CV", "text", "skill"]
        # upload_keywords_to_s3 doesn't return anything, so no return_value needed

        # --- Test Event ---
        test_event = {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'test-bucket'
                    },
                    'object': {
                        'key': 'cv_uploads/my_cv.pdf'
                    }
                }
            }]
        }

        # --- Function Execution ---
        result = lambda_handler_keywords(test_event, None)

        # --- Assertions ---
        # Check that the secrets loader was called correctly
        mock_secrets.assert_called_once_with("aws/credentials")

        # Check that the S3 client was initialized correctly
        mock_boto_client.assert_called_once_with(
            "s3",
            aws_access_key_id="test_access_key",
            aws_secret_access_key="test_secret_key",
            region_name="eu-central-1"
        )

        # Check that the CV parsing function was called with correct arguments
        mock_parse.assert_called_once_with(mock_s3_client, 'test-bucket', 'cv_uploads/my_cv.pdf')

        # Check that the keyword extraction was called with the text from parsing
        mock_extract.assert_called_once_with("This is the parsed CV text with skills like Python and AWS.")

        # Check that the keyword upload function was called correctly
        expected_keywords_key = "cv_keywords/my_cv_keywords.json"
        mock_upload.assert_called_once_with(
            mock_s3_client,
            'test-bucket',
            expected_keywords_key,
            ["Python", "AWS", "CV", "text", "skill"]
        )

        # Check the overall result of the handler
        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['message'], "Keywords extracted and uploaded successfully")
        self.assertEqual(body['keywords_file'], expected_keywords_key)

    @patch('handler_keywords.secrets_loader.get_json_secret')
    def test_lambda_handler_keywords_exception(self, mock_secrets):
        """
        Test the lambda_handler_keywords function for a failure scenario.
        """
        # --- Mock Setup ---
        # Simulate an exception when trying to get secrets
        mock_secrets.side_effect = Exception("Could not retrieve secrets")

        # --- Test Event ---
        test_event = {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'test-bucket'
                    },
                    'object': {
                        'key': 'cv_uploads/my_cv.pdf'
                    }
                }
            }]
        }

        # --- Function Execution ---
        result = lambda_handler_keywords(test_event, None)

        # --- Assertions ---
        self.assertEqual(result['statusCode'], 500)
        body = json.loads(result['body'])
        self.assertEqual(body['error'], "Could not retrieve secrets")

