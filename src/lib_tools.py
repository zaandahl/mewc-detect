"""Detection validation and explicitly versioned suppression policy."""
import math

LEGACY_POLICY = 'legacy-matryoshka-v1'
DEFAULT_POLICY = 'category-confidence-v1'


def validate_detections(json_image):
    """Reject failed/malformed images; [] is a successful image with zero detections."""
    if not isinstance(json_image, dict) or json_image.get('failure'):
        raise ValueError('Detector image failed or is not an object')
    detections = json_image.get('detections')
    if not isinstance(detections, list):
        raise ValueError('detections must be a list; null/missing is not a blank image')
    for index, detection in enumerate(detections):
        if not isinstance(detection, dict):
            raise ValueError(f'Detection {index} is not an object')
        confidence = detection.get('conf')
        bbox = detection.get('bbox')
        if (isinstance(confidence, bool) or not isinstance(confidence, (int, float))
                or not math.isfinite(confidence) or not 0 <= confidence <= 1):
            raise ValueError(f'Detection {index} has invalid confidence')
        if not isinstance(detection.get('category'), str) or not detection['category']:
            raise ValueError(f'Detection {index} has invalid category')
        if (not isinstance(bbox, (list, tuple)) or len(bbox) != 4
                or any(isinstance(v, bool) or not isinstance(v, (int, float))
                       or not math.isfinite(v) for v in bbox)
                or bbox[2] <= 0 or bbox[3] <= 0):
            raise ValueError(f'Detection {index} has invalid bounding box')
    return detections


def get_coords(bbox):
    x1, y1, w_box, h_box = bbox
    y1,x1,y2,x2 = y1, x1, y1 + h_box, x1 + w_box
    coords = (round(x1, 5), round(x2, 5), round(y1, 5), round(y2, 5))
    return(coords)

def calc_area(coords):
    x1,x2,y1,y2 = coords
    area = (x2-x1)*(y2-y1)
    return(round(area, 4))

def check_overlap(bbox1, bbox2):
    a_x1,a_x2,a_y1,a_y2 = get_coords(bbox1)
    b_x1,b_x2,b_y1,b_y2 = get_coords(bbox2)
    if(a_x1 < b_x2 and a_x2 > b_x1 and a_y1 < b_y2 and a_y2 > b_y1):
        return True
    else:
        return False

def calc_overlap(bbox1, bbox2):
    a_x1,a_x2,a_y1,a_y2 = get_coords(bbox1)
    b_x1,b_x2,b_y1,b_y2 = get_coords(bbox2)
    overlap = (max(a_x1,b_x1)-min(a_x2,b_x2))*(max(a_y1,b_y1)-min(a_y2,b_y2))
    return(round(overlap, 4))

def calc_perc(area1,area2,overlap):
    denominator = area1 + area2 - overlap
    if denominator <= 0:
        raise ValueError('Bounding boxes have zero area at legacy overlap precision')
    percent = overlap / denominator
    return(round(percent, 4))

def calc_overpercent(bbox1, bbox2):
    coords1 = get_coords(bbox1)
    area1 = calc_area(coords1)
    coords2 = get_coords(bbox2)
    area2 = calc_area(coords2)
    overlap = calc_overlap(bbox1, bbox2)
    denominator = area1 + area2 - overlap
    if denominator <= 0:
        raise ValueError('Bounding boxes have zero area at legacy overlap precision')
    percent = overlap / denominator
    return(round(percent, 4))

def calc_edgedist(bbox1, bbox2):
    a_x1,a_x2,a_y1,a_y2 = get_coords(bbox1)
    b_x1,b_x2,b_y1,b_y2 = get_coords(bbox2)
    edgedist = (round(abs(a_x1-b_x1),4),
        round(abs(a_x2-b_x2),4),
        round(abs(a_y1-b_y1),4),
        round(abs(a_y2-b_y2),4))
    return(edgedist)

def is_matryoshka(bbox1, bbox2, max_overpercent, min_edgedist, min_edges):
    overpercent = calc_overpercent(bbox1, bbox2)
    edgedist = calc_edgedist(bbox1, bbox2)
    num_edges = sum(i < float(min_edgedist) for i in edgedist)
    if(overpercent > float(max_overpercent) and num_edges > int(min_edges)):
        return(True)
    else:
        return(False)

def process_detections(json_image, overlap, edge_dist, min_edges, upper_conf, lower_conf,
                       policy=DEFAULT_POLICY):
    """Return a mask in original index order using an explicitly named policy.

    category-confidence-v1 compares retained, same-category detections in descending
    confidence order. legacy-matryoshka-v1 preserves the historical ordered policy.
    """
    if policy not in {DEFAULT_POLICY, LEGACY_POLICY}:
        raise ValueError(f'Unsupported suppression policy: {policy}')
    validate_detections(json_image)
    for name, value in [('overlap', overlap), ('edge_dist', edge_dist),
                        ('upper_conf', upper_conf), ('lower_conf', lower_conf)]:
        if not math.isfinite(float(value)) or not 0 <= float(value) <= 1:
            raise ValueError(f'{name} must be finite and between 0 and 1')
    if (isinstance(min_edges, bool)
            or int(min_edges) != float(min_edges)
            or not 0 <= int(min_edges) <= 4):
        raise ValueError('min_edges must be an integer between 0 and 4')
    n = len(json_image['detections'])
    if policy == DEFAULT_POLICY:
        detections = json_image['detections']
        valid_image = [False] * n
        order = sorted((i for i in range(n) if detections[i]['conf'] >= float(lower_conf)),
                       key=lambda i: (-detections[i]['conf'], tuple(detections[i]['bbox']),
                                      detections[i]['category'], i))
        retained = []
        for index in order:
            candidate = detections[index]
            suppress = False
            if candidate['conf'] < float(upper_conf):
                for previous in retained:
                    reference = detections[previous]
                    if (candidate['category'] == reference['category']
                            and check_overlap(reference['bbox'], candidate['bbox'])
                            and is_matryoshka(reference['bbox'], candidate['bbox'],
                                             overlap, edge_dist, min_edges)):
                        suppress = True
                        break
            if not suppress:
                valid_image[index] = True
                retained.append(index)
        return valid_image
    valid_image = [True for i in range(n)]
    for i in reversed(range(0,n-1)):
        json_detection0 = json_image['detections'][i]
        bbox0 = json_detection0['bbox']
        for j in reversed(range(i+1,n)):
            json_detection = json_image['detections'][j]
            bbox = json_detection['bbox']
            if(check_overlap(bbox0, bbox)):
                if(float(json_detection['conf']) < float(upper_conf)):
                    matryoshka = is_matryoshka(bbox0, bbox, overlap, edge_dist, min_edges)
                else: 
                    matryoshka = False
                if(matryoshka):
                    valid_image[j] = False
    for i in range(0,n):
        if(json_image['detections'][i]['conf'] < float(lower_conf)):
            valid_image[i] = False
    return(valid_image)

def contains_animal(json_image):
    """Inspect validated detections; failed images must not be reported as blanks."""
    return any(detection['category'] == '1' for detection in validate_detections(json_image))
