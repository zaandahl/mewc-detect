<img src="mewc_logo_hex.png" alt="MEWC Hex Sticker" width="200" align="right"/>

# mewc-detect

## Introduction
This repository contains code to build a Docker container for running [MegaDetector](https://github.com/agentmorris/MegaDetector/blob/main/megadetector.md). You can use this to process camera trap images with GPU support without having to install TensorFlow or CUDA. The only software you need on your computer is [Docker](https://www.docker.com). 

The container runs MegaDetector via the package entrypoint `python -m megadetector.detection.run_detector_batch`. The Dockerfile is based on an image called [mewc-flow](https://github.com/zaandahl/mewc-torch) that is built on PyTorch with additional Python packages for MegaDetector including TensorFlow to support the MegaDetector 4.0 model.

Base image: `zaandahl/mewc-torch:py310-cu117-torch2.0.1-no-tf` (PyTorch-only; TF removed).

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

### Switching from MDv5 to MDv1000
MDv1000 models typically benefit from lower detection thresholds than MDv5; starting around ~0.3–0.4 often yields better recall. For best results, tune the `--threshold` on a small labeled subset of your data to calibrate precision/recall trade-offs before scaling up.

## Config Options

The following environment variables are supported for configuration (and their default values are shown). Simply omit any variables you don't need to change and if you want to just use all defaults you can leave `--env-file megadetector.env` out of the command alltogether. 

| Variable | Default | Description |
| ---------|---------|------------ |
| INPUT_DIR | "/images/" | A mounted point containing images to process - must match the Docker command above |
| OUTPUT_DIR | INPUT_DIR | Optional separate writable directory for detector JSON/checkpoints |
| MD_MODEL | "md_v1000.0.0-redwood.pt" | Supported model alias, absolute model file path, or model file relative to /code |
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

## Pipeline integrity contract

Both Python entrypoints construct an argument list and run MegaDetector without a
shell. The container returns the detector's nonzero exit status (including exit 7)
and rejects invalid booleans, thresholds, CPU counts, missing model files, missing
checkpoints and paths escaping the input root. Absolute model mounts such as
`/models/model.pt` are used as supplied; relative model files resolve from the code
directory. `IMG_FILE` is relative to `INPUT_DIR`; `MD_FILE` and `CHECKPOINT_FILE` are
relative to `OUTPUT_DIR` (which defaults to `INPUT_DIR`). For read-only sources,
use `INPUT_DIR=/images/originals`, `OUTPUT_DIR=/images` and `MD_FILE=md_out.json`.
Detector image names remain relative to the original input directory.
A zero process exit still requires the orchestrator to validate the detector JSON
and image-level accounting before starting later stages.

The shared `process_detections` helper defaults to the approved
`category-confidence-v1` policy. It validates detections, removes entries below
`LOWER_CONF`, and examines remaining detections in descending confidence order.
Ties use bounding-box coordinates, category and original index. Only retained
same-category detections can suppress a later candidate. The existing overlap,
edge-distance, minimum-edge and upper-confidence conditions are unchanged. The
returned mask always uses the original detection-list indices.

`SUPPRESSION_POLICY=legacy-matryoshka-v1` explicitly selects the old ordered,
cross-category policy for reproductions. The new policy can change retained counts:
an overlapping person no longer suppresses an animal, a low-confidence detection
cannot suppress a valid one, and a suppressed detection cannot suppress another.
Do not reinterpret or rewrite older results silently. Null/failed detector images
and malformed boxes raise errors; a valid empty detection list remains a blank.
Shared stages must record their selected policy and effective thresholds.

Lightweight checks (no model download, inference or GPU required):

```sh
python -m pytest -q tests
```

The checks use pytest and PyYAML and include subprocess exit propagation,
absolute/code-relative model paths, path containment and old/new policy fixtures.
