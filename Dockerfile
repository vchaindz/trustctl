FROM python:3.10.5-slim-buster

WORKDIR /app_demo

COPY requirements.txt requirements.txt
COPY regctl /usr/bin/regctl
RUN pip3 install -r requirements.txt
COPY trustctl.py trustctl.py

ENTRYPOINT [ "python", "trustctl.py" ]
