# MEWC-Detect repo description

- Purpose: Build a Docker image that runs MegaDetector on camera-trap images with GPU support, without requiring local TensorFlow/CUDA installs.
- Strategy: Bundle models and clone the MegaDetector code into the image, then invoke MD’s batch script via a small Python wrapper.
- Output: A JSON file (default md_out.json) with detections written next to your images.

## Repo Layout

- Dockerfile: Builds the runtime image, downloads MD models, clones MD-related repos, copies src code, and sets the entry command.
- src/megadetector.py: Main wrapper. Loads config + env overrides, builds the MD command, prints it, and runs it.
- src/lib_tools.py: Helpers for post-processing detections (overlap, “matryoshka” nesting logic, filtering by confidence).
- src/config.yaml: Default configuration; env vars can override these at runtime.
- .github/workflows/: CI for building/pushing the Docker image and syncing Docker Hub description.
- docs/: Recon/plan notes for migrating to the official megadetector package and MDv1000 models.

## Runtime Flow

- Entrypoint: CMD ["python", "./megadetector.py"] inside the container.
- Config: megadetector.py reads src/config.yaml, then overrides keys with environment variables if present.
- Command build: lib_command.create_command(config) assembles flags and paths, e.g.:
    - Calls python /code/megadetector/detection/run_detector_batch.py
    - Appends flags like --recursive, --output_relative_filenames, --threshold, checkpointing, cores, etc.
    - Passes model path (under /code), input directory, and output JSON path.
- Execution: The command is printed and run via os.system(...).

## Configuration

- Primary env vars (with defaults in README.md/src/config.yaml):
    - INPUT_DIR (default "/images/"): Directory mount with your images.
    - MD_MODEL (default "md_v5a.0.0.pt"): Model file expected in /code/ inside the image.
    - IMG_FILE: Optional single image to process; otherwise process directory.
    - MD_FILE (default "md_out.json"): Output written to INPUT_DIR.
    - Flags: RECURSIVE, RELATIVE_FILENAMES, QUIET, IMAGE_QUEUE.
    - Tuning: THRESHOLD, CHECKPOINT_FREQ, CHECKPOINT_FILE, NCORES.
- Usage example (from README):
    - docker run --env CUDA_VISIBLE_DEVICES=0 --env-file "$ENV_FILE" --gpus all -it --rm -v "$IN_DIR":/images zaandahl/mewc-detect

## Docker & Dependencies

- Base image: zaandahl/mewc-torch (unpinned).
- Models downloaded into /code/: md_v4.1.0.pb, md_v5a.0.0.pt, md_v5b.0.0.pt.
- Repos cloned into image: agentmorris/megadetector, Microsoft/ai4eutils, ecologize/yolov5.
- PYTHONPATH includes those clones so run_detector_batch.py can be imported/run.
- A Torch “upsampling” hack is applied via sed to work around version compatibility.
- CI builds/pushes image on tagged releases; a separate workflow updates Docker Hub description.

## Helpers (lib_tools.py)

- Bounding-box utilities: compute area, overlap, and edge distances.
- “Matryoshka” filter: detects nested/near-duplicate boxes and invalidates lower-confidence ones.
- Filtering: can return a mask of valid detections per image and a simple “contains animal” check.

## Notable Details / Caveats

- Booleans parsing: lib_command.py checks for the literal string 'True'. If a value remains a Python boolean (e.g., from YAML defaults), flags won’t set unless env overrides provide 'True' as a string. This can lead to defaults being
ignored.
- Import mismatch: megadetector.py tries from lib_common import read_yaml but lib_common isn’t present in src. It likely exists in the base image or is a legacy name; this is fragile.
- Hard paths: The command uses a fixed path to MD’s script: /code/megadetector/detection/run_detector_batch.py. Works because the image clones that repo into /code.
- docker-compose: Uses zaandahl/megadetector image name and tails logs; seems like a local-build helper rather than a runnable service.

## Planned Migration (docs/)

- Move to the official megadetector Python package and MDv1000 models (e.g., md_v1000.0.0-redwood).
- Replace git clones and PYTHONPATH hacks with pip install.
- Switch call to python -m megadetector.detection.run_detector_batch.
- Harden boolean/env parsing and clarify README defaults/threshold guidance.
- Add CI smoke test (--help) post-build.
