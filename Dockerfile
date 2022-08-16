# set base image (host OS)
FROM zaandahl/mewc-torch:latest

# set the working directory in the container
WORKDIR /code

# clone megadetector repos
RUN git clone --depth 1 https://github.com/Microsoft/cameratraps
RUN git clone --depth 1 https://github.com/Microsoft/ai4eutils
RUN git clone --depth 1 https://github.com/ultralytics/yolov5/
ENV PYTHONPATH "${PYTHONPATH}:/code/cameratraps:/code/ai4eutils:/code/yolov5"

# download the megadetector models
RUN wget -O /code/md_v4.1.0.pb https://lilablobssc.blob.core.windows.net/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb
RUN wget -O /code/md_v5a.0.0.pt https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5a.0.0.pt
RUN wget -O /code/md_v5b.0.0.pt https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5b.0.0.pt

# copy the content of the local src directory to the working directory
COPY src/ .

# run megadetector wrapper script
CMD [ "python", "./megadetector.py" ]