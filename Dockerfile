FROM python:3
USER root

RUN apt-get update
RUN pip install --upgrade pip
ADD requirements.txt /root/
RUN pip install -r /root/requirements.txt