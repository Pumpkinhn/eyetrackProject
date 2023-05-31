# eyetrackProject

## tobiiAPI

- 此为调取tobii eyeX tracker设备API的c++程序，将眼动数据记录至本地并通过socket发送给数据处理程序。
- 包含Tobii.StreamEngine.Native.2.2.2.363官方API，内含API-Reference
- Debug/tobiiAPI.exe 为应用程序，目录中已有动态链接库，可直接运行，可直接调取。

## eyetracker

- 此为处理眼动数据的Python程序，包含术中主动注视点跟踪算法、基于主动注视的外视镜控制系统与相关测试用代码。
- 所需环境已导出至tobii.yaml，使用conda安装即可。
- main.py为主程序，即基于主动注视的外视镜控制系统，实现了调取设备API，校正计算，术中主动注视点跟踪，并通过标记的形式展现效果。
- correction.py为校正模块，实现了九点校正-仿射变换校正法，并通过显示采集数据与校正数据展现校正效果。
- ALG.py为术中主动注视点跟踪算法，实现了间隙处理模块、计算分类模块、合并剔除模块，并使用matplotlib绘图以观察模块效果。
- API获取的眼动数据都会以csv文件形式存入data文件夹，可以用于后期数据处理，参数调整等。
- fig文件夹中是一些绘图用的程序，用于绘制论文中所展现的示例图像，从而体现算法的效果。

