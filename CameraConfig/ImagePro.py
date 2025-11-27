import os

import cv2
import numpy as np
from functools import lru_cache

# 全局变量，用于存储预加载的模板
templateNeedle = None
templateNeedle_size = (0, 0)
templateDevice = None
templateDevice_size = (0, 0)
templateLight = None
templateLight_size = (0, 0)


# 缓存模板加载结果
def load_templates():
    global templateNeedle, templateNeedle_size, templateDevice, templateDevice_size, templateLight, templateLight_size
    # 定义模板路径和对应的全局变量
    templates = {
        'templateNeedle.png': ('templateNeedle', 'templateNeedle_size'),
        'templatepad.png': ('templateDevice', 'templateDevice_size'),
        'templateLight.png': ('templateLight', 'templateLight_size')
    }

    # 检查每个模板文件
    for path, (template_var, size_var) in templates.items():
        if os.path.exists(path):
            current_mtime = os.path.getmtime(path)

            # 检查是否需要重新加载
            cache_key = f"{template_var}_mtime"
            if not hasattr(load_templates, cache_key) or getattr(load_templates, cache_key) != current_mtime:
                # 文件发生变化或首次加载，重新读取
                template_img = cv2.imread(path, cv2.IMREAD_COLOR)
                if template_img is not None:
                    globals()[template_var] = template_img
                    globals()[size_var] = template_img.shape[:2]
                    setattr(load_templates, cache_key, current_mtime)
                    print(f"Loaded template: {path}")
                else:
                    print(f"Failed to load template image from {path}")
            # else: 文件未变化，使用缓存中的模板
        else:
            print(f"Template file not found: {path}")


def is_nearby_vectorized(centers_np, x, y, min_distance):
    """
    使用向量化方式判断一个点是否靠近已存在的点。
    优化: 使用平方距离避免sqrt计算
    """
    if centers_np.size == 0:
        return False
    squared_distances = (centers_np[:, 0] - x) ** 2 + (centers_np[:, 1] - y) ** 2
    return np.any(squared_distances < min_distance ** 2)

import cv2
import numpy as np


