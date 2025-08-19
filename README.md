<img src="mewc_logo_hex.png" alt="MEWC Hex Sticker" width="200" align="right"/>

# mewc-detect

## Introduction
This repository contains code to build a Docker container for running [MegaDetector](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md). You can use this to process camera trap images with GPU support without having to install TensorFlow or CUDA. The only software you need on your computer is [Docker](https://www.docker.com). 

The container runs MegaDetector via the package entrypoint `python -m megadetector.detection.run_detector_batch`. The Dockerfile is based on an image called [mewc-flow](https://github.com/zaandahl/mewc-torch) that is built on PyTorch with additional Python packages for MegaDetector including TensorFlow to support the MegaDetector 4.0 model.

You can supply arguments via an environment file where the contents of that file are in the following format with one entry per line:
```
VARIABLE=VALUE
```

## Usage

After installing Docker you can run the container using a command similar to the following. Substitute `"$IN_DIR"` for your image directory and create a text file `"$ENV_FILE"` with any config options you wish to override. 

```
docker pull zaandahl/mewc-detect
docker run --env CUDA_VISIBLE_DEVICES=0 --env-file "$ENV_FILE" \
    --gpus all --interactive --tty --rm \
    --volume "$IN_DIR":/images \
    zaandahl/mewc-detect
```

With MDv1000 models, start with thresholds around 0.3–0.4 and tune for your dataset.

## Config Options

The following environment variables are supported for configuration (and their default values are shown). Simply omit any variables you don't need to change and if you want to just use all defaults you can leave `--env-file megadetector.env` out of the command alltogether. 

| Variable | Default | Description |
| ---------|---------|------------ |
| INPUT_DIR | "/images/" | A mounted point containing images to process - must match the Docker command above |
| MD_MODEL | "md_v5a.0.0.pt" | The MegaDetector model file (can be overridden under /code) |
| IMG_FILE | "" | A specific image filename to process. Empty means process entire directory |
| MD_FILE | "md_out.json" | MegaDetector output file, will write to INPUT_DIR |
| RECURSIVE | True | Recursive processing |
| RELATIVE_FILENAMES | True | Use relative filenames |
| QUIET | False | Quiet mode |
| IMAGE_QUEUE | False | Use image queue |
| THRESHOLD | 0.01 | MegaDetector threshold |
| CHECKPOINT_FREQ | 100 | Checkpoint frequency |
| CHECKPOINT_FILE | | File to resume checkpointing from under INPUT_DIR, empty for none |
| NCORES | | Number of CPU cores if GPU processing is unavailable, empty if not used |
