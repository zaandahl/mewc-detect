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
    percent = overlap/(area1+area2-overlap)
    return(round(percent, 4))

def calc_overpercent(bbox1, bbox2):
    coords1 = get_coords(bbox1)
    area1 = calc_area(coords1)
    coords2 = get_coords(bbox2)
    area2 = calc_area(coords2)
    overlap = calc_overlap(bbox1, bbox2)
    percent = overlap/(area1+area2-overlap)
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

def process_detections(json_image, overlap, edge_dist, min_edges, upper_conf, lower_conf):
    n = len(json_image['detections'])
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
    n = len(json_image['detections'])
    animal_there = False
    for i in range(0,n):
        if json_image['detections'][i]['category'] == "1":
            animal_there = True
    return(animal_there)