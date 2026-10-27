FROM denoland/deno:2.5.6@sha256:3ea71953ff50e3ff15c377ead1a8521f624e2f43d27713675a8bed7b33f166aa AS deno
FROM node:24-trixie-slim@sha256:43b9ba1142b8dcf33fa8f922ca1be85714adc444e0586c7cf7726daaeabc1bea
COPY --from=deno /usr/bin/deno /usr/local/bin/deno
RUN apt-get update && apt-get install -y --no-install-recommends python3 git ca-certificates ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g opencode-ai@1.19.4 && npm cache clean --force \
    && useradd --uid 10001 --create-home agent && mkdir /sandbox && chown 10001:10001 /sandbox
COPY context-gate.mjs gate-policy.mjs /opt/demo/
COPY agent/models.json /opt/demo/models.json
COPY fixtures /opt/demo/fixtures
COPY agent/process.py /opt/demo/agent-process.py
RUN chmod -R a-w /opt/demo
WORKDIR /sandbox
USER 10001:10001
CMD ["/bin/sleep", "infinity"]
