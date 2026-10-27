FROM denoland/deno:2.5.6@sha256:3ea71953ff50e3ff15c377ead1a8521f624e2f43d27713675a8bed7b33f166aa AS deno
FROM node:24-trixie-slim@sha256:43b9ba1142b8dcf33fa8f922ca1be85714adc444e0586c7cf7726daaeabc1bea
# Linux bootstrap passes the host UID so bind-mounted run directories stay owned by it.
ARG AGENT_UID=10001
COPY --from=deno /usr/bin/deno /usr/local/bin/deno
# Tool targets for the host-side Flue harness: shell, ripgrep/find for grep/glob, Deno/Node for checks.
RUN apt-get update && apt-get install -y --no-install-recommends python3 git ca-certificates ripgrep findutils \
    && rm -rf /var/lib/apt/lists/* \
    && (getent passwd "${AGENT_UID}" >/dev/null || useradd --uid "${AGENT_UID}" --create-home agent) \
    && mkdir /sandbox && chown "${AGENT_UID}:${AGENT_UID}" /sandbox
# No harness, model catalog or expected results in the image: checks receive cases on stdin.
COPY agent/fs-helper.py /opt/demo/fs-helper.py
COPY fixtures/check-scenario.js /opt/demo/fixtures/check-scenario.js
RUN chmod -R a-w /opt/demo
WORKDIR /sandbox
USER ${AGENT_UID}:${AGENT_UID}
CMD ["/bin/sleep", "infinity"]
