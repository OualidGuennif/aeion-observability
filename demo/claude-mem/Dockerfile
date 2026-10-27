# Isolated local runtime; no global Claude Code/OpenCode hooks or provider credentials.
FROM oven/bun:1.3.12-debian@sha256:1b709c9dd883fc1af38c210f7ea5222c552a8d470ea73efbd4b8fcfee798a64b
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates procps curl \
    && rm -rf /var/lib/apt/lists/*
RUN git init /opt/claude-mem \
    && cd /opt/claude-mem \
    && git remote add origin https://github.com/thedotmack/claude-mem.git \
    && git fetch --depth 1 origin 93c82aac6ce14e1cbda02dff9aa4c16e0edfce57 \
    && git checkout --detach FETCH_HEAD \
    && rm -rf .git \
    && bun install --production --ignore-scripts
ENV HOME=/home/bun CLAUDE_MEM_DATA_DIR=/data CLAUDE_MEM_WORKER_HOST=0.0.0.0 \
    CLAUDE_MEM_WORKER_PORT=37777 CLAUDE_MEM_CHROMA_ENABLED=false \
    CLAUDE_MEM_TELEMETRY=0 DO_NOT_TRACK=1
RUN mkdir -p /data && chown -R bun:bun /data /home/bun
USER bun
WORKDIR /opt/claude-mem
CMD ["bun", "plugin/scripts/worker-service.cjs", "--daemon"]
