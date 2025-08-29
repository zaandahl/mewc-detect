FROM zaandahl/mewc-torch:py310-cu117-torch2.0.1-no-tf

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN ln -sf /opt/venv/bin/python /usr/local/bin/python && \
    ln -sf /opt/venv/bin/pip    /usr/local/bin/pip

RUN python -m pip install --no-cache-dir megadetector && \
    python -m pip install --no-cache-dir numpy==1.26.4

WORKDIR /code
RUN wget -O /code/md_v1000.0.0-redwood.pt https://github.com/agentmorris/MegaDetector/releases/download/v1000.0/md_v1000.0.0-redwood.pt
ENV MD_MODEL=md_v1000.0.0-redwood.pt
COPY src/ .
CMD ["/opt/venv/bin/python","./mewc_runner.py"]
