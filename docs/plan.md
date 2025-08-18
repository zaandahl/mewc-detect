# Plan — Migration to MD package + MDv1000

This plan splits changes into small, reviewable modules. Each module ends with test commands and clear acceptance criteria. Module 0 includes docs only.

## Module 1 — Dockerfile switch + call site update + MDv1000 default

Scope:
- Replace base image with a pinned CUDA/PyTorch runtime (e.g., `pytorch/pytorch:<version>-cuda11.8-cudnn8-runtime` or digest)
- `pip install` runtime deps: `megadetector` (pinned), `ultralytics` (pinned if needed), `pydantic<2` only if required by MD version, etc.
- Remove git clones (`megadetector`, `ai4eutils`, `yolov5`) and `ENV PYTHONPATH` edits
- Remove Torch `sed -i` hacks on `upsampling.py`
- Keep wrapper `src/megadetector.py`; update `src/lib_command.py` call site and model handling

Edits:
- Dockerfile
  - Line 3: replace base image; add `pip install megadetector==<pinned>` (+ `ultralytics==<pinned>` if needed)
  - Lines 9–11: remove `wget` model downloads
  - Lines 18, 21, 26: remove `git clone` steps
  - Line 34: remove `ENV PYTHONPATH ...`
  - Lines 47–48: remove `sed -i` hacks
  - Keep `CMD ["python", "./megadetector.py"]`
- `src/lib_command.py`
  - Line 21: change to `python -m megadetector.detection.run_detector_batch`
  - Line 16: detect if `MD_MODEL` looks like a file (`*.pt` or path) vs model name; pass through accordingly
  - No behavior change to env names; preserve defaults
- `src/megadetector.py`
  - Remove unused import of `detection.run_detector_batch` (optional in this module); ensure local config reader import is correct

Default model:
- Set image/README default to `md_v1000.0.0-redwood` (keep backward support for `md_v5*.pt` via `MD_MODEL` env)

Quick tests:
- Build: `docker build -t mewc-detect:md1000 .`
- Help probe: `docker run --rm mewc-detect:md1000 python -m megadetector.detection.run_detector_batch --help`
- Smoke: `docker run --rm -e INPUT_DIR=/images -v "$PWD":/images mewc-detect:md1000 python -m megadetector.detection.run_detector_batch --threshold 0.3 md_v1000.0.0-redwood /images /images/md_out.json`

Acceptance criteria:
- Image builds without `git clone` or `sed` hacks; base is pinned
- `--help` works; default model resolves to MDv1000 `redwood`
- MDv5 remains runnable via `MD_MODEL` file path or name

Commit boundary:
- Single PR: Dockerfile + `src/lib_command.py` (+ minimal wrapper import cleanup if needed) + README note of MD package usage

## Module 2 — Wrapper hardening + README

Scope:
- Robust boolean parsing with backward compatibility (`True`/`False` strings still honored); accept `true/false/1/0/yes/no`
- `MD_MODEL` auto-handling: pass through model name vs file path seamlessly
- Update README: MDv1000 guidance (recommended thresholds ~0.3–0.4), examples for `redwood`, MDv5 compatibility note

Quick tests:
- Env matrix (examples):
  - `RECURSIVE=True`, `RELATIVE_FILENAMES=True`, `QUIET=False`, `IMAGE_QUEUE=False`
  - `RECURSIVE=true`, `QUIET=1`, `IMAGE_QUEUE=no` → flags match intent
  - `MD_MODEL=md_v5b.0.0` vs `MD_MODEL=/code/md_v5b.0.0.pt`

Acceptance criteria:
- Wrapper correctly interprets booleans across common forms
- Model name vs path both work; outputs match expectations
- README examples reflect realities and run in the image

Commit boundary:
- PR: `src/lib_command.py` boolean parsing + README updates

## Module 3 — CI polish

Scope:
- Ensure base image pin/digest documented in Dockerfile comment and commit
- Add smoke test step to `.github/workflows/docker-image.yaml` after build:
  - `docker run --rm $IMAGE python -m megadetector.detection.run_detector_batch --help`
- Optionally update build-push actions to latest majors

Acceptance criteria:
- CI builds on tag; smoke test passes; tags/labels include semver and sha

Commit boundary:
- PR: workflow changes only

## Module 4 — Optional variants (larch/sorrel)

Scope:
- Add documented support for `md_v1000.0.0-larch` and `...-sorrel`
- Ensure `ultralytics` pin supports chosen variants

Quick tests:
- Run help + one dry-run command for each variant

Acceptance criteria:
- Selecting variants via `MD_MODEL` env works; no extra code churn

---

## Fast Reference — Current exact strings to change

- `Dockerfile`
  - `FROM zaandahl/mewc-torch` (line 3)
  - `RUN wget -O /code/md_v4.1.0.pb ...` (line 9)
  - `RUN wget -O /code/md_v5a.0.0.pt ...` (line 10)
  - `RUN wget -O /code/md_v5b.0.0.pt ...` (line 11)
  - `RUN git clone https://github.com/agentmorris/megadetector` (line 18)
  - `RUN git clone https://github.com/Microsoft/ai4eutils` (line 21)
  - `RUN git clone https://github.com/ecologize/yolov5/` (line 26)
  - `ENV PYTHONPATH "${PYTHONPATH}:/code/megadetector:/code/ai4eutils:/code/yolov5"` (line 34)
  - `RUN sed -i ... upsampling.py` (lines 47–48)

- `src/lib_command.py`
  - `detector_file_str = " /code/" + ...` (line 16)
  - `md_cmd = "python /code/megadetector/detection/run_detector_batch.py " + ...` (line 21)
  - Boolean string checks for flags (lines 2,4,6,8)

- `src/megadetector.py`
  - `import detection.run_detector_batch as run_detector_batch` (line 4)
  - `from lib_common import read_yaml` (line 5)

- `README.md`
  - `run_detector_batch.py` mention (line 8)
  - MDv5 default in table (line 34)

## Build commands

- Baseline (current): `docker build -t mewc-detect:baseline .`
- Post-migration (Module 1): `docker build -t mewc-detect:md1000 .`

