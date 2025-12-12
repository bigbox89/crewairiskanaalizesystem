FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY . .

RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir -e ".[dev]"

ENV FNS_MODE=test
RUN pytest test/test_all_tools.py -v --tb=short || exit 1

RUN mkdir -p /certs

ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
