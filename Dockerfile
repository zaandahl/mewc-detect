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

# download the megadetector models
RUN wget -O /code/md_v4.1.0.pb https://lilablobssc.blob.core.windows.net/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb
RUN wget -O /code/md_v5a.0.0.pt https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5a.0.0.pt
RUN wget -O /code/md_v5b.0.0.pt https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5b.0.0.pt

# clone megadetector repos
#RUN git clone https://github.com/Microsoft/cameratraps
#WORKDIR /code/cameratraps
#RUN git reset --hard fc8cdf71064b54241a63db9c80bf35e117886911

# Using pip-installed megadetector; remove repo clones
#WORKDIR /code/ai4eutils
#RUN git reset --hard 1bbbb8030d5be3d6488ac898f9842d715cdca088

#WORKDIR /code
# Removed yolov5 clone (not needed with package)
#RUN git clone https://github.com/ultralytics/yolov5/
#WORKDIR /code/yolov5
#RUN git reset --hard c23a441c9df7ca9b1f275e8c8719c949269160d1

#WORKDIR /code
#ENV PYTHONPATH "${PYTHONPATH}:/code/cameratraps:/code/ai4eutils:/code/yolov5"

# Removed PYTHONPATH manipulation (package provides modules)
ENV LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:/opt/conda/lib"

# Install cudnn for MD 4.1
#RUN conda install -c anaconda cudnn

# RUN pip install torchvision==0.15.2
# RUN pip install torch==2.0.1

# copy the content of the local src directory to the working directory
COPY src/ .

# Removed Torch upsampling sed hacks

# run megadetector wrapper script
CMD [ "python", "./megadetector.py" ]
