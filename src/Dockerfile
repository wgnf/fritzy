# need:
# 1. mongo-db

FROM python:3

WORKDIR /usr/src/fritzy

COPY scripts/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "scripts/exec.py" ]