# 这是系统运行的主程序
import socket
import subprocess
import numpy as np
import cv2
import pygame
import time
import traceback

# 重要参数
max_gap = 8  # 最大间隙长度
max_vel = 0.0008  # 速度阈值
max_dur = 5  # 最大注视间隔
min_dur = 40  # 最短注视长度
max_dis = 50  # 最大注视间距
size_of_AOI = 30  # 感兴趣区大小
v_window = 2  # 窗口平均

# 数据列表
points = []
gaze_points = []
ori_points = []

# socket配置
TCP_IP = '127.0.0.1'
TCP_PORT = 5001
BUFFER_SIZE = 1024
# socket初始化，用于链接眼动API
dir = "../tobiiAPI/Debug/tobiiAPI.exe"
gaze_process = None
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# pygame部分
pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # 设置为全屏
font = pygame.font.SysFont("Microsoft YaHei", 50)  # 字体
clock = pygame.time.Clock()  # 时钟
timer = 0  # 计时器

# 屏幕分辨率
width = float(screen.get_width())
height = float(screen.get_height())

# 颜色
BLUE = (0, 0, 255)
RED = (255, 0, 0)

# 设置程序运行状态与测试运行状态
running = True
calibration = False
Tracking = False
Working = False

# 校正程序
calibration_index = 0
# 设置校准用点的位置
calibration_points = [(width * 0.2, height * 0.2), (width * 0.5, height * 0.2), (width * 0.8, height * 0.2),
                      (width * 0.2, height * 0.5), (width * 0.5, height * 0.5), (width * 0.8, height * 0.5),
                      (width * 0.2, height * 0.8), (width * 0.5, height * 0.8), (width * 0.8, height * 0.8)]
# 仿射变换矩阵初始化
M = []

# 绘制白色背景和“按下空格键开始测试”的文字
screen.fill((255, 255, 255))
text = font.render("按下空格键开始校准程序", True, (0, 0, 0))
text_rect = text.get_rect(center=(width / 2, height / 2))
screen.blit(text, text_rect)
pygame.display.update()

# 加载背景图片
bg_img = pygame.image.load("./src/bg001.jpg")
# 缩放背景图片为全屏大小
bg_img = pygame.transform.scale(bg_img, (int(width), int(height)))

# 控制背景图片显示的标志位，默认为False
show_bg_img = False

last_point = (0, 0)


# 主动注视点计算
def gaze_cal(arrs):
    # 读取数据
    validity = [arr[0] for arr in arrs]
    timestamp = [arr[1] for arr in arrs]
    x = np.array([arr[2] for arr in arrs])
    y = np.array([arr[3] for arr in arrs])
    length = len(validity)
    vel = []
    # 将超出屏幕范围的点的有效性置零
    validity = np.round(validity).astype(int)
    validity[(x < 20) | (x > 1900) | (y < 20) | (y > 1060)] = 0

    # 间隙插值模块
    start_i = []
    end_i = []
    # 筛出间隙的起点与终点
    for i in range(length - 2):
        if validity[i] == 1 and validity[i + 1] == 0:
            start_i.append(i)
        if i > 0 and validity[i] == 0 and validity[i + 1] == 1:
            end_i.append(i)
    # 对间隙符合要求的进行线性插值
    for start, end in zip(start_i, end_i):
        gap_len = end - start
        if gap_len < max_gap:
            gap_x = ((x[end + 1] - x[start]) * np.arange(gap_len + 1) / float(gap_len + 1) + x[start]).tolist()
            gap_y = ((y[end + 1] - y[start]) * np.arange(gap_len + 1) / float(gap_len + 1) + y[start]).tolist()
            for j in range(1, len(gap_x)):
                x[start + j] = gap_x[j]
                y[start + j] = gap_y[j]
                validity[start + j] = 1

    # 速度计算模块
    for i in range(1, length):
        if validity[i] == 1 and validity[i - 1] == 1:
            start = np.array((x[i - 1], y[i - 1]))
            end = np.array((x[i], y[i]))
            dist = np.sqrt(sum(np.power((end - start), 2)))
            vel.append(dist / (timestamp[i] - timestamp[i - 1]))
        else:
            vel.append(np.nan)
    # 对速度进行移动窗口平均
    vel_filtered = []
    for i in range(v_window, length):
        if not np.isnan(vel[i - v_window:i]).all():
            vel_filtered.append(np.mean(vel[i - v_window:i]))
        else:
            vel_filtered.append(np.nan)

    # I-VT分类器
    vel = np.array(vel_filtered)
    nan_index = np.where(np.isnan(vel))
    vel[nan_index] = 1000
    # 速度分类
    fix_idx = vel < max_vel
    vel[nan_index] = np.nan
    start_idx, end_idx = [], []
    if fix_idx[0] and fix_idx[1]:
        start_idx.append(0)
    for i in range(len(vel) - 1):
        if not fix_idx[i] and fix_idx[i + 1]:
            start_idx.append(i + 1)
        if fix_idx[i] and not fix_idx[i + 1]:
            end_idx.append(i)
    if len(start_idx) > len(end_idx):
        end_idx.append(len(vel) - 1)

    # 合并剔除
    i = 0
    while i < len(start_idx) - 2:
        # 合并时空接近的注视点
        if start_idx[i + 1] - end_idx[i] < max_dur:
            # 切片获取需要计算的数据
            x_slice1 = x[start_idx[i]: end_idx[i] + 1]
            y_slice1 = y[start_idx[i]: end_idx[i] + 1]
            x_slice2 = x[start_idx[i + 1]: end_idx[i + 1] + 1]
            y_slice2 = y[start_idx[i + 1]: end_idx[i + 1] + 1]
            # 使用numpy库计算平均值
            x1 = np.mean(x_slice1)
            y1 = np.mean(y_slice1)
            x2 = np.mean(x_slice2)
            y2 = np.mean(y_slice2)
            distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            if distance < max_dis:
                del end_idx[i]
                del start_idx[i + 1]
                # 删除注视点后不需要递增i的值，因为下一个注视点的索引位置并没有发生变化
            else:
                i += 1
        else:
            i += 1
    # 剔除短注视
    i = 0
    while i < len(start_idx) - 1:
        if end_idx[i] - start_idx[i] < min_dur:
            del start_idx[i]
            del end_idx[i]
            # 同样不需要递增i的值
        else:
            i += 1

    # 筛选出最长的一段数据并计算平均值（置信度）
    means = []
    max_validity_len = 0
    max_start = 0
    max_end = 0
    for i in range(len(start_idx)):
        start = start_idx[i]
        end = end_idx[i]
        if end - start > max_validity_len:
            max_validity_len = end - start
            max_start = start
            max_end = end
    if max_end != 0:
        valid_x = x[max_start:max_end + 1]
        valid_y = y[max_start:max_end + 1]
        mean_x = np.mean(valid_x)
        mean_y = np.mean(valid_y)
        means.append((mean_x, mean_y))
    return means


