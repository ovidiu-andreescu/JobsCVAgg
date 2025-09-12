import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from services.cv_handling.src.cv_parser import parse_cv_from_s3

# Mocking boto3 client and secrets_loader and PdfReader
@patch('services.cv_handling.src.cv_parser.boto3.client')
@patch('services.cv_handling.src.cv_parser.secrets_loader.get_json_secret')
@patch('services.cv_handling.src.cv_parser.PdfReader')
def test_parse_cv_from_s3_success(mock_pdf_reader, mock_get_json_secret, mock_boto_client):
    # Testing successful PDF parsing from S3
    # Mocking the PDF content and extraction
    fake_pdf_bytes = b"%PDF-1.4 fake pdf content"
    fake_text = "Sample CV text"
    # Setting up the mock responses
    mock_get_json_secret.return_value = {
        "AWS_ACCESS_KEY_ID": "fake_id",
        "AWS_SECRET_ACCESS_KEY": "fake_secret",
        "AWS_REGION": "eu-central-1"
    }
    # Mocking S3 client and its methods
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    mock_s3.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=fake_pdf_bytes))
    }
    # Mocking the PDF reader and its methods
    mock_page = MagicMock()
    mock_page.extract_text.return_value = fake_text
    mock_pdf_reader.return_value.pages = [mock_page]
    # Call the function
    result = parse_cv_from_s3("bucket", "cv.pdf")
    # Assertions
    assert fake_text in result
    # Verifying the S3 and PDF reader interactions
    mock_s3.get_object.assert_called_once_with(Bucket="bucket", Key="cv.pdf")
    mock_pdf_reader.assert_called_once()

@patch('services.cv_handling.src.cv_parser.boto3.client')
@patch('services.cv_handling.src.cv_parser.secrets_loader.get_json_secret')
def test_parse_cv_from_s3_client_error(mock_get_json_secret, mock_boto_client):
    # Test S3 client error scenario
    mock_get_json_secret.return_value = {
        "AWS_ACCESS_KEY_ID": "fake_id",
        "AWS_SECRET_ACCESS_KEY": "fake_secret",
        "AWS_REGION": "eu-central-1"
    }
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    # Mocking the S3 client error
    mock_s3.get_object.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'S3 error'}}, "GetObject"
    )
    # Call the function and expect an error
    with pytest.raises(RuntimeError, match="Failed fetching PDF from S3:"):
        parse_cv_from_s3("bucket", "cv.pdf")

@patch('services.cv_handling.src.cv_parser.boto3.client')
@patch('services.cv_handling.src.cv_parser.secrets_loader.get_json_secret')
@patch('services.cv_handling.src.cv_parser.PdfReader')
def test_parse_cv_from_s3_pdf_extract_error(mock_pdf_reader, mock_get_json_secret, mock_boto_client):
    # Test PDF text extraction error scenario
    # Setting up the mock responses
    fake_pdf_bytes = b"%PDF-1.4 fake pdf content"
    mock_get_json_secret.return_value = {
        "AWS_ACCESS_KEY_ID": "fake_id",
        "AWS_SECRET_ACCESS_KEY": "fake_secret",
        "AWS_REGION": "eu-central-1"
    }
    # Mocking S3 client and its methods
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    mock_s3.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=fake_pdf_bytes))
    }
    # Mocking the PDF reader to raise an exception on text extraction
    mock_page = MagicMock()
    mock_page.extract_text.side_effect = Exception("PDF error")
    mock_pdf_reader.return_value.pages = [mock_page]
    # Call the function
    result = parse_cv_from_s3("bucket", "cv.pdf")
    # Since extract_text raises an exception, the result should be empty
    assert result == ""
