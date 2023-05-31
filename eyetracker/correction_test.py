import pandas as pd
import numpy as np
from scipy.spatial import KDTree
import matplotlib.pyplot as plt
from skimage.transform import AffineTransform

# 读取数据
data_correct = pd.read_csv('data/gaze_data_32.csv', header=None, names=['validity', 'timestamp', 'x', 'y'])
data_test = pd.read_csv('data/gaze_data_33.csv', header=None, names=['validity', 'timestamp', 'x', 'y'])

# 取出校准数据
x_front = data_correct['x'].values
y_front = data_correct['y'].values

# 取出校准数据
x_back = data_test['x'].values
y_back = data_test['y'].values

# 注视点坐标
x0 = np.array([0.2, 0.5, 0.8, 0.2, 0.5, 0.8, 0.2, 0.5, 0.8])
y0 = np.array([0.2, 0.2, 0.2, 0.5, 0.5, 0.5, 0.8, 0.8, 0.8])

x1 = np.array(
    [0.1, 0.3, 0.5, 0.7, 0.9, 0.1, 0.3, 0.5, 0.7, 0.9, 0.1, 0.3, 0.5, 0.7, 0.9, 0.1, 0.3, 0.5, 0.7, 0.9, 0.1, 0.3, 0.5,
     0.7, 0.9])
y1 = np.array(
    [0.1, 0.1, 0.1, 0.1, 0.1, 0.3, 0.3, 0.3, 0.3, 0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.7, 0.7, 0.7, 0.7, 0.7, 0.9, 0.9, 0.9,
     0.9, 0.9])

points = np.transpose(np.array((x0, y0)))
points_test = np.transpose(np.array((x1, y1)))

# 计算近似点
tree = KDTree(points)
dist_f, idx_f = tree.query(np.transpose(np.array((x_front, y_front))), k=1)



# 计算误差向量并筛选误差向量较小的点
max_error = 0.1
errors = points[idx_f] - np.transpose(np.array((x_front, y_front)))
good_indices = np.where(np.linalg.norm(errors, axis=1) <= max_error)
good_idx = idx_f[good_indices]
x_clean = x_front[good_indices]
y_clean = y_front[good_indices]

# 计算所有误差向量的平均值和中位值
mean_error = np.mean(errors[good_indices], axis=0)
median_error = np.median(errors[good_indices], axis=0)

# 输出误差向量
abs_error = np.linalg.norm(mean_error)
print('误差向量平均值：{}'.format(mean_error))
print('误差向量中位值：{}'.format(median_error))
print('误差向量绝对值：{}'.format(abs_error))

# 将平均误差向量应用于原始数据
x_corrected_mean = x_back + mean_error[0]
y_corrected_mean = y_back + mean_error[1]

tree_test = KDTree(points_test)
dist_b, idx_b = tree_test.query(np.transpose(np.array((x_corrected_mean, y_corrected_mean))), k=1)

errors_b = points_test[idx_b] - np.transpose(np.array((x_back, y_back)))
good_indices_b = np.where(np.linalg.norm(errors_b, axis=1) <= max_error)

# 计算应用后的误差
errors_mean_corrected = points_test[idx_b] - np.transpose(np.array((x_corrected_mean, y_corrected_mean)))
# 计算所有误差向量的绝对值的平均值
print('平均误差修正后，误差向量绝对值：{}'.format(
    np.linalg.norm(np.mean(np.abs(errors_mean_corrected[good_indices_b]), axis=0))))

# 将中位误差向量应用于原始数据
x_corrected_median = x_back + median_error[0]
y_corrected_median = y_back + median_error[1]
# 计算应用后的误差
errors_median_corrected = points_test[idx_b] - np.transpose(np.array((x_corrected_median, y_corrected_median)))
print('中位误差修正后，误差向量绝对值：{}'.format(
    np.linalg.norm(np.mean(np.abs(errors_median_corrected[good_indices_b]), axis=0))))

# 计算仿射变换矩阵
tform = AffineTransform()
tform.estimate(np.transpose(np.array((x_clean, y_clean))), points[good_idx])

# 套用仿射变换矩阵
# params = [[1.00288351, 0.01975269, -0.02625267],
#           [0.01822246, 0.96070049, 0.08216896],
#           [0., 0., 1.]]
# tform = AffineTransform(matrix=params)

# 输出仿射变换矩阵
# print('仿射变换矩阵：{}'.format(tform.params))

# 应用仿射变换矩阵修正原始数据
xy = np.column_stack((x_back, y_back))
xy_corrected = tform(xy)
x_corrected = xy_corrected[:, 0]
y_corrected = xy_corrected[:, 1]
# 计算应用后的误差
errors_affine_corrected = points_test[idx_b] - np.transpose(np.array((x_corrected, y_corrected)))
print('仿射变换修正后，误差向量绝对值：{}'.format(
    np.linalg.norm(np.mean(np.abs(errors_affine_corrected[good_indices_b]), axis=0))))

# 创建 2x2 的子图
fig, axs = plt.subplots(nrows=2, ncols=2)
# 将子图分别赋值给变量
ax1 = axs[0, 0]
ax2 = axs[0, 1]
ax3 = axs[1, 0]
ax4 = axs[1, 1]

# 绘制眼动点
ax1.set_title('Origin Gaze Point')
ax1.scatter(x1, y1, color='red')
ax1.scatter(x_back, y_back, s=3)
ax1.set_xlim(0, 1)
ax1.set_ylim(1, 0)

# 绘制平均误差修正
ax2.set_title('Mean Fixed Point')
ax2.scatter(x1, y1, color='red')
ax2.scatter(x_corrected_mean, y_corrected_mean, s=3)
ax2.set_xlim(0, 1)
ax2.set_ylim(1, 0)

# 绘制中位误差修正
ax3.set_title('Median Fixed Point')
ax3.scatter(x1, y1, color='red')
ax3.scatter(x_corrected_median, y_corrected_median, s=3)
ax3.set_xlim(0, 1)
ax3.set_ylim(1, 0)

# 绘制仿射变换误差修正
ax4.set_title('AffineTransform Fixed Point')
ax4.scatter(x1, y1, color='red')
ax4.scatter(x_corrected, y_corrected, s=3)
ax4.set_xlim(0, 1)
ax4.set_ylim(1, 0)

# 显示图像
plt.show()
