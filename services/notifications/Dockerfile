FROM public.ecr.aws/lambda/python:3.12 AS base

WORKDIR /var/task

COPY requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r service_requirements.txt

COPY src .

CMD [ "notifications.handler.handler" ]

