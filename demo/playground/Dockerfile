FROM denoland/deno:2.5.6@sha256:3ea71953ff50e3ff15c377ead1a8521f624e2f43d27713675a8bed7b33f166aa
WORKDIR /app
COPY deno.json deno.lock main.js ./
RUN deno cache --frozen main.js
COPY pages ./pages
USER deno
EXPOSE 8000
CMD ["task", "start"]
