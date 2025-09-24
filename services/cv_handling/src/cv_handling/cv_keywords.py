import spacy
import json
import re
from spacy.matcher import Matcher
from botocore.exceptions import BotoCoreError, ClientError
from typing import List, Set

# Load the spacy model for English
nlp = spacy.load("en_core_web_md")

# Initialize the matcher with custom patterns
matcher = Matcher(nlp.vocab)
# Define patterns to match programming languages and technical terms
patterns = [
    {"label": "PROG_LANG", "pattern": [{"TEXT": {"REGEX": "^[a-zA-Z]$"}}, {"TEXT": {"IN": ["++", "#"]}}]},
    {"label": "TECH", "pattern": [{"TEXT": "."}, {"LOWER": "net"}]},
    {"label": "ACRONYM", "pattern": [{"IS_UPPER": True, "LENGTH": {"IN": [2, 3]}}]},
    {"label": "PROG_LANG", "pattern": [{"LOWER": {"IN": ["c", "r", "go"]}, "POS": "PROPN"}]}
]
# Add patterns to the matcher
for pat in patterns:
    matcher.add(pat["label"], [pat["pattern"]])

def clean_and_split_keywords(text:str) -> List[str]:
    # Clean and split the text into keywords
    text = text.replace('\n', ' ').replace('\r', '')
    potential_keywords = re.split(r'\s*[\&/,]\s*', text)
    cleaned_keywords = [keyword.strip() for keyword in potential_keywords if keyword.strip()]
    return cleaned_keywords

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

    # Process the text with spaCy
    doc = nlp(text)
    keywords: Set[str] = set()
    min_keyword_length = 3

    # Use the matcher to find patterns in the text
    matches = matcher(doc)
    # Extract matched phrases as keywords
    for match_id, start, end in matches:
        phrase = doc[start:end].text
        cleaned_list = clean_and_split_keywords(phrase)
        for keyword in cleaned_list:
            keywords.add(keyword.lower())

    # Extract noun chunks as candidate phrases
    general_candidate_phrases = []
    for chunk in doc.noun_chunks:
        general_candidate_phrases.append(chunk.text)

    # Extract named entities as keywords
    for ent in doc.ents:
        if ent.label_ in {"ORG", "GPE", "PRODUCT", "LANGUAGE", "WORK_OF_ART"}:
            general_candidate_phrases.append(ent.text)

    # Further clean and filter candidate phrases
    for phrase in general_candidate_phrases:
        cleaned_list = clean_and_split_keywords(phrase)
        for keyword in cleaned_list:
            final_keyword = keyword.lower()
            if len(final_keyword) >= min_keyword_length:
                 keywords.add(final_keyword)
    """# Remove person names from keywords
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            person_name = ent.text.lower().strip()
            if person_name in keywords:
                keywords.remove(person_name)
    """
    # Return unique keywords
    return sorted(list(keywords))

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
    