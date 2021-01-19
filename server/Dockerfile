FROM python:3.8.7

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY Pipfile /usr/src/app
RUN pip install

ENTRYPOINT [ "flask" ]
CMD ["run", "--host=0.0.0.0", "--port=5000"]