# MegaDetector Docker 4.1
This repository contains code to build a Docker container for running [MegaDetector](https://github.com/microsoft/CameraTraps/blob/main/megadetector.md). You can use this to process camera trap images with GPU support without having to install TensorFlow or CUDA. The only software you need on your computer is [Docker](https://www.docker.com). 

The container invokes the script `run_tf_detector_batch.py` using MegaDetector v4.1. The version tags in this repo are matched to the version tags for the MegaDetector repo.

You can supply arguments via an environment file where the contents of that file are in the following format with one entry per line:
```
VARIABLE=VALUE
```

After installing Docker you can run the container using a command similar to the following. Substitute `"$IN_DIR"` for your image directory and create the file `megadetector.env` with any options you wish to customise. 

```
docker pull zaandahl/megadetector:v4.1
docker run --env CUDA_VISIBLE_DEVICES=0 --env-file megadetector.env \
    --gpus all --interactive --tty --rm \
    --volume "$IN_DIR":/images \
    zaandahl/megadetector
```

The following environment variables are supported for configuration (and their default values are shown). Simply omit any variables you don't need to change and if you want to just use all defaults you can leave `--env-file megadetector.env` out of the command alltogether. 

| Variable | Default | Description |
| ---------|---------|------------ |
| INPUT_DIR | "/images/" | A mounted point containing images to process - must match the Docker command above |
| MD_MODEL | "md_v4.1.0.pb" | The MegaDetector model file (can be overridden under /code) |
| IMG_FILE | "" | A specific image filename to process. Empty means process entire directory |
| MD_FILE | "md_out.json" | MegaDetector output file, will write to INPUT_DIR |
| RECURSIVE | True | Recursive processing |
| RELATIVE_FILENAMES | True | Use relative filenames |
| THRESHOLD | 0.01 | MegaDetector threshold |
| CHECKPOINT_FREQ | 100 | Checkpoint frequency |
| CHECKPOINT_FILE | None | File to resume checkpointing from under INPUT_DIR |
| NCORES | None | Number of CPU cores if GPU processing is unavailable |
