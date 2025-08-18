# Recon — mewc-detect → MD package + MDv1000 (Module 0)

This document inventories the current repo, identifies MegaDetector coupling points, notes risks, and proposes a phased migration to the official `megadetector` Python package with MDv1000 (default: `redwood`).

## 1) Context Verification

- Working dir: `/mnt/c/git/mewc-detect`
- Git branch: `main` (tracking `origin/main`)
- Remote: `https://github.com/zaandahl/mewc-detect.git`
- Docker client: `Docker version 28.3.2, build 578ccf6`
- Docker daemon access: not available in this environment (`permission denied`); baseline build not executed here
- Default branch (remote): inferred `main`
- NVIDIA runtime: not checked (no container run in this module)

## 2) Repo Map (top two levels)

- `.github/workflows/`
  - `docker-image.yaml` (1.4 KB): CI build/push
  - `dockerhub-description.yaml` (581 B): README → Docker Hub
- `Dockerfile` (2.2 KB): builds runtime image
- `docker-compose.yml` (168 B): local build helper
- `README.md` (2.6 KB): usage and config
- `src/`
  - `config.yaml` (501 B): defaults (env-overridable)
  - `lib_command.py` (1.6 KB): builds MD CLI command
  - `lib_tools.py` (3.1 KB): detection post-processing helpers
  - `megadetector.py` (416 B): wrapper that loads config/env and runs MD
- Large binaries: none in repo (no files >5 MB)

## 3) Extracted Summaries

### Dockerfile

- Base image: `FROM zaandahl/mewc-torch` (unpinned tag; line 3)
- Weight downloads (lines 9–11):
  - v4.1 TF graph: `/code/md_v4.1.0.pb`
  - v5a/v5b Torch: `/code/md_v5a.0.0.pt`, `/code/md_v5b.0.0.pt`
- Git clones (lines 18, 21, 26):
  - `agentmorris/megadetector`
  - `Microsoft/ai4eutils`
  - `ecologize/yolov5`
- Env (line 34): `PYTHONPATH` adds `/code/megadetector:/code/ai4eutils:/code/yolov5`
- Torch interpolation hacks (lines 47–48): in-place `sed -i` on `.../torch/nn/modules/upsampling.py`
- Workdir: `/code`
- Entrypoint/CMD (line 51): `python ./megadetector.py`

Notes:
- No `pip install`; dependencies provided by base + cloned repos.
- Mixes TF (for MDv4.1) and Torch (for MDv5) era requirements.

### Source: `src/megadetector.py`

- Imports: `import detection.run_detector_batch as run_detector_batch` (line 4), implies cloned `megadetector` repo on `PYTHONPATH`
- Config loading: `read_yaml('config.yaml')` then overrides with matching env vars (lines 8–11)
- Execution: builds string command and runs via `os.system()` (lines 13–15)
- Note: imports `read_yaml` from `lib_common` (line 5), which is not present in `src/`; likely a legacy name (should be from `lib_tools` or similar) — current image may rely on something from base or clones.

### Source: `src/lib_command.py`

- Boolean parsing: string comparisons to `'True'` for flags (lines 2,4,6,8)
- Threshold/checkpoint/ncores: appended as strings (lines 10–15)
- Model path assembly (line 16): `" /code/" + config["MD_MODEL"] + " "` (assumes a local file path under `/code`)
- Call site (line 21): `python /code/megadetector/detection/run_detector_batch.py ...` (hard-coded path into cloned repo)

### Source: `src/config.yaml`

- Defaults: `MD_MODEL: "md_v5a.0.0.pt"`, `THRESHOLD: 0.01`, recursion and relative filenames enabled
- Additional knobs (not used in CLI builder yet): box/matryoshka/exif/snips

### README.md

- Describes invoking `run_detector_batch.py` (line 8)
- Config table uses `MD_MODEL: "md_v5a.0.0.pt"` default (line 34)
- Mentions TF support for MegaDetector 4.0 model; no mention of MDv1000 models

### CI: `.github/workflows/docker-image.yaml`

- Triggers: push to any branch and tags `v*`; PRs from any branch
- Push gating: only pushes when base ref is `main` and ref is a tag (non-v0)
- Uses `docker/metadata-action@v3` and `docker/build-push-action@v2`
- Pitfall: runtime image’s base is unpinned (Dockerfile), so reproducibility depends on `zaandahl/mewc-torch` tag stability

## 4) Code Search: coupling and fragile strings

- `run_detector_batch` hard path: `src/lib_command.py:21`
- Import assuming cloned MD code: `src/megadetector.py:4`
- Model defaults and downloads:
  - `src/config.yaml:6` → `md_v5a.0.0.pt`
  - `Dockerfile:9–11` → v4.1, v5a, v5b
- PYTHONPATH injection: `Dockerfile:34`
- Torch `sed -i` hacks: `Dockerfile:47–48`
- README references MD and `run_detector_batch.py`: `README.md:8, 34`

## 5) Baseline Build (attempt)

- Command: `docker build -t mewc-detect:baseline .`
- Status: not executed here due to sandboxed Docker daemon (`permission denied`)
- Expected behavior outside sandbox: pulls `zaandahl/mewc-torch`, downloads three weight files, clones three repos; final image likely large and variable due to unpinned base and git HEADs

## 6) Risk Register & Touch-points

- Call site swap:
  - Change from hard path to module: `python -m megadetector.detection.run_detector_batch`
