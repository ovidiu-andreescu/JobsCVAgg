from services.cv_handling.src.cv_handling.cv_upload import process

def handler(event, _context):
    rec = event["Records"][0]
    return process(rec["s3"]["bucket"]["name"], rec["s3"]["object"]["key"])
