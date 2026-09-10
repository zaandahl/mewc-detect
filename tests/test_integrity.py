import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

SRC = Path(__file__).resolve().parents[1] / 'src'
sys.path.insert(0, str(SRC))
from lib_command import create_command
from lib_tools import process_detections, validate_detections


def config(tmp_path):
    return dict(INPUT_DIR=str(tmp_path), MD_MODEL='mdv5a', MD_FILE='md_out.json',
                THRESHOLD=.01, CHECKPOINT_FREQ=100)


def detection(category='1', confidence=.5, bbox=None):
    return {'category': category, 'conf': confidence, 'bbox': bbox or [.1, .1, .4, .4]}


def mask(detections, policy='category-confidence-v1'):
    return process_detections({'detections': detections}, .3, .02, 0, .9, .05, policy=policy)


@pytest.mark.parametrize('entrypoint', ['mewc_runner.py', 'mewc_detect.py'])
def test_detector_exit_7_is_propagated(tmp_path, entrypoint):
    module = tmp_path / 'megadetector' / 'detection'
    module.mkdir(parents=True)
    (module / 'run_detector_batch.py').write_text('raise SystemExit(7)\n')
    env = {**os.environ, 'PYTHONPATH': str(tmp_path), 'MD_MODEL': 'mdv5a', 'INPUT_DIR': str(tmp_path)}
    result = subprocess.run([sys.executable, str(SRC / entrypoint)], env=env, capture_output=True, text=True)
    assert result.returncode == 7
    assert 'failed with exit status 7' in result.stderr


def test_absolute_and_code_relative_model_paths(tmp_path):
    code = tmp_path / 'code'
    code.mkdir()
    model = code / 'model with spaces.pt'
    model.touch()
    for value in [str(model), model.name]:
        argv = create_command({**config(tmp_path), 'MD_MODEL': value}, code_dir=code)
        assert argv[-3] == str(model)


def test_argv_paths_remain_single_arguments(tmp_path):
    image = tmp_path / 'image ; $(touch injected).jpg'
    image.touch()
    argv = create_command({**config(tmp_path), 'IMG_FILE': image.name})
    assert isinstance(argv, list)
    assert argv[-2] == str(image)
    assert not (tmp_path / 'injected').exists()


@pytest.mark.parametrize('changes', [
    {'THRESHOLD': 'nan'}, {'THRESHOLD': 2}, {'NCORES': '1; touch evil'},
    {'RECURSIVE': 'maybe'}, {'MD_MODEL': 'unknown'}, {'MD_MODEL': '/missing/model.pt'},
    {'MD_FILE': '../outside.json'}, {'MD_FILE': '/tmp/out.json'},
    {'IMG_FILE': '../outside.jpg'}, {'CHECKPOINT_FREQ': 0}, {'CHECKPOINT_FILE': 'missing.json'},
])
def test_invalid_config_rejected(tmp_path, changes):
    with pytest.raises((ValueError, TypeError)):
        create_command({**config(tmp_path), **changes})


def test_symlink_output_escape_rejected(tmp_path):
    outside = tmp_path / 'outside'
    inside = tmp_path / 'inside'
    outside.mkdir()
    inside.mkdir()
    (inside / 'link').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='beneath'):
        create_command({**config(inside), 'MD_FILE': 'link/out.json'})


def test_cross_category_and_filtered_earlier_box_no_longer_suppress():
    mixed = [detection('2', .8), detection('1', .5)]
    assert mask(mixed, 'legacy-matryoshka-v1') == [True, False]
    assert mask(mixed) == [True, True]
    low_first = [detection(confidence=.01), detection(confidence=.5)]
    assert mask(low_first, 'legacy-matryoshka-v1') == [False, False]
    assert mask(low_first) == [False, True]


def test_confidence_order_independent_of_input_order():
    boxes = [detection(confidence=.5), detection(confidence=.8)]
    assert mask(boxes) == [False, True]
    assert mask(list(reversed(boxes))) == [True, False]


def test_equal_confidence_uses_stable_bbox_tie_key():
    boxes = [detection(bbox=[.11, .1, .4, .4]), detection(bbox=[.1, .1, .4, .4])]
    assert mask(boxes) == [False, True]
    assert mask(list(reversed(boxes))) == [True, False]


def test_suppressed_box_cannot_suppress_another():
    boxes = [detection(confidence=.8, bbox=[0, 0, .5, 1]),
             detection(confidence=.7, bbox=[.25, 0, .5, 1]),
             detection(confidence=.6, bbox=[.5, 0, .5, 1])]
    assert mask(boxes, 'legacy-matryoshka-v1') == [True, False, False]
    assert mask(boxes) == [True, False, True]


def test_high_confidence_boxes_still_respect_existing_upper_threshold():
    assert mask([detection(confidence=.95), detection(confidence=.9)]) == [True, True]


@pytest.mark.parametrize('image', [
    {'detections': None}, {'failure': 'unreadable', 'detections': []}, {},
    {'detections': [dict(detection(), bbox=None)]},
    {'detections': [dict(detection(), bbox=[0, 0, 0, .2])]},
    {'detections': [dict(detection(), conf=float('nan'))]},
])
def test_failed_or_invalid_detections_are_not_blank(image):
    with pytest.raises(ValueError):
        validate_detections(image)


def test_valid_zero_is_blank():
    assert validate_detections({'detections': []}) == []
    assert mask([]) == []


def test_separate_output_root_preserves_source_identity(tmp_path):
    originals = tmp_path / 'originals'
    output = tmp_path / 'outputs'
    originals.mkdir()
    output.mkdir()
    argv = create_command({**config(originals), 'OUTPUT_DIR': str(output)})
    assert argv[-2] == str(originals)
    assert argv[-1] == str(output / 'md_out.json')
    with pytest.raises(ValueError):
        create_command({**config(originals), 'OUTPUT_DIR': str(output), 'MD_FILE': '../bad.json'})
