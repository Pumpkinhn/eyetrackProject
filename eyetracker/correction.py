# 这是系统运行的主程序
import socket
import subprocess
import numpy as np
import cv2
import pygame
import time
import traceback

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
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

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

fixs = []
oris = []

# 绘制白色背景和“按下空格键开始测试”的文字
screen.fill((255, 255, 255))
text = font.render("按下空格键开始校准程序", True, (0, 0, 0))
text_rect = text.get_rect(center=(width / 2, height / 2))
screen.blit(text, text_rect)
pygame.display.update()


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
                    print(M)
                    Tracking = True
                    timer = time.time()
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
            elif data[0] == '0':
                continue
            position = np.array([(width * float(data[2]), height * float(data[3]))], dtype=np.float32)
            # 应用仿射变化校正
            fixed_position = cv2.transform(position.reshape(1, -1, 2), M).reshape(-1, 2)
            screen.fill((255, 255, 255))
            for p in calibration_points:
                pygame.draw.circle(screen, BLUE, p, 10)

            fixs.append((int(fixed_position[0][0]), int(fixed_position[0][1])))
            if len(fixs) > 3:
                fixs.pop(0)

            for fix in fixs:
                pygame.draw.circle(screen, GREEN, fix, 10)

            oris.append((int(width * float(data[2])), int(height * float(data[3]))))
            if len(oris) > 3:
                oris.pop(0)

            for ori in oris:
                pygame.draw.circle(screen, RED, ori, 10)

            pygame.display.update()
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
