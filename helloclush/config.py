# 配置文件

# 系统配置
APPLICATION = "HelloClush"
VERSION = "0.1.0"
PYTHON_VER = "3.6.8"
DEPENDS = ["ClusterShell", "tornado"]

# 应用配置

import os

# 应用目录
APPDIR = "/home/kilin/workspace/helloworld-v0.2/"
STATICDIR = APPDIR + "static/"
CUSTOMDIR = APPDIR + "customizations/"
WAREDIR = APPDIR + "warehouse/"

GROUPS_CONFIG = APPDIR + "groups.conf"