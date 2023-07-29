# the context to build this Dockerfile is in the parent-folder './src/'!

FROM python:3

WORKDIR /usr/src/fritzy

COPY ./scripts/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./scripts .
COPY .env .

CMD [ "python", "-u", "exec.py" ]