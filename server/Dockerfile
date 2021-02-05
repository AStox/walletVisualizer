FROM python:3.8.7

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

RUN pip install --upgrade pip
RUN pip install pipenv

COPY Pipfile Pipfile.lock /usr/src/app/
RUN pipenv install --system --deploy --ignore-pipfile

COPY app ./app
COPY *.sh \ /usr/src/app/

CMD /usr/src/app/start-gunicorn.sh
# CMD /usr/src/app/start-gunicorn.sh

# ENTRYPOINT [ "flask" ]
# CMD ["run", "--host=0.0.0.0", "--port=5000"]