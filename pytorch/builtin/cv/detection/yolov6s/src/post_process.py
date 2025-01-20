#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import argparse
import os
import cv2
import time
import math
import torch
import numpy as np
import os.path as osp

from tqdm import tqdm
from pathlib import Path
from PIL import ImageFont
from collections import deque

from yolov6.utils.events import LOGGER, load_yaml
from yolov6.layers.common import DetectBackend
#from yolov6.data.data_augment import letterbox
from yolov6.data.datasets import LoadData
from yolov6.utils.nms import non_max_suppression
from yolov6.utils.torch_utils import get_model_info


class_names = [ 'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
         'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
         'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
         'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
         'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
         'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
         'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
         'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
         'hair drier', 'toothbrush' ]  # class names

def detect(save_img=True):
    names = ['person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat', 'traffic light',
         'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat', 'dog', 'horse', 'sheep', 'cow',
         'elephant', 'bear', 'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
         'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard',
         'tennis racket', 'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
         'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
         'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote', 'keyboard', 'cell phone',
         'microwave', 'oven', 'toaster', 'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear',
         'hair drier', 'toothbrush']
    
    source, numpys, imgsz, save_dir, scales, conf_thres, iou_thres = opt.image, opt.numpys, opt.img_size, opt.save_dir, opt.scales, opt.conf_thres, opt.iou_thres
    stride = 32
    half = False
    max_det = 1000
    save_img=True
    classes=None
    agnostic_nms=False
    save_txt=False
    hide_labels=False
    hide_conf=False
    view_img=False
    ''' Model Inference and results visualization '''
    vid_path, vid_writer, windows = None, None, []
    fps_calculator = CalcFPS()
    webcam=False
    webcam_addr=0
    files=LoadData(source, webcam, webcam_addr)
    root = os.path.dirname(os.path.dirname(__file__))
    font = os.path.join(root, 'src/yolov6/utils/Arial.ttf')
    for img_src, img_path, vid_cap in tqdm(files):
        '''
        img, img_src = process_image(img_src, opt.img_size, stride, half)
        img = img
        if len(img.shape) == 3:
            img = img[None]
            # expand for batch dim
        t1 = time.time()
        img *= 255
        img = img.numpy().astype(np.uint8)
        '''

        from yolov6.assigners.anchor_generator import generate_anchors
        from yolov6.utils.general import dist2bbox
        cls_score_list0, cls_score_list1, cls_score_list2, reg_lrtb_list0, reg_lrtb_list1, reg_lrtb_list2 = numpys
        cls_score_list0 = torch.from_numpy(np.squeeze(np.load(cls_score_list0), -1)*scales[0])
        cls_score_list1 = torch.from_numpy(np.squeeze(np.load(cls_score_list1),-1)*scales[1])
        cls_score_list2 = torch.from_numpy(np.squeeze(np.load(cls_score_list2),-1)*scales[2])
        reg_lrtb_list0 = torch.from_numpy(np.squeeze(np.load(reg_lrtb_list0),-1)*scales[3])
        reg_lrtb_list1 = torch.from_numpy(np.squeeze(np.load(reg_lrtb_list1),-1)*scales[4])
        reg_lrtb_list2 = torch.from_numpy(np.squeeze(np.load(reg_lrtb_list2),-1)*scales[5])
        cls_score_list = torch.cat((cls_score_list0, cls_score_list1, cls_score_list2), axis=-1).permute(0, 2, 1)
        reg_lrtb_list = torch.cat((reg_lrtb_list0, reg_lrtb_list1, reg_lrtb_list2), axis=-1).permute(0, 2, 1)
        print(cls_score_list.shape, reg_lrtb_list.shape)
        anchor_points = torch.from_numpy(np.load("/ts.knight-modelzoo/pytorch/builtin/cv/detection/yolov6s/src/anchor_points.npy")) # yolov6small
        stride_tensor = torch.from_numpy(np.load("/ts.knight-modelzoo/pytorch/builtin/cv/detection/yolov6s/src/stride_tensor.npy"))
        pred_bboxes = dist2bbox(reg_lrtb_list, anchor_points, box_format='xywh')
        pred_bboxes *= stride_tensor
        outputs = torch.cat(
            [
                pred_bboxes,
                torch.ones((1, pred_bboxes.shape[1], 1), device=pred_bboxes.device, dtype=pred_bboxes.dtype),
                cls_score_list
            ],
            axis=-1) # 1, 8400, 85
        det = non_max_suppression(outputs, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)[0]
        t2 = time.time()

        if webcam:
            save_path = osp.join(save_dir, webcam_addr)
            txt_path = osp.join(save_dir, webcam_addr)
        else:
            # Create output files in nested dirs that mirrors the structure of the images' dirs
            rel_path = osp.relpath(osp.dirname(img_path), osp.dirname(source))
            save_path = osp.join(save_dir, rel_path, osp.basename(img_path))  # im.jpg
            txt_path = osp.join(save_dir, rel_path, 'labels', osp.splitext(osp.basename(img_path))[0])
            os.makedirs(osp.join(save_dir, rel_path), exist_ok=True)
        gn = torch.tensor(img_src.shape)[[1, 0, 1, 0]]  # normalization gain whwh
        img_ori = img_src.copy()

        # check image and font
        assert img_ori.data.contiguous, 'Image needs to be contiguous. Please apply to input images with np.ascontiguousarray(im).'
        font_check(font)

        if len(det):
            det[:, :4] = rescale((imgsz, imgsz), det[:, :4], img_src.shape).round()
            for *xyxy, conf, cls in reversed(det):
                if save_txt:  # Write to file
                    xywh = (box_convert(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                    line = (cls, *xywh, conf)
                    with open(txt_path + '.txt', 'a') as f:
                        f.write(('%g ' * len(line)).rstrip() % line + '\n')

                if save_img:
                    class_num = int(cls)  # integer class
                    label = None if hide_labels else (class_names[class_num] if hide_conf else f'{class_names[class_num]} {conf:.2f}')

                    plot_box_and_label(img_ori, max(round(sum(img_ori.shape) / 2 * 0.003), 2), xyxy, label, color=generate_colors(class_num, True))

            img_src = np.asarray(img_ori)
 
        if view_img:
            if img_path not in windows:
                windows.append(img_path)
                cv2.namedWindow(str(img_path), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                cv2.resizeWindow(str(img_path), img_src.shape[1], img_src.shape[0])
            cv2.imshow(str(img_path), img_src)
            cv2.waitKey(1)  # 1 millisecond

        # Save results (image with detections)
        if save_img:
            if files.type == 'image':
                print(f'save picture to {save_path}')
                cv2.imwrite(save_path, img_src)
            else:  # 'video' or 'stream'
                if vid_path != save_path:  # new video
                    vid_path = save_path
                    if isinstance(vid_writer, cv2.VideoWriter):
                        vid_writer.release()  # release previous video writer
                    if vid_cap:  # video
                        fps = vid_cap.get(cv2.CAP_PROP_FPS)
                        w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    else:  # stream
                        fps, w, h = 30, img_ori.shape[1], img_ori.shape[0]
                    save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                    vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                vid_writer.write(img_src)

def process_image(img_src, img_size, stride, half):
        '''Process image before image inference.'''
        image = letterbox_my(img_src, img_size, stride=stride)[0]
        # Convert
        image = image.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
        image = torch.from_numpy(np.ascontiguousarray(image))
        image = image.half() if half else image.float()  # uint8 to fp16/32
        image /= 255  # 0 - 255 to 0.0 - 1.0

        return image, img_src

def rescale(ori_shape, boxes, target_shape):
    '''Rescale the output to the original image shape'''
    ratio = min(ori_shape[0] / target_shape[0], ori_shape[1] / target_shape[1])
    padding = (ori_shape[1] - target_shape[1] * ratio) / 2, (ori_shape[0] - target_shape[0] * ratio) / 2

    boxes[:, [0, 2]] -= padding[0]
    boxes[:, [1, 3]] -= padding[1]
    boxes[:, :4] /= ratio

    boxes[:, 0].clamp_(0, target_shape[1])  # x1
    boxes[:, 1].clamp_(0, target_shape[0])  # y1
    boxes[:, 2].clamp_(0, target_shape[1])  # x2
    boxes[:, 3].clamp_(0, target_shape[0])  # y2

    return boxes

def check_img_size(self, img_size, s=32, floor=0):
    """Make sure image size is a multiple of stride s in each dimension, and return a new shape list of image."""
    if isinstance(img_size, int):  # integer i.e. img_size=640
        new_size = max(make_divisible(img_size, int(s)), floor)
    elif isinstance(img_size, list):  # list i.e. img_size=[640, 480]
        new_size = [max(make_divisible(x, int(s)), floor) for x in img_size]
    else:
        raise Exception(f"Unsupported type of img_size: {type(img_size)}")

    if new_size != img_size:
        print(f'WARNING: --img-size {img_size} must be multiple of max stride {s}, updating to {new_size}')
    return new_size if isinstance(img_size,list) else [new_size]*2

def make_divisible(self, x, divisor):
    # Upward revision the value x to make it evenly divisible by the divisor.
    return math.ceil(x / divisor) * divisor

def draw_text(
    img,
    text,
    font=cv2.FONT_HERSHEY_SIMPLEX,
    pos=(0, 0),
    font_scale=1,
    font_thickness=2,
    text_color=(0, 255, 0),
    text_color_bg=(0, 0, 0),
):

    offset = (5, 5)
    x, y = pos
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_w, text_h = text_size
    rec_start = tuple(x - y for x, y in zip(pos, offset))
    rec_end = tuple(x + y for x, y in zip((x + text_w, y + text_h), offset))
    cv2.rectangle(img, rec_start, rec_end, text_color_bg, -1)
    cv2.putText(
        img,
        text,
        (x, int(y + text_h + font_scale - 1)),
        font,
        font_scale,
        text_color,
        font_thickness,
        cv2.LINE_AA,
    )

    return text_size

def plot_box_and_label(image, lw, box, label='', color=(128, 128, 128), txt_color=(255, 255, 255), font=cv2.FONT_HERSHEY_COMPLEX):
    # Add one xyxy box to image with label
    p1, p2 = (int(box[0]), int(box[1])), (int(box[2]), int(box[3]))
    cv2.rectangle(image, p1, p2, color, thickness=lw, lineType=cv2.LINE_AA)
    if label:
        tf = max(lw - 1, 1)  # font thickness
        w, h = cv2.getTextSize(label, 0, fontScale=lw / 3, thickness=tf)[0]  # text width, height
        outside = p1[1] - h - 3 >= 0  # label fits outside box
        p2 = p1[0] + w, p1[1] - h - 3 if outside else p1[1] + h + 3
        cv2.rectangle(image, p1, p2, color, -1, cv2.LINE_AA)  # filled
        cv2.putText(image, label, (p1[0], p1[1] - 2 if outside else p1[1] + h + 2), font, lw / 3, txt_color,
                    thickness=tf, lineType=cv2.LINE_AA)

def font_check(font='./yolov6/utils/Arial.ttf', size=10):
    # Return a PIL TrueType Font, downloading to CONFIG_DIR if necessary
    assert osp.exists(font), f'font path not exists: {font}'
    try:
        return ImageFont.truetype(str(font) if font.exists() else font.name, size)
    except Exception as e:  # download if missing
        return ImageFont.truetype(str(font), size)

def box_convert(x):
    # Convert boxes with shape [n, 4] from [x1, y1, x2, y2] to [x, y, w, h] where x1y1=top-left, x2y2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2  # x center
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2  # y center
    y[:, 2] = x[:, 2] - x[:, 0]  # width
    y[:, 3] = x[:, 3] - x[:, 1]  # height
    return y

def generate_colors(i, bgr=False):
    hex = ('FF3838', 'FF9D97', 'FF701F', 'FFB21D', 'CFD231', '48F90A', '92CC17', '3DDB86', '1A9334', '00D4BB',
           '2C99A8', '00C2FF', '344593', '6473FF', '0018EC', '8438FF', '520085', 'CB38FF', 'FF95C8', 'FF37C7')
    palette = []
    for iter in hex:
        h = '#' + iter
        palette.append(tuple(int(h[1 + i:1 + i + 2], 16) for i in (0, 2, 4)))
    num = len(palette)
    color = palette[int(i) % num]
    return (color[2], color[1], color[0]) if bgr else color

class CalcFPS:
    def __init__(self, nsamples: int = 50):
        framerate = deque(maxlen=nsamples)

    def update(self, duration: float):
        framerate.append(duration)

    def accumulate(self):
        if len(framerate) > 1:
            return np.average(framerate)
        else:
            return 0.0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=str, help='original image')
    parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
    parser.add_argument('--numpys', nargs='+', type=str, help='model output numpy')
    parser.add_argument('--scales', nargs='+', type=float, help='model output scales')
    parser.add_argument('--save_dir', type=str, default='output', help='save dir for detect')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='display results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    opt = parser.parse_args()

    detect()