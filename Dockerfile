FROM python:3.5.3
MAINTAINER GetAtomo

WORKDIR /app

ADD . /app

RUN pip install --trusted-host pypi.org -r requirements.txt

EXPOSE 80

ENV NAME World

CMD [ "python", "__init__.py"]