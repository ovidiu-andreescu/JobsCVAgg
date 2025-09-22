FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY requirements.txt ./service_requirements.txt
COPY ../../libs/common/requirements-common.txt ./common_requirements.txt

RUN pip install --no-cache-dir -r service_requirements.txt -r common_requirements.txt
RUN python -m spacy download en_core_web_md

COPY src .
COPY ../../libs/common/src .

CMD [ "cv_handler.handler.handler" ]

