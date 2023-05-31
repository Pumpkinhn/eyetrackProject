import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 读取数据
data = data_correct = pd.read_csv('data/gaze_data_08.csv', header=None, names=['validity', 'timestamp', 'x', 'y'])

# 重要参数
max_gap = 8  # 最大间隙长度
max_vel = 0.0008  # 速度阈值
max_dur = 5  # 最大注视间隔
min_dur = 40  # 最短注视长度
max_dis = 50  # 最大注视间距
size_of_AOI = 30  # 感兴趣区大小
v_window = 2  # 窗口平均

width = 1920
height = 1080

# 取出数据
validity = data['validity'].values
timestamp = data['timestamp'].values
x = data['x'].values
y = data['y'].values
length = len(validity)
vel = []
# 换算为像素
x = np.array(x) * width
y = np.array(y) * height

# 绘制初始数据图像
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(x, y, 'o')
ax.set(title='Initial Data', xlim=[0, 1920], ylim=[1080, 0])
plt.show()

# 绘制初始数据图像
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(timestamp, x, '-')
ax.set(title='Initial Data')
plt.show()

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
        gap_x = ((x[end+1] - x[start]) * np.arange(gap_len + 1) / float(gap_len + 1) + x[start]).tolist()
        gap_y = ((y[end+1] - y[start]) * np.arange(gap_len + 1) / float(gap_len + 1) + y[start]).tolist()
        for j in range(1, len(gap_x)):
            x[start+j] = gap_x[j]
            y[start+j] = gap_y[j]
            validity[start+j] = 1

# 绘制插值图像
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(timestamp, x, '-')
ax.set(title='After Gap Interpolation')
plt.show()

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
# 绘制速度图像
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(timestamp[1:-1], vel_filtered, '-')
ax.set(title='Velocity Plot', xlabel='Time (sec)', ylabel='Velocity (pixels/sec)')
plt.show()
# I-VT分类器
vel = np.array(vel_filtered)
nan_index = np.where(np.isnan(vel) == True)
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
if fix_idx[len(vel) - 2] and fix_idx[len(vel) - 1]:
    end_idx.append(len(vel) - 1)

# 绘制最终结果图像
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(x, y, 'o')
for start, end in zip(start_idx, end_idx):
    ax.plot(x[start:end+1], y[start:end+1], 'r')
ax.set(title='Fixation Detection', xlim=[0, 1920], ylim=[1080, 0])
plt.show()

# 合并剔除
i = 0
while i < len(start_idx) - 2:
    # 合并时空接近的注视点
    if start_idx[i+1] - end_idx[i] < max_dur:
        # 切片获取需要计算的数据
        x_slice1 = x[start_idx[i]: end_idx[i]+1]
        y_slice1 = y[start_idx[i]: end_idx[i]+1]
        x_slice2 = x[start_idx[i+1]: end_idx[i+1]+1]
        y_slice2 = y[start_idx[i+1]: end_idx[i+1]+1]
        # 使用numpy库计算平均值
        x1 = np.mean(x_slice1)
        y1 = np.mean(y_slice1)
        x2 = np.mean(x_slice2)
        y2 = np.mean(y_slice2)
        distance = ((x1-x2)**2 + (y1-y2)**2)**0.5
        if distance < max_dis:
            del end_idx[i]
            del start_idx[i+1]
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

# 绘制最终结果图像
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(x, y, 'o')
for start, end in zip(start_idx, end_idx):
    ax.plot(x[start:end+1], y[start:end+1], 'r')
ax.set(title='Final Fixation Detection', xlim=[0, 1920], ylim=[1080, 0])
plt.show()
