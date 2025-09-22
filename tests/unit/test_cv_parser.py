import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from services.cv_handling.src.cv_handling.cv_parser import parse_cv_from_s3

# Test the parsing of a CV from S3
@patch('services.cv_handling.src.cv_parser.PdfReader')
def test_parse_cv_from_s3_success(mock_pdf_reader):
    """Tests the parsing of a CV from S3 in the happy path scenario."""
    # Mock the S3 client and the PDF reader
    mock_s3_client = MagicMock()
    mock_page = MagicMock()

    fake_pdf_bytes = b"%PDF-1.4 fake pdf content"
    fake_text = "Sample CV text"
    
    # Configure the mocks
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=fake_pdf_bytes))
    }
    mock_page.extract_text.return_value = fake_text
    mock_pdf_reader.return_value.pages = [mock_page]

    # Call the function
    result = parse_cv_from_s3(mock_s3_client, "bucket_name", "cv.pdf")
            
    # Verify the result
    assert result == fake_text
    
    # Verify interactions with the mocks
    mock_s3_client.get_object.assert_called_once_with(Bucket="bucket_name", Key="cv.pdf")
    mock_pdf_reader.assert_called_once()


# Test an S3 client error
def test_parse_cv_from_s3_client_error():
    """Tests an S3 client error."""
    # Mock the S3 client to raise an exception
    mock_s3_client = MagicMock()
    mock_s3_client.get_object.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'S3 error'}}, "GetObject"
    )
    
    # Verify that the function raises an exception
    with pytest.raises(RuntimeError, match="Failed fetching PDF from S3:"):
        parse_cv_from_s3(mock_s3_client, "bucket_name", "cv.pdf")


# Test an error during PDF text extraction
@patch('services.cv_handling.src.cv_parser.PdfReader')
def test_parse_cv_from_s3_pdf_extract_error(mock_pdf_reader):
    """Tests an error during PDF text extraction."""
    # Mock the S3 client and the PDF reader
    mock_s3_client = MagicMock()
    mock_page = MagicMock()

    fake_pdf_bytes = b"%PDF-1.4 fake pdf content"
    
    # Configure the mocks
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=fake_pdf_bytes))
    }
    mock_page.extract_text.side_effect = Exception("PDF error")
    mock_pdf_reader.return_value.pages = [mock_page]
        
    # Call the function
    result = parse_cv_from_s3(mock_s3_client, "bucket_name", "cv.pdf")
            
    # Verify that the result is an empty string in case of an error
    assert result == ""
