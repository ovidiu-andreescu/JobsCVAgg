import unittest
import boto3
import json
import base64
import os
import sys
from moto import mock_aws
from botocore.exceptions import ClientError
from unittest.mock import patch, MagicMock

from services.cv_handling.src.cv_upload import lambda_handler_upload

# Helper function to create a dummy PDF file content
def create_dummy_pdf_content(file_name="test_cv.pdf"):
    """Creates a simple, in-memory dummy PDF file content."""
    from PyPDF2 import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output_pdf = open(file_name, "wb")
    writer.write(output_pdf)
    output_pdf.close()
    
    with open(file_name, 'rb') as f:
        content = f.read()
    
    os.remove(file_name) # Clean up the temporary file
    return content


@mock_aws
class TestLambdaHandlerUploadIntegration(unittest.TestCase):

    def setUp(self):
        """Set up mocked AWS resources before each test."""
        self.s3_client = boto3.client("s3", region_name="eu-central-1")
        self.secretsmanager_client = boto3.client("secretsmanager", region_name="eu-central-1")
        
        # Define bucket name from secrets
        self.bucket_name = "test-cv-upload-bucket"
        self.secret_name = "aws/credentials"
        
        # Create a dummy S3 bucket
        self.s3_client.create_bucket(
            Bucket=self.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}
        )
        
        # Create a dummy secret
        self.secretsmanager_client.create_secret(
            Name=self.secret_name,
            SecretString=json.dumps({
                "AWS_ACCESS_KEY_ID": "testing",
                "AWS_SECRET_ACCESS_KEY": "testing",
                "AWS_REGION": "eu-central-1",
                "CV_S3_BUCKET": self.bucket_name
            })
        )

    def tearDown(self):
        """Clean up mocked resources."""
        # Moto automatically handles resource cleanup
        pass

    def test_lambda_handler_upload_success(self):
        """
        Test a successful file upload and presigned URL generation.
        """
        # --- Mocks & Test Data Setup ---
        file_name = "test_cv.pdf"
        pdf_content = create_dummy_pdf_content(file_name)
        encoded_pdf_content = base64.b64encode(pdf_content).decode('utf-8')

        # Mock event simulating an API Gateway request
        api_gateway_event = {
            "body": encoded_pdf_content,
            "isBase64Encoded": True,
            "headers": {
                "X-File-Name": file_name
            }
        }

        # --- Function Execution ---
        result = lambda_handler_upload(api_gateway_event, None)

        # --- Assertions ---
        # 1. Check the Lambda function's response
        self.assertEqual(result['statusCode'], 200)
        response_body = json.loads(result['body'])
        self.assertEqual(response_body['message'], "File uploaded successfully")
        self.assertIn('presigned_url', response_body)

        # 2. Verify the file exists in the mocked S3 bucket
        uploaded_object_key = f"cv_uploads/{file_name}"
        try:
            s3_object = self.s3_client.get_object(Bucket=self.bucket_name, Key=uploaded_object_key)
            uploaded_content = s3_object['Body'].read()
            self.assertEqual(uploaded_content, pdf_content)
        except ClientError as e:
            self.fail(f"File not found in S3: {e}")

    @patch('services.cv_handling.src.cv_upload.upload_cv_to_s3')
    def test_lambda_handler_upload_failure(self, mock_upload_cv_to_s3):
        """
        Test the lambda handler's graceful failure.
        """
        # Mock the dependency to raise an exception
        mock_upload_cv_to_s3.side_effect = RuntimeError("Mocked S3 upload error")

        # Create a dummy event
        file_name = "test_cv.pdf"
        pdf_content = create_dummy_pdf_content(file_name)
        encoded_pdf_content = base64.b64encode(pdf_content).decode('utf-8')
        api_gateway_event = {
            "body": encoded_pdf_content,
            "isBase64Encoded": True,
            "headers": {
                "X-File-Name": file_name
            }
        }

        # --- Function Execution ---
        result = lambda_handler_upload(api_gateway_event, None)

        # --- Assertions ---
        self.assertEqual(result['statusCode'], 500)
        response_body = json.loads(result['body'])
        self.assertIn("Mocked S3 upload error", response_body['error'])
        mock_upload_cv_to_s3.assert_called_once()