try:
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # 按下空格键，清空屏幕，开始计时
                screen.fill((255, 255, 255))
                timer = time.time()
                calibration = True
                # 调用可执行文件
                gaze_process = subprocess.Popen(dir)
                s.connect((TCP_IP, TCP_PORT))
                # 绘制第一个点
                pygame.draw.circle(screen, BLUE, calibration_points[calibration_index], 10)
                pygame.display.update()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # 按下esc键，退出程序
                if gaze_process:
                    gaze_process.terminate()
                running = False

        # 校正阶段
        if calibration:
            # 获取眼动数据
            if 1 < time.time() - timer < 2.5:
                data = s.recv(BUFFER_SIZE).decode().split(",")
                if data[0].isdigit() and int(data[0]) == 1:
                    point = (width * float(data[2]), height * float(data[3]))
                    distance = np.sqrt((point[0] - calibration_points[calibration_index][0]) ** 2 + (
                            point[1] - calibration_points[calibration_index][1]) ** 2)
                    if distance < 200:
                        points.append(point)
            # 每三秒换校正用点并计算均值
            if time.time() - timer > 3:
                gaze_point = np.mean(points, axis=0)
                gaze_points.append(gaze_point)
                points.clear()
                ori_points.append(calibration_points[calibration_index])
                calibration_index += 1
                if calibration_index == 9:
                    calibration = False
                    # 估计仿射变换矩阵
                    M, _ = cv2.estimateAffinePartial2D(np.array(gaze_points), np.array(ori_points))
                    Tracking = True
                    timer = time.time()
                    if show_bg_img:
                        # 显示背景图片
                        screen.blit(bg_img, (0, 0))
                    continue
                # 绘制校正用点
                screen.fill((255, 255, 255))
                pygame.draw.circle(screen, BLUE, calibration_points[calibration_index], 10)
                timer = time.time()
                pygame.display.update()

        # 跟踪阶段
        if Tracking:
            # 获取数据
            data = s.recv(BUFFER_SIZE).decode().split(",")
            if data[0] != '0' and data[0] != '1':
                continue
            position = np.array([(width * float(data[2]), height * float(data[3]))], dtype=np.float32)
            # 应用仿射变化校正
            fixed_position = cv2.transform(position.reshape(1, -1, 2), M).reshape(-1, 2)
            points.append((int(data[0]), int(data[1]), fixed_position[0][0], fixed_position[0][1]))
            # 每两秒计算注视点
            if time.time() - timer > 2.2:
                new_gaze = gaze_cal(points)
                points.clear()
                timer = time.time()
                # 得到最新的注视点
                if new_gaze:
                    screen.blit(bg_img, (0, 0))
                    point = new_gaze[-1]
                    distance = ((point[0] - last_point[0]) ** 2 + (point[1] - last_point[1]) ** 2) ** 0.5
                    if distance > size_of_AOI:
                        last_point = point
                        pygame.draw.circle(screen, RED, (int(point[0]), int(point[1])), 60, 5)
                        pygame.display.update()
                        # to do：将新目标的坐标和方向传递给外视镜
        # 控制帧率
        clock.tick(60)

except Exception as e:
    print(e)
    # 捕获异常并打印堆栈信息
    traceback.print_exc()
finally:
    # 确保关闭API
    if gaze_process:
        gaze_process.terminate()
    s.close()
    pygame.quit()
