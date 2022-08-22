# set base image (host OS)
FROM zaandahl/mewc-torch:1.0

# set the working directory in the container
WORKDIR /code

# download the megadetector models
RUN wget -O /code/md_v4.1.0.pb https://lilablobssc.blob.core.windows.net/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb
RUN wget -O /code/md_v5a.0.0.pt https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5a.0.0.pt
RUN wget -O /code/md_v5b.0.0.pt https://github.com/microsoft/CameraTraps/releases/download/v5.0/md_v5b.0.0.pt

# clone megadetector repos
RUN git clone https://github.com/Microsoft/cameratraps
WORKDIR /code/cameratraps
RUN git reset --hard fc8cdf71064b54241a63db9c80bf35e117886911
WORKDIR /code
RUN git clone https://github.com/Microsoft/ai4eutils
WORKDIR /code/ai4eutils
RUN git reset --hard 1bbbb8030d5be3d6488ac898f9842d715cdca088
WORKDIR /code
RUN git clone https://github.com/ultralytics/yolov5/
WORKDIR /code/yolov5
RUN git reset --hard c23a441c9df7ca9b1f275e8c8719c949269160d1
WORKDIR /code
ENV PYTHONPATH "${PYTHONPATH}:/code/cameratraps:/code/ai4eutils:/code/yolov5"

# copy the content of the local src directory to the working directory
COPY src/ .

# run megadetector wrapper script
CMD [ "python", "./megadetector.py" ]