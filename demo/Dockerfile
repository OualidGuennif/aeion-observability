FROM node:24-trixie-slim@sha256:43b9ba1142b8dcf33fa8f922ca1be85714adc444e0586c7cf7726daaeabc1bea
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv ca-certificates git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home agent
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt /opt/demo/requirements.txt
RUN pip install --no-cache-dir -r /opt/demo/requirements.txt
COPY tokenizers.json fetch_tokenizers.py /opt/demo/
RUN python3 /opt/demo/fetch_tokenizers.py
COPY . /opt/demo
RUN chmod -R a-w /opt/demo && mkdir /data /work && chmod 700 /data && chmod 711 /work
WORKDIR /opt/demo/app
EXPOSE 8080
CMD ["python3", "server.py"]
