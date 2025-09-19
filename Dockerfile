ARG SERVICE_NAME

FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY services/${SERVICE_NAME}/requirements.txt ./service_requirements.txt
COPY libs/common/requirements-common.txt ./common_requirements.txt

RUN pip install --no-cache-dir -r service_requirements.txt -r common_requirements.txt

COPY services/${SERVICE_NAME}/src/ .

COPY libs/common/src/ .

CMD [ "${SERVICE_NAME}.handler.handler" ]

