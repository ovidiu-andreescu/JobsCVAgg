FROM public.ecr.aws/lambda/python:3.12 AS base

WORKDIR /var/task

COPY services/notifications/requirements.txt ./service_requirements.txt
RUN pip install --no-cache-dir -r service_requirements.txt

COPY services/notifications/src .

CMD [ "notifications.handler.handler" ]

