FROM python:3.13-alpine

RUN apk add --no-cache \
    bash \
    openjdk21 \
    build-base

WORKDIR /app

ENV PATH="/app/bin:${PATH}"

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

RUN chmod a+x /app/bin/np
RUN pip install .

CMD ["uvicorn", "nanopub_submitter:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
