FROM node:22-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g browse \
    && npm cache clean --force

WORKDIR /app

COPY fetch_exam.py /app/fetch_exam.py
RUN chmod +x /app/fetch_exam.py \
    && mkdir -p /output

ENTRYPOINT ["python3", "/app/fetch_exam.py"]
CMD ["--output-dir", "/output"]
