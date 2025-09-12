import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from services.cv_handling.src.cv_upload import upload_cv_to_s3

# Mocking boto3 client and secrets_loader
@patch('services.cv_handling.src.cv_upload.boto3.client')
@patch('services.cv_handling.src.cv_upload.secrets_loader.get_json_secret')
def test_upload_cv_to_s3_success(mock_get_json_secret, mock_boto_client, tmp_path):
    # Test successful upload and presigned URL generation
    # Setting up the mock responses
    mock_get_json_secret.return_value = {
        "AWS_ACCESS_KEY_ID": "fake_id",
        "AWS_SECRET_ACCESS_KEY": "fake_secret",
        "AWS_REGION": "eu-central-1"
    }
    # Mocking S3 client and its methods
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    mock_s3.generate_presigned_url.return_value = "http://presigned.url/fake_cv.pdf"
    test_file = tmp_path / "test_cv.pdf"
    test_file.write_bytes(b"ceva ceva nu stiu ceva")
    # Call the function
    url = upload_cv_to_s3(
        file_path=str(test_file),
        bucket_name="fake-bucket",
        object_name="cv/test_cv.pdf"
    )
    # Assertions
    mock_s3.upload_file.assert_called_once_with(str(test_file), "fake-bucket", "cv/test_cv.pdf")
    mock_s3.generate_presigned_url.assert_called_once()
    assert url == "http://presigned.url/fake_cv.pdf"


@patch('services.cv_handling.src.cv_upload.boto3.client')
@patch('services.cv_handling.src.cv_upload.secrets_loader.get_json_secret')
def test_upload_cv_to_s3_upload_error(mock_get_json_secret, mock_boto_client, tmp_path):
    # Test upload failure scenario
    # Setting up the mock responses
    mock_get_json_secret.return_value = {
        "AWS_ACCESS_KEY_ID": "fake_id",
        "AWS_SECRET_ACCESS_KEY": "fake_secret",
        "AWS_REGION": "eu-central-1"
    }
    # Mocking S3 client and its methods
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    mock_s3.upload_file.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'Upload error'}}, "UploadFile"
    )
    test_file = tmp_path / "test_cv.pdf"
    test_file.write_bytes(b"ceva ceva nu stiu ceva")
    # Call the function and expect an error
    with pytest.raises(RuntimeError, match="Failed uploading file to S3:"):
        upload_cv_to_s3(str(test_file), "fake-bucket", "cv/fake_cv.pdf")

@patch('services.cv_handling.src.cv_upload.boto3.client')
@patch('services.cv_handling.src.cv_upload.secrets_loader.get_json_secret')
def test_upload_cv_to_s3_presign_error(mock_get_json_secret, mock_boto_client, tmp_path):
    # Test presigned URL generation failure scenario
    # Setting up the mock responses
    mock_get_json_secret.return_value = {
        "AWS_ACCESS_KEY_ID": "fake_id",
        "AWS_SECRET_ACCESS_KEY": "fake_secret",
        "AWS_REGION": "eu-central-1"
    }
    # Mocking S3 client and its methods
    mock_s3 = MagicMock()
    mock_boto_client.return_value = mock_s3
    mock_s3.generate_presigned_url.side_effect = ClientError(
        {'Error': {'Code': '500', 'Message': 'Presign error'}}, "GeneratePresignedUrl"
    )
    test_file = tmp_path / "test_cv.pdf"
    test_file.write_bytes(b"ceva ceva nu stiu ceva")
    # Call the function and expect an error
    with pytest.raises(RuntimeError, match="Failed generating presigned URL:"):
        upload_cv_to_s3(str(test_file), "fake-bucket", "cv/fake_cv.pdf")
