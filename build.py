import os
import subprocess
import sys

# 项目根目录
project_root = os.path.dirname(os.path.abspath(__file__))

# 入口脚本
entry_script = 'main.py'

# 可执行文件名称
executable_name = 'TimingAndPointsSystem'

# .spec 文件路径
spec_file = f'{executable_name}.spec'

# 删除旧的 .spec 文件
if os.path.exists(spec_file):
    os.remove(spec_file)

# 生成 .spec 文件
subprocess.run([sys.executable, '-m', 'PyInstaller', '--onefile', '--name', executable_name, entry_script])

# 修改 .spec 文件
with open(spec_file, 'r', encoding='utf-8') as file:
    spec_content = file.readlines()

# 查找 Analysis 部分并插入新的参数
for i, line in enumerate(spec_content):
    if line.startswith('a = Analysis('):
        # 移除旧的重复参数
        while not line.strip().endswith('],'):
            i += 1
            line = spec_content[i]
        i += 1
        # 插入新的参数
        spec_content.insert(i, "    pathex=[],\n")
        spec_content.insert(i + 1, "    binaries=[],\n")
        spec_content.insert(i + 2, "    datas=[('app/templates', 'app/templates'), ('app/static', 'app/static')],\n")
        spec_content.insert(i + 3, "    hiddenimports=[],\n")
        spec_content.insert(i + 4, "    hookspath=[],\n")
        spec_content.insert(i + 5, "    hooksconfig={},\n")
        spec_content.insert(i + 6, "    runtime_hooks=[],\n")
        spec_content.insert(i + 7, "    excludes=['instance', 'backups'],\n")
        spec_content.insert(i + 8, "    noarchive=False,\n")
        spec_content.insert(i + 9, "    optimize=0,\n")  # 添加逗号
        break

# 确保 datas 参数存在且正确
datas_found = False
for i, line in enumerate(spec_content):
    if line.strip().startswith('datas='):
        datas_found = True
        spec_content[i] = "    datas=[('app/templates', 'app/templates'), ('app/static', 'app/static')],\n"
        break

if not datas_found:
    for i, line in enumerate(spec_content):
        if line.startswith('a = Analysis('):
            while not line.strip().endswith('],'):
                i += 1
                line = spec_content[i]
            i += 1
            spec_content.insert(i + 2, "    datas=[('app/templates', 'app/templates'), ('app/static', 'app/static')],\n")
            break

# 移除重复的参数定义
spec_content = [line for line in spec_content if not line.strip().startswith(('pathex=', 'binaries=', 'datas=', 'hiddenimports=', 'hookspath=', 'hooksconfig=', 'runtime_hooks=', 'excludes=', 'noarchive=', 'optimize='))]

with open(spec_file, 'w', encoding='utf-8') as file:
    file.writelines(spec_content)

# 运行 PyInstaller 打包
subprocess.run([sys.executable, '-m', 'PyInstaller', spec_file])