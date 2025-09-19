FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY services/job_aggregator/requirements.txt ./job_agg_requirements.txt
COPY libs/common/requirements-common.txt ./common_requirements.txt

RUN pip install --no-cache-dir -r job_agg_requirements.txt -r common_requirements.txt

COPY services/job_aggregator/src/ .
COPY libs/common/src/ .

CMD [ "job_aggregator.handler.handler" ]
