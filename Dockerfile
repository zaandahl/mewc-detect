# set base image (host OS)
FROM zaandahl/mewc-torch:1.0.9

# set the working directory in the container
WORKDIR /code

# download the megadetector models

#RUN wget -O /code/md_v4.1.0.pb https://lilablobssc.blob.core.windows.net/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb
RUN wget -O /code/md_v4.1.0.pb https://lilawildlife.blob.core.windows.net/lila-wildlife/models/camera_traps/megadetector/md_v4.1.0/md_v4.1.0.pb
RUN wget -O /code/md_v5a.0.0.pt https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5a.0.0.pt
RUN wget -O /code/md_v5b.0.0.pt https://github.com/agentmorris/MegaDetector/releases/download/v5.0/md_v5b.0.0.pt

# clone megadetector repos
#RUN git clone https://github.com/Microsoft/cameratraps
#WORKDIR /code/cameratraps
#RUN git reset --hard fc8cdf71064b54241a63db9c80bf35e117886911

RUN git clone https://github.com/agentmorris/megadetector

#WORKDIR /code
RUN git clone https://github.com/Microsoft/ai4eutils
#WORKDIR /code/ai4eutils
#RUN git reset --hard 1bbbb8030d5be3d6488ac898f9842d715cdca088

#WORKDIR /code
RUN git clone https://github.com/ecologize/yolov5/
#RUN git clone https://github.com/ultralytics/yolov5/
#WORKDIR /code/yolov5
#RUN git reset --hard c23a441c9df7ca9b1f275e8c8719c949269160d1

#WORKDIR /code
#ENV PYTHONPATH "${PYTHONPATH}:/code/cameratraps:/code/ai4eutils:/code/yolov5"

ENV PYTHONPATH "${PYTHONPATH}:/code/megadetector:/code/ai4eutils:/code/yolov5"
ENV LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:/opt/conda/lib"

# Install cudnn for MD 4.1
#RUN conda install -c anaconda cudnn

# RUN pip install torchvision==0.15.2
# RUN pip install torch==2.0.1

# copy the content of the local src directory to the working directory
COPY src/ .

# hack to fix problems with torch >= 1.11.0
RUN sed -i 's/return F.interpolate(input, self.size, self.scale_factor, self.mode, self.align_corners,/return F.interpolate(input, self.size, self.scale_factor, self.mode, self.align_corners)/g' /opt/conda/lib/python3.10/site-packages/torch/nn/modules/upsampling.py
RUN sed -i 's/recompute_scale_factor=self.recompute_scale_factor)//g' /opt/conda/lib/python3.10/site-packages/torch/nn/modules/upsampling.py

# run megadetector wrapper script
CMD [ "python", "./megadetector.py" ]