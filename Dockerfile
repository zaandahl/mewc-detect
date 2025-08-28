FROM zaandahl/mewc-torch:py310-cu117-torch2.0.1-no-tf

# ensure we’re using the venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
RUN ln -sf /opt/venv/bin/python /usr/local/bin/python && \
    ln -sf /opt/venv/bin/pip    /usr/local/bin/pip

# install MegaDetector WITHOUT pulling its deps (we provide them)
RUN /opt/venv/bin/python -m pip install --no-cache-dir --upgrade --no-deps megadetector

# hard-pin the ABI triplet so nothing “helpfully” upgrades it
RUN /opt/venv/bin/python -m pip install --no-cache-dir \
    "numpy==1.26.4" "opencv-python-headless==4.8.1.78"

# sanity check (uses venv)
RUN /opt/venv/bin/python - <<'PY'
import numpy, torch, torchvision, cv2
print('numpy', numpy.__version__)
print('torch', torch.__version__)
print('vision', torchvision.__version__)
print('cv2', cv2.__version__)
PY

# help check (uses venv)
RUN /opt/venv/bin/python -m megadetector.detection.run_detector_batch --help > /dev/null

# set the working directory in the container
WORKDIR /code

# Bundle MDv1000 (redwood) weights
RUN wget -O /code/md_v1000.0.0-redwood.pt \
    https://github.com/agentmorris/MegaDetector/releases/download/v1000.0/md_v1000.0.0-redwood.pt

# Default model (overridable at runtime)
ENV MD_MODEL=md_v1000.0.0-redwood.pt

# copy the content of the local src directory to the working directory
COPY src/ .

# run megadetector wrapper script (venv python)
CMD ["/opt/venv/bin/python","./mewc_runner.py"]
