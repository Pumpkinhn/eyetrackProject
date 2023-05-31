import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

max_gap = 8   # 最大间隙长度

plt.rcParams['font.sans-serif'] = ['SimHei'] # 中文字体
plt.rcParams['font.weight'] = 'bold' # 字体加粗
plt.rcParams['font.size'] = 20 # 字体大小
plt.rcParams['axes.unicode_minus'] = False # 解决负号无法正常显示的问题

data = pd.read_csv('../data/test02.csv', header=None, names=['validity', 'timestamp', 'x', 'y'])

validity = data['validity'].tolist()
timestamp = data['timestamp'].tolist()
x = data['x'].tolist()
y = data['y'].tolist()
length = len(validity)

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

fig, ax = plt.subplots()
ax.scatter(timestamp, validity, marker='x')

ax.set_xlabel('时间戳/us')
ax.set_ylabel('有效性')
ax.set_ylim([-0.5, 1.5])
ax.set_yticks([0, 1])

plt.show()
