import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei']     # 中文字体
plt.rcParams['font.weight'] = 'bold'     # 字体加粗
plt.rcParams['font.size'] = 16    # 字体大小
plt.rcParams['axes.unicode_minus'] = False       # 解决负号无法正常显示的问题

# 读取数据
data = pd.read_csv("../data/gaze_data_07.csv", header=None, names=['timestamp', 'position_x', 'position_y'])
ori_position = [(0.2, 0.2), (0.2, 0.5), (0.2, 0.8),
                (0.5, 0.2), (0.5, 0.5), (0.5, 0.8),
                (0.8, 0.2), (0.8, 0.5), (0.8, 0.8)]

# 绘制散点图
plt.scatter(data["position_x"], data["position_y"], marker="x", color="blue")
# 绘制标识点
for p in ori_position:
    plt.plot(p[0], p[1], marker="+", markersize=15, color="red")

# 设置坐标轴范围和标签
plt.xlim([0, 1])
plt.ylim([1, 0])
plt.xlabel("屏幕宽度/%")
plt.ylabel("屏幕高度/%")

# 添加图例
plt.legend(["标识点", "测试点"])

plt.show()
