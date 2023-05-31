import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei'] # 中文字体
plt.rcParams['font.weight'] = 'bold' # 字体加粗
plt.rcParams['font.size'] = 20 # 字体大小
plt.rcParams['axes.unicode_minus'] = False # 解决负号无法正常显示的问题

data = data_correct = pd.read_csv('../data/test02.csv', header=None, names=['validity', 'timestamp', 'x', 'y'])

x_axis = data['timestamp']
y_axis = data['validity']

fig, ax = plt.subplots()
ax.scatter(x_axis, y_axis, marker='x')

ax.set_xlabel('时间戳/us')
ax.set_ylabel('有效性')
ax.set_ylim([-0.5, 1.5])
ax.set_yticks([0, 1])

plt.show()