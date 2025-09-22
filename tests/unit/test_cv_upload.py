import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from services.cv_handling.src.cv_handling.cv_upload import upload_cv_to_s3

def test_upload_cv_to_s3_success(tmp_path):
    # Test successful upload and presigned URL generation
    # Create a mock S3 client to pass to the function
    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.return_value = "http://presigned.url/fake_cv.pdf"
    
    test_file = tmp_path / "test_cv.pdf"
    test_file.write_bytes(b"some content")
    
    # Call the function with the mock client
    url = upload_cv_to_s3(
        s3_client=mock_s3_client,
        file_path=str(test_file),
        bucket_name="fake-bucket",
        object_name="cv/test_cv.pdf"
    )
    
    # Assertions
    mock_s3_client.upload_file.assert_called_once_with(str(test_file), "fake-bucket", "cv/test_cv.pdf")
    mock_s3_client.generate_presigned_url.assert_called_once()
    assert url == "http://presigned.url/fake_cv.pdf"


def test_upload_cv_to_s3_upload_error(tmp_path):
    # Test upload failure scenario
    mock_s3_client = MagicMock()
    mock_s3_client.upload_file.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'Upload error'}}, "UploadFile"
    )
    
    test_file = tmp_path / "test_cv.pdf"
    test_file.write_bytes(b"some content")
    
    # Call the function and expect an error
    with pytest.raises(RuntimeError, match="Failed uploading file to S3:"):
        upload_cv_to_s3(mock_s3_client, str(test_file), "fake-bucket", "cv/fake_cv.pdf")

def test_upload_cv_to_s3_presign_error(tmp_path):
    # Test presigned URL generation failure scenario
    mock_s3_client = MagicMock()
    mock_s3_client.generate_presigned_url.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'Presign error'}}, "GeneratePresignedUrl"
    )
    
    test_file = tmp_path / "test_cv.pdf"
    test_file.write_bytes(b"some content")
    
    # Call the function and expect an error
    with pytest.raises(RuntimeError, match="Failed generating presigned URL:"):
        upload_cv_to_s3(mock_s3_client, str(test_file), "fake-bucket", "cv/fake_cv.pdf")