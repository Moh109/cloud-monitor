# CloudGuard - containerized CSPM scanner.
# Build:  docker build -t cloudguard .
# Demo:   docker run --rm cloudguard scan --demo
# Real:   docker run --rm -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
#                 -e AWS_DEFAULT_REGION cloudguard scan --region us-east-1
FROM python:3.11-slim

# Non-root runtime user.
RUN useradd --create-home --uid 10001 scanner
WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "moto[all]>=5.0" cryptography

# Install the package.
COPY pyproject.toml README.md ./
COPY cloudguard ./cloudguard
RUN pip install --no-cache-dir .

USER scanner
ENTRYPOINT ["cloudguard"]
CMD ["scan", "--demo"]
