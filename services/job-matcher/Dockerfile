FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY services/job_matcher/requirements.txt ./service_requirements.txt
COPY libs/common/requirements-common.txt ./common_requirements.txt

RUN pip install --no-cache-dir -r service_requirements.txt -r common_requirements.txt

COPY services/job_matcher/src/ .
COPY libs/common/src/ .

CMD [ "job_matcher.handler.handler" ]

