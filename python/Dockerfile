FROM python:3.12

RUN apt-get update
RUN apt-get install -y netcat-traditional
RUN pip3 install pip-tools

WORKDIR /usr/src/app

COPY pyproject.toml pyproject.toml
RUN pip-compile
RUN pip3 install -r requirements.txt

COPY . .

RUN pip install --compile --no-cache-dir --no-deps -e '.'

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
