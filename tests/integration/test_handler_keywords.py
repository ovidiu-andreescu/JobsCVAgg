import unittest
import boto3
import json
from moto import mock_aws
from unittest.mock import patch
import io
import os
import sys
from PyPDF2 import PdfWriter, PdfReader

SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'cv_handling', 'src'))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from services.cv_handling.src.handler_keywords import lambda_handler_keywords

# This is a helper function to create a dummy PDF for testing
def create_dummy_pdf(text):
    """Creates an in-memory PDF file with the given text."""
    output_pdf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(output_pdf)
    output_pdf.seek(0)
    return output_pdf.read()

@mock_aws
class TestLambdaHandlerKeywordsIntegration(unittest.TestCase):

    def setUp(self):
        """Set up mocked AWS resources."""
        self.s3_client = boto3.client("s3", region_name="eu-central-1")
        self.secretsmanager_client = boto3.client("secretsmanager", region_name="eu-central-1")

        self.bucket_name = "test-cv-bucket"
        self.s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
        )

        self.secretsmanager_client.create_secret(
            Name="aws/credentials",
            SecretString=json.dumps({
                #"AWS_ACCESS_KEY_ID": "testing",
                #"AWS_SECRET_ACCESS_KEY": "testing",
                "AWS_REGION": "eu-central-1"
            })
        )

    def tearDown(self):
        """Clean up mocked resources."""
        pass

    
    @patch('services.cv_handling.src.handler_keywords.extract_keywords')
    @patch('services.cv_handling.src.handler_keywords.parse_cv_from_s3')
    def test_lambda_handler_integration_success(self, mock_parse, mock_extract):
        """
        Test the lambda handler's integration with S3 and Secrets Manager.
        """
        cv_text = "Software Engineer with experience in Python and Cloud technologies like AWS."
        mock_parse.return_value = cv_text
        mock_extract.return_value = ["Software Engineer", "Python", "Cloud", "AWS"]

        pdf_content = create_dummy_pdf(cv_text)
        object_key = "incoming_cvs/test_cv.pdf"
        self.s3_client.put_object(Bucket=self.bucket_name, Key=object_key, Body=pdf_content)

        s3_event = {
            'Records': [{
                's3': {
                    'bucket': {
                        'name': 'test-cv-bucket'
                    },
                    'object': {
                        'key': 'incoming_cvs/test_cv.pdf'
                    }
                }
            }]
        }

        result = lambda_handler_keywords(s3_event, None)

        self.assertEqual(result['statusCode'], 200)
        body = json.loads(result['body'])
        self.assertEqual(body['message'], "Keywords extracted and uploaded successfully")

        expected_keywords_key = "cv_keywords/test_cv_keywords.json"
        self.assertEqual(body['keywords_file'], expected_keywords_key)

        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=expected_keywords_key)
        keywords_data = json.loads(response['Body'].read().decode('utf-8'))
        self.assertEqual(keywords_data, ["Software Engineer", "Python", "Cloud", "AWS"])

        mock_parse.assert_called_once()
        mock_extract.assert_called_once_with(cv_text)
