FROM python:3.11-bullseye AS base
WORKDIR /project
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS test
RUN chmod +x docker-entrypoint.sh
CMD ["./docker-entrypoint.sh"]

FROM base AS prod
RUN playwright install chromium
RUN playwright install-deps
# RUN apt install libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
#          libatk-bridge2.0-0 libcups2 libxcomposite1 libxdamage1 \ 
#          libxfixes3 libxrandr2 libgbm1 libdrm2 \
#          libxkbcommon0 libasound2 libatspi2.0-0
CMD [ "python", "worker.py" ]