def template(video, x_dia=0, y_dia=0, equipment=0, sharpen_params=None):
    """快速稳定的模板匹配版本（优化版）"""
    global templateNeedle, templateLight

    # ================================= 步骤1：强制转换为灰度图像 =================================
    if len(video.shape) == 3:
        video_gray = cv2.cvtColor(video, cv2.COLOR_BGR2GRAY)
    else:
        video_gray = video

    # ================================= 步骤2：获取模板并灰度化 =================================
    template_img = templateLight if equipment else templateNeedle
    if template_img is None:
        return None, None, 0, 0

    if len(template_img.shape) == 3:
        template_gray = cv2.cvtColor(template_img, cv2.COLOR_BGR2GRAY)
    else:
        template_gray = template_img

    # ================================= 步骤3：轻量预处理（减少特征破坏）=================================
    # 🔴 优化：减少预处理强度，避免破坏原始特征
    # 仅在需要时进行轻微处理
    video_processed = cv2.GaussianBlur(video_gray, (3, 3), 0)  # 轻微去噪
    template_processed = cv2.GaussianBlur(template_gray, (3, 3), 0)

    # ================================= 步骤4：多尺度模板匹配 =================================
    # 🔴 优化：添加多尺度匹配，提高鲁棒性
    scales = [0.9, 1.0, 1.1]  # 探针可能因距离略有缩放
    best_val = -1
    best_loc = None
    best_scale = 1.0
    best_template = template_processed
    
    for scale in scales:
        # 缩放模板
        if scale != 1.0:
            h, w = template_processed.shape
            new_h, new_w = int(h * scale), int(w * scale)
            if new_h < 10 or new_w < 10:
                continue
            scaled_template = cv2.resize(template_processed, (new_w, new_h))
        else:
            scaled_template = template_processed
        
        # 🔴 优化：只使用最可靠的 TM_CCOEFF_NORMED 方法
        res = cv2.matchTemplate(video_processed, scaled_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        
        if max_val > best_val:
            best_val = max_val
            best_loc = max_loc
            best_scale = scale
            best_template = scaled_template

    # ================================= 步骤5：局部精细化搜索 =================================
    # 🔴 优化：降低阈值从 0.9 到 0.65，接受更多有效匹配
    if best_val > 0.65:
        x, y = best_loc
        h, w = best_template.shape

        # 局部精细化搜索（仅在安全范围内）
        if x > 5 and y > 5 and x + w < video_processed.shape[1] - 5 and y + h < video_processed.shape[0] - 5:
            roi = video_processed[y - 5:y + h + 5, x - 5:x + w + 5]
            refined_res = cv2.matchTemplate(roi, best_template, cv2.TM_CCOEFF_NORMED)
            _, refined_val, _, refined_loc = cv2.minMaxLoc(refined_res)

            if refined_val > best_val:
                x = x - 5 + refined_loc[0]
                y = y - 5 + refined_loc[1]
                best_val = refined_val

        # 计算红点中心并绘制（使用原始模板尺寸）
        orig_h, orig_w = template_gray.shape
        red_dot_x = int(x + (w / best_scale) // 2 + x_dia)
        red_dot_y = int(y + (h / best_scale) // 2 + y_dia)
        
        # 🔴 优化：根据匹配得分调整红点颜色（置信度可视化）
        if best_val > 0.85:
            color = (0, 255, 0)  # 绿色 - 高置信度
        elif best_val > 0.75:
            color = (0, 165, 255)  # 橙色 - 中等置信度
        else:
            color = (0, 0, 255)  # 红色 - 低置信度
        
        cv2.circle(video, (red_dot_x, red_dot_y), 5, color, -1)
        
        # 🔴 优化：始终显示匹配框和得分（帮助调试）
        # cv2.rectangle(video, (x, y), (x + w, y + h), (0, 255, 0), 1)  # 绿色匹配框
        # cv2.putText(video, f"{best_val:.2f}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)

        return red_dot_x, red_dot_y, template_img.shape[0], template_img.shape[1]
    else:
        # 🔴 优化：显示实际匹配得分
        cv2.putText(video, f"No Match (Score={best_val:.2f}, Need>0.65)", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        return None, None, 0, 0


def preprocess_images(video_gray, template_gray, sharpen_params=None):
    """综合图像预处理函数"""
    # 默认锐化参数
    if sharpen_params is None:
        sharpen_params = {'kernel_size': 3, 'sigma': 1.0, 'amount': 1.5, 'threshold': 10}

    # 1. 直方图均衡化（增强对比度）
    video_gray = cv2.equalizeHist(video_gray)
    template_gray = cv2.equalizeHist(template_gray)

    # 2. 高斯模糊去噪（轻微）
    video_gray = cv2.GaussianBlur(video_gray, (3, 3), 0)
    template_gray = cv2.GaussianBlur(template_gray, (3, 3), 0)

    # 3. 锐化处理
    video_gray = sharpen_image(video_gray, **sharpen_params)
    template_gray = sharpen_image(template_gray, **sharpen_params)

    # 4. 边缘增强（可选，对于边缘明显的探针很有效）
    # video_gray = enhance_edges(video_gray)
    # template_gray = enhance_edges(template_gray)

    return video_gray, template_gray


def sharpen_image(image, kernel_size=3, sigma=1.0, amount=1.5, threshold=5):
    """USM锐化算法"""
    # 高斯模糊
    blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)

    # 非锐化掩蔽
    sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)

    # 阈值处理，避免过度锐化平滑区域
    if threshold > 0:
        low_contrast_mask = np.abs(image - blurred) < threshold
        sharpened[low_contrast_mask] = image[low_contrast_mask]

    return sharpened


def enhance_edges(image, low_threshold=50, high_threshold=150):
    """边缘增强"""
    # Canny边缘检测
    edges = cv2.Canny(image, low_threshold, high_threshold)

    # 将边缘叠加到原图
    enhanced = cv2.addWeighted(image, 0.8, edges, 0.2, 0)

    return enhanced


# 可选：自适应预处理（根据图像特性自动调整）
def adaptive_preprocess(image):
    """自适应预处理"""
    # 计算图像对比度
    mean, std = cv2.meanStdDev(image)
    contrast = std[0][0]

    if contrast < 25:  # 低对比度图像
        image = cv2.equalizeHist(image)
        image = sharpen_image(image, amount=2.0)
    elif contrast > 60:  # 高对比度图像
        image = cv2.GaussianBlur(image, (3, 3), 0)
    else:  # 中等对比度
        image = sharpen_image(image, amount=1.5)

    return image


def match_device_templates(video):
    global templateDevice, templateDevice_size

    if templateDevice is None:
        print("模板未加载，无法进行匹配")
        return []

    try:
        with open('Paddia.txt', 'r', encoding='utf-8') as f:
            xdia, ydia = map(int, f.read().strip().split(','))
    except:
        xdia, ydia = 0, 0

    # 灰度转换
    video_gray = cv2.cvtColor(video, cv2.COLOR_BGR2GRAY) if len(video.shape) == 3 else video
    template_gray = cv2.cvtColor(templateDevice, cv2.COLOR_BGR2GRAY) if len(
        templateDevice.shape) == 3 else templateDevice

    original_template_h, original_template_w = template_gray.shape

    # 多尺度匹配
    scales = [0.8, 0.9, 1.0, 1.1, 1.2]
    all_matches = []

    for scale in scales:
        # 缩放模板
        if scale != 1.0:
            new_w = int(original_template_w * scale)
            new_h = int(original_template_h * scale)
            if new_w < 10 or new_h < 10: continue
            template_resized = cv2.resize(template_gray, (new_w, new_h))
        else:
            template_resized = template_gray

        # 执行匹配
        res = cv2.matchTemplate(video_gray, template_resized, cv2.TM_CCOEFF_NORMED)

        # 更严格的阈值设置
        threshold = max(0.85, 0.8)  # 使用固定高阈值或更智能的动态阈值
        locs = np.where(res >= threshold)

        # 只保留每个局部区域的最佳匹配
        temp_matches = []
        for pt in zip(*locs[::-1]):
            temp_matches.append({
                'pt': pt,
                'size': (template_resized.shape[1], template_resized.shape[0]),
                'score': res[pt[1], pt[0]],
                'scale': scale
            })

        # 对当前尺度的匹配进行局部NMS
        temp_matches.sort(key=lambda x: x['score'], reverse=True)
        filtered_matches = []
        for match in temp_matches:
            pt = match['pt']
            w, h = match['size']
            center_x = pt[0] + w // 2
            center_y = pt[1] + h // 2

            # 更严格的重叠检查
            overlap = False
            for selected in filtered_matches:
                s_pt = selected['pt']
                s_w, s_h = selected['size']
                s_center_x = s_pt[0] + s_w // 2
                s_center_y = s_pt[1] + s_h // 2

                # 检查中心点距离和区域重叠
                if (abs(center_x - s_center_x) < max(w, s_w) // 2 and
                        abs(center_y - s_center_y) < max(h, s_h) // 2):
                    overlap = True
                    break

            if not overlap:
                filtered_matches.append(match)

        all_matches.extend(filtered_matches)

    # 全局非极大值抑制
    all_matches.sort(key=lambda x: x['score'], reverse=True)
    final_locations = []

    for match in all_matches:
        pt = match['pt']
        w, h = match['size']
        center_x = pt[0] + w // 2 + xdia
        center_y = pt[1] + h // 2 + ydia

        # 更严格的重叠检查
        overlap = False
        for selected in final_locations:
            s_x, s_y, s_w, s_h = selected
            s_center_x = s_x + s_w // 2
            s_center_y = s_y + s_h // 2

            # 使用更小的重叠阈值
            if (abs(center_x - s_center_x) < min(w, s_w) // 2 and
                    abs(center_y - s_center_y) < min(h, s_h) // 2):
                overlap = True
                break

        if not overlap:
            final_locations.append((center_x, center_y, w, h))
            cv2.circle(video, (center_x, center_y), 4, (0, 255, 255), -1)

    return [(x, y) for x, y, _, _ in final_locations]