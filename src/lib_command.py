"""Validated MegaDetector argv construction; no shell evaluation."""
import math
from pathlib import Path
import sys


MODEL_NAMES = {'mdv5a', 'mdv5b', 'mdv1000-redwood', 'mdv1000-cedar', 'mdv1000-spruce'}


def as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (str, int)):
        token = str(value).strip().lower()
        if token in {'true', 't', 'yes', 'y', '1'}:
            return True
        if token in {'false', 'f', 'no', 'n', '0'}:
            return False
    raise ValueError(f'Invalid boolean: {value!r}')


def _is_unset(value):
    return value is None or (isinstance(value, str) and not value.strip())


def relative_path(root, value, label):
    """Resolve a child path and reject traversal, absolute paths and symlink escapes."""
    path = Path(str(value))
    if _is_unset(value) or path.is_absolute() or '..' in path.parts or '\\' in str(value):
        raise ValueError(f'{label} must be a nonempty relative path')
    result = (root / path).resolve()
    if result == root or not result.is_relative_to(root):
        raise ValueError(f'{label} must stay beneath its configured root')
    return result


def integer(value, label, minimum=1):
    if isinstance(value, bool):
        raise ValueError(f'{label} must be an integer')
    try:
        parsed = int(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f'{label} must be an integer') from None
    if str(value).strip() != str(parsed):
        raise ValueError(f'{label} must be an integer')
    if parsed < minimum:
        raise ValueError(f'{label} must be >= {minimum}')
    return parsed


def create_command(config, code_dir=None):
    """Return executable argv, validating configured files before detector launch."""
    code_dir = Path(code_dir or Path(__file__).resolve().parent)
    if _is_unset(config.get('INPUT_DIR')):
        raise ValueError('INPUT_DIR is required')
    input_dir = Path(str(config['INPUT_DIR'])).resolve()
    if not input_dir.is_dir():
        raise ValueError(f'INPUT_DIR does not exist: {input_dir}')
    model = str(config.get('MD_MODEL') or '').strip()
    if model.lower() in MODEL_NAMES:
        model_path = model.lower()
    else:
        candidate = Path(model)
        if not model or '\\' in model or not (candidate.suffix.lower() in {'.pt', '.pb'}):
            raise ValueError('MD_MODEL must be a supported model name or a .pt/.pb file')
        model_path = (candidate if candidate.is_absolute() else code_dir / candidate).resolve()
        if not candidate.is_absolute() and not model_path.is_relative_to(code_dir.resolve()):
            raise ValueError('Relative MD_MODEL must stay beneath the code directory')
        if not model_path.is_file():
            raise ValueError(f'Model file does not exist: {model_path}')
        model_path = str(model_path)
    image_path = input_dir
    if not _is_unset(config.get('IMG_FILE')):
        image_path = relative_path(input_dir, config['IMG_FILE'], 'IMG_FILE')
        if not image_path.is_file():
            raise ValueError(f'IMG_FILE does not exist: {image_path}')
    output_dir_value = config.get('OUTPUT_DIR')
    output_dir = input_dir if _is_unset(output_dir_value) else Path(str(output_dir_value)).resolve()
    if not output_dir.is_dir():
        raise ValueError(f'OUTPUT_DIR does not exist: {output_dir}')
    output = relative_path(output_dir, config['MD_FILE'], 'MD_FILE')
    if output == image_path or str(output) == model_path or output.suffix.lower() != '.json':
        raise ValueError('MD_FILE must be a separate JSON output file')
    if not output.parent.is_dir() or output.is_dir():
        raise ValueError('MD_FILE parent must exist and output cannot be a directory')
    threshold = float(config['THRESHOLD'])
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('THRESHOLD must be finite and between 0 and 1')
    checkpoint_frequency = integer(config['CHECKPOINT_FREQ'], 'CHECKPOINT_FREQ', -1)
    if checkpoint_frequency == 0:
        raise ValueError('CHECKPOINT_FREQ must be -1 (disabled) or a positive integer')
    argv = [sys.executable, '-m', 'megadetector.detection.run_detector_batch']
    for key, flag in [('RECURSIVE', '--recursive'), ('RELATIVE_FILENAMES', '--output_relative_filenames'),
                      ('QUIET', '--quiet'), ('IMAGE_QUEUE', '--use_image_queue')]:
        if as_bool(config.get(key, False)):
            argv.append(flag)
    argv += [f'--threshold={threshold}', f'--checkpoint_frequency={checkpoint_frequency}']
    if not _is_unset(config.get('CHECKPOINT_FILE')):
        checkpoint = relative_path(output_dir, config['CHECKPOINT_FILE'], 'CHECKPOINT_FILE')
        if not checkpoint.is_file():
            raise ValueError(f'CHECKPOINT_FILE does not exist: {checkpoint}')
        if checkpoint == output:
            raise ValueError('CHECKPOINT_FILE must differ from MD_FILE')
        argv += ['--resume_from_checkpoint', str(checkpoint)]
    if not _is_unset(config.get('NCORES')):
        argv += ['--ncores', str(integer(config['NCORES'], 'NCORES'))]
    return argv + [model_path, str(image_path), str(output)]
