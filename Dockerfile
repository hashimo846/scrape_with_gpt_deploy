FROM python:3.9
USER root

RUN apt-get update
RUN pip install --upgrade pip
ADD requirements.txt /root/
RUN curl -sSL https://install.python-poetry.org | python3 -
RUN apt -y install rustc
RUN pip install -r /root/requirements.txt