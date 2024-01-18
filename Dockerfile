FROM python:3.11-slim-bookworm

RUN apt-get update && \
  apt install -y --no-install-recommends bash default-jre build-essential gcc && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./bin /app/bin

ENV PATH="/app/bin:${PATH}"

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . /app

RUN chmod a+x /app/bin/np
RUN pip install .

CMD ["uvicorn", "nanopub_submitter:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
