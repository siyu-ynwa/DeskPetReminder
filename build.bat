@echo off
chcp 65001 >nul
echo ====================================
echo 久坐提醒程序打包工具
echo ====================================
echo.

echo 检查必要文件...
if exist bg.jpeg (
    echo ✅ 找到背景图片: bg.jpeg
    set BG_ARG=--add-data=bg.jpeg;.
) else (
    echo ⚠️ 未找到背景图片，将不包含
    set BG_ARG=
)

if exist dog.ico (
    echo ✅ 找到图标文件: dog.ico
    set ICON_ARG=--icon=dog.ico
) else (
    echo ⚠️ 未找到图标文件，将使用默认图标
    set ICON_ARG=
)

echo.
echo 开始打包...
python -m PyInstaller -F -w --name=久坐提醒 %ICON_ARG% --add-data phase1;phase1 --add-data phase2;phase2 --add-data phase3;phase3 --add-data phase4;phase4 --add-data pause;pause %BG_ARG% --hidden-import PIL --hidden-import PIL._imaging --hidden-import PIL.ImageFilter --hidden-import tkinter main.py

echo.
if exist "dist\久坐提醒.exe" (
    echo ✅ 打包成功！
    echo 文件位置: dist\久坐提醒.exe
    echo.
    echo 文件大小:
    dir "dist\久坐提醒.exe" | find "久坐提醒.exe"
) else (
    echo ❌ 打包失败
)

pause