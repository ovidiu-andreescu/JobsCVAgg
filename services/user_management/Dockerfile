FROM public.ecr.aws/lambda/python:3.12

WORKDIR /var/task

COPY requirements.txt ./requirements.txt
COPY ../../libs/common/requirements-common.txt ./common_requirements.txt

RUN pip install --no-cache-dir -r \
    requirements.txt -r common_requirements.txt

COPY src .
COPY ../../libs/common/src .

CMD [ "user_management.main.handler" ]