- Model acquisition:
  - Today expects local `/code/md_v5a.0.0.pt` etc.; with MD package, prefer model names (e.g., `md_v5b.0.0`, `md_v1000.0.0-redwood`) or absolute file paths
- Remove git clones/PYTHONPATH edits:
  - Eliminate `git clone` of `megadetector`, `ai4eutils`, and `yolov5`; install `megadetector` (and `ultralytics` if needed) via `pip`
  - Remove `ENV PYTHONPATH` mutations
- Remove Torch `sed` hacks:
  - Incompatible with reproducibility; ensure compatible Torch/CUDA versions instead
- Threshold defaults:
  - Current `THRESHOLD: 0.01`; MDv1000 models often prefer ~0.3–0.4 for comparable precision; document guidance without changing output format
- Boolean/env parsing:
  - Wrapper compares to string `'True'`; maintain backward compatibility but add robust parsing (accept `true/1/yes`)
- Base image pinning:
  - Pin a CUDA runtime image or `pytorch/pytorch` tag/digest to ensure reproducibility; avoid TF if MDv4 support is no longer required in-image
- README and CI drift:
  - Update docs to reflect MD package usage and new defaults; add CI smoke test using `python -m megadetector... --help`

Breaking-change risks and mitigations:
- Behavior shift from file-based model path to name-based selection → Accept both; auto-detect if value endswith `.pt` to keep current behavior
- Threshold changes affecting downstream workflows → Keep default as-is initially; document MDv1000 recommended values; allow env overrides
- Removal of v4.1 TF support → Keep MDv5 compatibility; consider dropping v4.1 download by default but leave a documented escape hatch (optional add-on)

## 7) Proposed Modules (with acceptance criteria)

1) Module 1 — Dockerfile → MD package + MDv1000 (redwood by default)
   - Swap to a pinned CUDA/PyTorch base; `pip install megadetector` (and `ultralytics`, pinned)
   - Remove git clones and `PYTHONPATH` edits; delete Torch `sed` hacks
   - Update `lib_command.py` to call `python -m megadetector.detection.run_detector_batch`
   - Keep MDv5 weights optional: allow `MD_MODEL` to be a file path or a model name
   - Acceptance: image builds; CLI `--help` runs; default model resolves to `md_v1000.0.0-redwood`; MDv5 still runnable via file path or name

2) Module 2 — Wrapper hardening + README
   - Add robust boolean/env parsing with backward compatibility (`True`/`False` strings still work)
   - Model arg auto-handling: file path vs named model
   - README updates: MDv1000 usage, threshold guidance (0.3–0.4), examples
   - Acceptance: env var matrix tested; README examples match behavior

3) Module 3 — CI polish
   - Pin base image tag or digest; upgrade actions; add smoke test step (`python -m megadetector... --help`)
   - Acceptance: CI builds on tag; smoke test passes; labels/tags correct

4) Module 4 — Optional MDv1000 variants
   - Gated support for `larch`/`sorrel` (ensure compatible `ultralytics` version)
   - Acceptance: selecting model variant works via env; build size remains reasonable

## 8) Exact Touch Points (files/lines)

- `Dockerfile`
  - Line 3: `FROM zaandahl/mewc-torch` → switch to pinned CUDA/PyTorch base
  - Lines 9–11: `RUN wget ... md_v4.1.0.pb / md_v5*.pt` → remove; rely on package-managed weights or runtime fetch
  - Lines 18, 21, 26: `git clone` repos → remove
  - Line 34: `ENV PYTHONPATH ...` → remove
  - Lines 47–48: `sed -i` hacks on `upsampling.py` → remove
  - Line 51: `CMD ["python","./megadetector.py"]` → keep wrapper, but its call site changes (below)

- `src/megadetector.py`
  - Line 4: `import detection.run_detector_batch as run_detector_batch` → not needed with package/module execution
  - Line 5: `from lib_common import read_yaml` → verify/rename to local helper or inline reader

- `src/lib_command.py`
  - Line 16: `" /code/" + MD_MODEL` → allow either raw model name or absolute/`/code` file path
  - Line 21: `python /code/megadetector/detection/run_detector_batch.py` → `python -m megadetector.detection.run_detector_batch`
  - Lines 2,4,6,8: boolean string comparisons → robust parsing (keep `'True'` compatibility)

- `README.md`
  - Line 8: reference to `run_detector_batch.py` → reflect module invocation
  - Line 34: default `MD_MODEL` value → document MDv1000 defaults (`md_v1000.0.0-redwood`) and MDv5 compatibility

- `.github/workflows/docker-image.yaml`
  - Ensure base image pinning in Dockerfile; add module help smoke test in CI

## 9) Open Questions

- Must MDv4.1 remain supported inside the default image, or can it be documented as optional/out-of-scope?
- Target CUDA/Torch baseline for GPUs commonly used by maintainers? (e.g., CUDA 11.8 vs 12.x)
- Prefer bundling common weights at build time vs. lazy download on first use?
- Any consumers rely on the current ultra-low threshold default `0.01`? OK to keep default but recommend higher for MDv1000?
- Should we keep `docker-compose.yml` (it pins no tags) or simplify to Docker CLI examples only?

## 10) Baseline vs. Post-migration build lines

- Baseline (current): `docker build -t mewc-detect:baseline .`
- Post-migration (Module 1): `docker build -t mewc-detect:md1000 .`

