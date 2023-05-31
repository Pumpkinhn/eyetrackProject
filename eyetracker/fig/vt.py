import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 读取数据
data = data_correct = pd.read_csv('../data/gaze_data_123.csv', header=None, names=['validity', 'timestamp', 'x', 'y'])
data['x'] *= 1920
data['y'] *= 1080

# 计算速度
v_window = 2  # 窗口大小
length = len(data)
validity, timestamp, x, y = data['validity'].values, data['timestamp'].values, data['x'].values, data['y'].values
vel = []

for i in range(1, length):
    if validity[i] == 1 and validity[i - 1] == 1:
        start = np.array((x[i - 1], y[i - 1]))
        end = np.array((x[i], y[i]))
        dist = np.sqrt(sum(np.power((end - start), 2)))
        vel.append(dist / (timestamp[i] - timestamp[i - 1]))
    else:
        vel.append(np.nan)

vel_filtered = []
for i in range(v_window, length):
    if not np.isnan(vel[i - v_window:i]).all():
        vel_filtered.append(np.mean(vel[i - v_window:i]))
    else:
        vel_filtered.append(np.nan)

# 绘制 VT 图像
fig, ax = plt.subplots()
ax.scatter(timestamp[2:], vel_filtered, color='blue')
ax.set_xlabel('Timestamp (ms)')
ax.set_ylabel('Velocity (px/ms)')
ax.set_ylim([0, 0.002])
plt.show()


