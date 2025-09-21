FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH="/app"

COPY libs/common/requirements-common.txt ./requirements-common.txt
COPY services/cv_handling/requirements.txt ./requirements-service.txt

RUN pip install --no-cache-dir -r requirements-common.txt
RUN pip install --no-cache-dir -r requirements-service.txt

RUN python -m spacy download en_core_web_md

COPY libs/ /app/libs
COPY services/cv_handling/src/ /app/services/cv_handling/src

CMD ["python", "handler_keywords.py"]
