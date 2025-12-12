FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY . .

RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir -e ".[dev]"

ENV ARBITR_MODE=test
RUN pytest test/test_arbitr_api.py -v --tb=short || exit 1

ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]


