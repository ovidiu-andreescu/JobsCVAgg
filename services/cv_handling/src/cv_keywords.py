import spacy
import boto3
import json
from botocore.exceptions import BotoCoreError, ClientError
from typing import List

def extract_keywords(text: str) -> List[str]:
    """
    Extract keywords from the input text.
    Arguments:
    - text: The input text from which to extract keywords
    Returns:
    - A list of extracted keywords
    """
    # Return empty list if text is empty
    if not text:
        return []

    # Load the spacy model for English
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    keywords = []

    # Extract named entities as keywords
    for ent in doc.ents:
        keywords.append(ent.text)
    
    # Extract nouns, proper nouns, and adjectives as keywords
    for token in doc:
        if token.pos_ in {"NOUN", "PROPN", "ADJ"} and not token.is_stop and not token.is_punct:
            keywords.append(token.lemma_) # Use lemma to avoid duplicates

    # Return unique keywords
    return list(set(keywords))

def upload_keywords_to_s3(s3_client, bucket_name: str, object_name: str, keywords: list):
    try:
        keywords_json = json.dumps(keywords, indent = 2)
        s3_client.put_object(
            Bucket = bucket_name,
            Key = object_name,
            Body = keywords_json.encode('utf-8'),
            ContentType = "application/json"
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f"Failed uploading keywords to S3: {e}")
    