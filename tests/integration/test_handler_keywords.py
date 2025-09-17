import unittest
import boto3
import json
from moto import mock_aws
from unittest.mock import patch
import io
import os
import sys

# Add the source directory to the Python path to allow for correct module imports
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'cv_handling', 'src'))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Import the main function from the refactored handler script
from services.cv_handling.src.handler_keywords import main

def create_dummy_pdf(text: str) -> bytes:
    """
    Creates an in-memory, PDF-like binary object for testing purposes.
    Note: This does not create a valid PDF structure but provides a binary object
    that can be uploaded to the mock S3 bucket. This is sufficient because
    the actual PDF parsing function is mocked in the test.

    Args:
        text: A string to be encoded into the binary object.

    Returns:
        A bytes object representing the dummy file content.
    """
    output_pdf = io.BytesIO()
    output_pdf.write(text.encode('utf-8'))
    output_pdf.seek(0)  # Rewind the buffer to the beginning
    return output_pdf.read()

@mock_aws
class TestMainHandlerKeywordsIntegration(unittest.TestCase):
    """
    Integration tests for the main keyword handler script.
    This test suite uses the 'moto' library to mock AWS services (S3, Secrets Manager),
    ensuring that the handler interacts correctly with AWS infrastructure without
    making real API calls.
    """

    def setUp(self):
        """
        Set up mocked AWS resources before each test runs.
        This method is called automatically by the unittest framework.
        """
        # Set up a mock S3 client and create a bucket for the test
        self.s3_client = boto3.client("s3", region_name="eu-central-1")
        self.bucket_name = "test-cv-bucket"
        self.s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
        )

        # Set up a mock Secrets Manager client and create a secret for the test
        self.secretsmanager_client = boto3.client("secretsmanager", region_name="eu-central-1")
        self.secretsmanager_client.create_secret(
            Name="aws/credentials",
            SecretString=json.dumps({"AWS_REGION": "eu-central-1"})
        )

    def tearDown(self):
        """
        Clean up resources after each test.
        Moto automatically handles the teardown of mocked AWS resources,
        so this method can be left empty.
        """
        pass
    
    @patch('services.cv_handling.src.handler_keywords.boto3.client')
    @patch('services.cv_handling.src.handler_keywords.extract_keywords')
    @patch('services.cv_handling.src.handler_keywords.parse_cv_from_s3') 
    @patch.dict(os.environ, {
        "S3_BUCKET": "test-cv-bucket",
        "S3_KEY": "incoming_cvs/test_cv.pdf"
    })
    # The order of mock arguments MUST be the reverse of the @patch decorator stack.
    def test_main_integration_success(self, mock_parse, mock_extract, mock_boto_client):
        """
        Test the main function's successful integration with S3 and Secrets Manager.
        This test verifies the orchestration logic of the handler, while the core
        business logic (parsing and keyword extraction) is mocked.
        """
        # --- ARRANGE ---
        # Configure the mocks and set up the initial state for the test.

        # Configure the mock for boto3.client to return the S3 client instance
        # created in setUp(). This ensures the handler uses our mock S3 environment.
        mock_boto_client.return_value = self.s3_client

        # Define the test data and the expected return values for the mocked functions.
        cv_text = "Software Engineer with experience in Python and Cloud technologies like AWS."
        expected_keywords = ["Software Engineer", "Python", "Cloud", "AWS"]

        # Set the return values for our mocked functions.
        mock_parse.return_value = cv_text
        mock_extract.return_value = expected_keywords

        # Create a dummy file and upload it to the mock S3 bucket to simulate the
        # input file that the handler is expected to process.
        pdf_content = create_dummy_pdf(cv_text)
        object_key = "incoming_cvs/test_cv.pdf"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=object_key, Body=pdf_content)

        # --- ACT ---
        # Execute the function being tested.
        main()

        # --- ASSERT ---
        # Verify that the outcomes and side effects are as expected.

        # 1. Verify that the final keywords JSON file was created in S3 with the correct content.
        expected_keywords_key = "cv_keywords/test_cv_keywords.json"
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=expected_keywords_key)
            keywords_data = json.loads(response['Body'].read().decode('utf-8'))
            self.assertEqual(keywords_data, expected_keywords)
        except self.s3_client.exceptions.NoSuchKey:
            self.fail(f"The expected keywords file '{expected_keywords_key}' was not found in the S3 bucket.")

        # 2. Verify that the mocked functions were called exactly once with the expected arguments.
        mock_parse.assert_called_once_with(self.s3_client, self.bucket_name, object_key)
        mock_extract.assert_called_once_with(cv_text)