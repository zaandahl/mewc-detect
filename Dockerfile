# Frozen previous runtime; this release replaces its source with reviewed fixes.
FROM zaandahl/mewc-detect:6.0.0@sha256:d7684e9878f9130c50a3a85e9d10a9ca58ba8f0b10c866aaec45473161473bbf
WORKDIR /code
COPY src/ .

CMD ["python", "./mewc_runner.py"]
