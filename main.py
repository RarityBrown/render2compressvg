import os, io, subprocess
import xml.etree.ElementTree as ET
import skimage.io, skimage.metrics
os.environ['path'] += r';C:\Program Files\Inkscape\bin' # https://stackoverflow.com/questions/46265677/get-cairosvg-working-in-windows
import cairosvg
import cv2
import numpy as np


COMPARISON_THRESHOLD = 1e-32
RESVG_PATH = r"C:\Users\newdell\Desktop\svg2png_speed\resvg.exe"

def optimize_svg_visually_lossless(svg_string, scale = 1, renderer='cairosvg'):
    svg_root = ET.fromstring(svg_string)
    view_box = svg_root.get('viewBox', None)
    if view_box:
        view_box_values = view_box.split(' ')
        if max(float(view_box_values[2]), float(view_box_values[3])) < 1000:
            scale = scale * 2
        if max(float(view_box_values[2]), float(view_box_values[3])) < 600:
            scale = scale * 2
    if renderer == 'cairosvg':
        png_file_root_bytes = cairosvg.svg2png(bytestring=svg_string, scale=scale, background_color='white')  # white is a workaround for is_match
    elif renderer == 'resvg':
        process = subprocess.Popen(
            [RESVG_PATH, "--resources-dir", os.path.dirname(RESVG_PATH), "--background", "white", "-", "-c"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        png_file_root_bytes, errors = process.communicate(input=svg_string.encode())
        if process.returncode != 0:
            raise Exception("resvg error:", errors.decode())
    else:
        raise NotImplementedError


    image_original = skimage.io.imread(io.BytesIO(png_file_root_bytes))
    img1_array = np.frombuffer(png_file_root_bytes, dtype=np.uint8)
    img1 = cv2.imdecode(img1_array, cv2.IMREAD_GRAYSCALE)
    _, img1_bin = cv2.threshold(img1, 127, 1, cv2.THRESH_BINARY)

    def is_match(image2_bytes):
        img2_array = np.frombuffer(image2_bytes, dtype=np.uint8)
        img2 = cv2.imdecode(img2_array, cv2.IMREAD_GRAYSCALE)
        if img1.shape != img2.shape:
            return False
        _, img2_bin = cv2.threshold(img2, 127, 1, cv2.THRESH_BINARY)

        intersection = np.logical_and(img1_bin, img2_bin)
        union = np.logical_or(img1_bin, img2_bin)
        iou = np.sum(intersection) / np.sum(union)       
        return iou >= 1-COMPARISON_THRESHOLD

        image_to_compare = skimage.io.imread(io.BytesIO(image2_bytes))
        try:
            score = skimage.metrics.normalized_root_mse(image_original, image_to_compare)     # 6x  slower  200ms
            skimage.metrics.structural_similarity(image1, image2, win_size = 3)             # 60x slower 2000ms
            return score <= 1e-8
        except ValueError:           # ValueError: Input images must have the same dimensions.
            return False
    
    # Register namespaces to avoid 'ns0' in the output
    def register_namespaces(svg_string):
        svg_file_like_object = io.StringIO(svg_string)
        namespaces = dict([
            node for _, node in ET.iterparse(svg_file_like_object, events=['start-ns'])
        ])
        for ns in namespaces:
            ET.register_namespace(ns, namespaces[ns])
    
    register_namespaces(svg_string)
    compressed_svg_tree = ET.ElementTree(ET.fromstring(svg_string))
    svg_string = ET.tostring(compressed_svg_tree.getroot())
    for element in compressed_svg_tree.iter():
        original_attributes = element.attrib.copy()
        exclude_attributes = {'x', 'y', "font-family", 'font-size', 'xmlns:xlink'}
        for attr in list(element.attrib):
            if attr not in exclude_attributes:
                del element.attrib[attr]
                svg_string = ET.tostring(compressed_svg_tree.getroot())
                if renderer == 'cairosvg':
                    png_file_new_bytestring = cairosvg.svg2png(bytestring=svg_string, scale=scale, background_color='white')  # white is a workaround for is_match
                elif renderer == 'resvg':
                    process = subprocess.Popen(
                        [RESVG_PATH, "--resources-dir", os.path.dirname(RESVG_PATH), "--background", "white", "-", "-c"],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    png_file_new_bytestring, errors = process.communicate(input=svg_string)
                    if process.returncode != 0:
                        raise Exception("resvg error:", errors.decode())
                else:
                    raise NotImplementedError

                if not is_match(png_file_new_bytestring):
                    element.set(attr, original_attributes[attr])

    # compressed_svg_tree.write(svg_compressed, encoding='utf-8', xml_declaration=True)
    return svg_string.decode()