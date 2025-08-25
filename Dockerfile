# set base image (host OS)
#FROM zaandahl/mewc-torch:1.0
FROM zaandahl/mewc-torch

# set the working directory in the container
WORKDIR /code

# Install official MegaDetector package and bundle MDv1000 (redwood) weights
RUN pip install --no-cache-dir --upgrade megadetector
RUN wget -O /code/md_v1000.0.0-redwood.pt \
    https://github.com/agentmorris/MegaDetector/releases/download/v1000.0/md_v1000.0.0-redwood.pt

# Quick import/CLI check
RUN python -m megadetector.detection.run_detector_batch --help > /dev/null

# Default model (overridable at runtime)
ENV MD_MODEL=md_v1000.0.0-redwood.pt

ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/opt/conda/lib

# copy the content of the local src directory to the working directory
COPY src/ .

# run megadetector wrapper script
CMD [ "python", "./mewc_runner.py" ]
