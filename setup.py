from cx_Freeze import setup, Executable
import os
from setuptools import find_packages
# # 设置环境变量
# os.environ['TCL_LIBRARY'] = r'C:\path\to\tcl\tcl8.6'
# os.environ['TK_LIBRARY'] = r'C:\path\to\tcl\tk8.6'

# 添加需要包含的文件和文件夹
include_files = [
]

# 设置可执行文件
executables = [
    Executable('main.py', base=None)
]

# 设置打包选项
options = {
    'build_exe': {
        'packages': ['flask', 'sqlalchemy', 'threading', 'webbrowser','apscheduler'],
        'include_files': include_files,
    },
}

# 设置打包配置
setup(
    name='TimingAndCountingSystem',
    version='0.1',
    description='一个计时记分的管理系统',
    options=options,
    executables=executables
)