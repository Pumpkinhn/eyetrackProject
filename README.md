# 项目文档

## 项目简介

​		本项目基于tobii eyex controller眼动设备，设计并实现了术中主动注视点跟踪算法，以及基于主动注视的外视镜控制系统，包含获取眼动数据、误差校正、非主动眼动剔除、主动眼动识别等多项功能。

​		项目git仓库地址：[Pumpkinhn/eyetrackProject (github.com)](https://github.com/Pumpkinhn/eyetrackProject)

## 硬件环境

​		本项目使用tobii eyex controller眼动设备，需自行使用磁吸固定在显示器下方。可连接win10、win11系统，通过use3.0接口连接，连接后前往官网下载驱动（[Tobii Gaming | Download or Setup Eye Tracking Software and Drivers](https://gaming.tobii.com/zh/getstarted/)）。下载后即可使用gaze tracking功能。

![](C:\bysj\eyetrackProject\src\图片1.png)

​		如需通过API获取眼动数据，请使用Visual Studio的Package Manager下载官方API——tobii stream engine，下载地址为[NuGet Gallery | Tobii.StreamEngine.Native 2.2.2.363](https://www.nuget.org/packages/Tobii.StreamEngine.Native)。

​		或通过如下命令下载：

```
NuGet\Install-Package Tobii.StreamEngine -Version 2.2.2.363
```

​		下载后会有[API-Reference](.\tobiiAPI\packages\Tobii.StreamEngine.Native.2.2.2.363\content\Tobii\API-Reference.pdf)的pdf文档，可以查看各个API的功能与使用。常用的如tobii_gaze_point_subscribe以获取眼动数据。

## 软件环境

### tobiiAPI

​		TobiiAPI 项目使用Visual Studio 2019创建，安装了 Tobii.StreamEngine 包，通过5001端口进行socket连接。

​		可以调用Debug/tobiiAPI.exe，连接socket后将直接获取眼动数据，并眼动数据保存至./data中。需要提前创建data文件夹。

### eyetracker

​		eyetracker项目使用pycharm创建，Python版本为3.9.16，具体环境已导出至 eyetracker/tobii.yaml ，可通过 conda 创建环境：

```
conda env create -f tobii.yaml
```

## 工程简述

### tobiiAPI

主要代码均在 API.cpp 中实现，包含

- 获取设备情况
- 创建socket连接
  - 默认端口号为5001
- 循环读取眼动数据
  - 默认循环次数为10000次，可通过修改 is_running 变量改变循环次数
  - 循环结束后或终止程序将自动释放
- 回调函数
  - 通过socket发送眼动数据，包含validity、timestamp_us、position_xy
  - 记录到本地的./data文件夹中，文件名形如gaze_data_01.csv，数字递增

### eyetracker

#### main.py

- main.py为主程序，即基于主动注视的外视镜控制系统，但并未接入外视镜控制，仅通过在屏幕上绘制主动注视点位置表示。实现了调取设备API，校正计算，术中主动注视点跟踪，并通过标记的形式展现效果。

- 参数调整：代码中有大量可调整的参数，具体默认值与说明如下：

  ```
  # 重要参数
  max_gap = 8  # 最大间隙长度——可以接受的最大的连续缺失数据的个数，可等效为时间，略小于眨眼
  
  max_vel = 0.0008  # 速度阈值——基于像素的速度阈值
  
  max_dur = 5  # 最大注视间隔——两个相邻注视可被视为同一段注视的最大的时间间隔，等效为时间
  
  max_dis = 50  # 最大注视间距——个相邻注视可被视为同一段注视的最大的距离，单位为像素
  
  min_dur = 40  # 最短注视长度——一段注视可被认定为是主动注视的最短注视时长，等效为时间
  
  size_of_AOI = 30  # 感兴趣区大小——以主动注视点为圆心划定的感兴趣区的半径
  
  v_window = 2  # 窗口平均——速度计算模块的窗口平均降噪的窗口大小
  
  t_window = 2  # 实时窗口——用于实时计算的数据的时间，将每隔2s截存所有数据用于计算注视点
  ```

- 运行过程：

  - 通过 subprocess 调用 tobiiAPI，获取眼动数据。
  - 先进行校正，通过 pygame 依次绘制9点，计算仿射变换矩阵。
  - 通过 pygame 绘制背景，每隔2s截存一段眼动数据用于 gaze_cal() 函数计算主动注视点。
  - 如有主动注视点，更新于屏幕，绘制出注视区域。
  - 如果出现异常，将回报错误内容，并确保关闭 API 避免后台持续运行。

#### correction.py

​		correction.py为校正演示，实现了九点校正-仿射变换校正法，并通过显示采集数据与校正数据展现校正效果。

#### ALG.py

​		ALG.py为术中主动注视点跟踪算法，实现了间隙处理模块、计算分类模块、合并剔除模块。可以读取本地眼动数据记录，进行主动注视点计算，并使用matplotlib绘图以观察模块效果。

#### ./fig

​		fig文件夹中是一些绘图用的程序，用于绘制论文中所展现的示例图像，从而体现算法的效果。

- ori.py 绘制了采集注视和真实注视的位置，展现了误差的情况。
- gap.py 绘制了数据的 validity，展现了间隙的情况。
- gapfill.py 实现了间隙处理模块，绘制了处理后的数据的 validity， 展现了间隙处理模块的效果。
- vt.py 实现了速度计算，绘制了v-t图像，用于观察速度变化，为选择速度阈值提供参考。