import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk, ImageFilter  # 添加 ImageFilter
import os
import time
import sys


# =========================
# 🟢 路径处理（支持打包后的exe）
# =========================
def get_resource_path(relative_path):
    """获取资源文件的绝对路径，支持开发环境和打包后的exe"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# =========================
# 🟢 输入时间
# =========================
try:
    if hasattr(sys, "_MEIPASS"):
        # 图形界面模式
        root_temp = tk.Tk()
        root_temp.withdraw()
        result = simpledialog.askstring(
            "时间设置",
            "请输入久坐时间（分钟，最小为1，最大为1440）：",
            parent=root_temp,
        )
        root_temp.destroy()

        # 用户点击取消或关闭窗口 → 退出程序
        if result is None:
            print("用户取消输入，程序退出")
            sys.exit(0)

        # 验证输入
        try:
            TOTAL_MINUTES = int(result)
            if not (1 <= TOTAL_MINUTES <= 1440):
                messagebox.showerror("输入错误", "请输入1到1440之间的数字！")
                print("输入超出范围，程序退出")
                sys.exit(1)
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字！")
            print("输入无效，程序退出")
            sys.exit(1)

    else:
        # 命令行模式 - 循环直到获得有效输入或用户主动退出
        while True:
            try:
                user_input = input(
                    "请输入久坐时间（分钟，最小为1，最大为1440，输入q退出）："
                )

                # 用户输入q退出
                if user_input.lower() == "q":
                    print("用户退出程序")
                    sys.exit(0)

                TOTAL_MINUTES = int(user_input)
                if 1 <= TOTAL_MINUTES <= 1440:
                    break  # 输入有效，跳出循环
                else:
                    print("输入超出范围（1-1440），请重新输入！")
            except ValueError:
                print("请输入有效的数字！")

except Exception as e:
    print(f"程序发生错误：{e}")
    sys.exit(1)

TOTAL_TIME = TOTAL_MINUTES * 60

# =========================
# 🟢 窗口
# =========================
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)

TRANSPARENT = "#010101"
root.config(bg=TRANSPARENT)
root.wm_attributes("-transparentcolor", TRANSPARENT)

canvas = tk.Canvas(root, bg=TRANSPARENT, highlightthickness=0, bd=0)
canvas.pack()

# =========================
# 🟢 屏幕
# =========================
screen_w = root.winfo_screenwidth()
screen_h = root.winfo_screenheight()

# =========================
# 🟢 状态
# =========================
start_time = time.time()
reminded = False
paused = False
pause_start_time = 0
is_completed = False

dragging = False
offset_x = 0
offset_y = 0

current_x = 0
current_y = screen_h - 260

scale_percent = 40

# 图片缓存
image_cache = {}
current_image_id = None
current_frame_index = 0


# =========================
# 🟢 动画加载和缓存
# =========================
def load_and_cache(folder, scale):
    """加载并缓存图片"""
    cache_key = f"{folder}_{scale}"
    if cache_key in image_cache:
        return image_cache[cache_key]

    folder_path = get_resource_path(folder)

    try:
        files = sorted(os.listdir(folder_path))
    except FileNotFoundError:
        folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder)
        files = sorted(os.listdir(folder_path))

    frames = []
    for f in files:
        img_path = os.path.join(folder_path, f)
        img = Image.open(img_path).convert("RGBA")
        w, h = img.size
        new_w = int(w * scale / 100)
        new_h = int(h * scale / 100)
        scaled_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        photo = ImageTk.PhotoImage(scaled_img)
        frames.append(photo)

    image_cache[cache_key] = frames
    return frames


def get_frames(folder):
    """获取缓存的帧"""
    cache_key = f"{folder}_{scale_percent}"
    if cache_key not in image_cache:
        return load_and_cache(folder, scale_percent)
    return image_cache[cache_key]


def preload_all_frames():
    """预加载所有动画帧"""
    folders = ["phase1", "phase2", "phase3", "phase4", "pause"]
    for folder in folders:
        load_and_cache(folder, scale_percent)


preload_all_frames()


# =========================
# 🟢 阶段
# =========================
def get_phase(t):
    p = t / TOTAL_TIME
    if p < 0.25:
        return "phase1"
    elif p < 0.5:
        return "phase2"
    elif p < 0.75:
        return "phase3"
    return "phase4"


current_folder = "phase1"


def update_frames_by_phase(phase):
    """更新当前动画阶段"""
    global current_folder, current_frame_index
    if current_folder != phase:
        current_folder = phase
        current_frame_index = 0


# =========================
# 🟢 拖动
# =========================
def on_press(event):
    global dragging, offset_x, offset_y
    dragging = True
    offset_x = event.x_root - root.winfo_x()
    offset_y = event.y_root - root.winfo_y()


def on_release(event):
    global dragging, current_x, current_y
    dragging = False
    current_x = root.winfo_x()
    current_y = root.winfo_y()


def on_move(event):
    if not dragging:
        return
    new_y = event.y_root - offset_y
    root.geometry(f"+{int(current_x)}+{int(new_y)}")


canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<ButtonRelease-1>", on_release)
canvas.bind("<B1-Motion>", on_move)


# =========================
# 🟢 右键菜单
# =========================
def toggle_pause():
    global paused, current_frame_index, start_time, pause_start_time, current_folder

    if not paused:
        paused = True
        pause_start_time = time.time()
        current_folder = "pause"
        current_frame_index = 0
    else:
        paused = False
        pause_duration = time.time() - pause_start_time
        start_time += pause_duration

        t = time.time() - start_time
        phase = get_phase(t)
        update_frames_by_phase(phase)


def scale_dialog():
    global scale_percent, current_frame_index, paused, image_cache

    was_paused = paused
    if paused:
        toggle_pause()

    result = simpledialog.askstring("缩放", "请输入缩放百分比 (10-300):", parent=root)
    if result:
        try:
            new_scale = float(result)
            if 10 <= new_scale <= 300:
                scale_percent = new_scale
                image_cache.clear()
                preload_all_frames()

                t = time.time() - start_time
                phase = get_phase(t)
                update_frames_by_phase(phase)

                if was_paused:
                    toggle_pause()
            else:
                messagebox.showwarning("警告", "请输入10-300之间的数字")
        except:
            messagebox.showwarning("警告", "请输入有效数字")


def exit_app():
    root.destroy()


def show_menu(event):
    menu = tk.Menu(root, tearoff=0)
    menu.add_command(label="暂停 / 继续", command=toggle_pause)
    menu.add_command(label="缩放", command=scale_dialog)
    menu.add_command(label="退出", command=exit_app)
    menu.tk_popup(event.x_root, event.y_root)


canvas.bind("<Button-3>", show_menu)


# =========================
# 🟢 动画
# =========================
def animate():
    global current_frame_index, current_image_id, is_completed

    if is_completed:
        root.after(90, animate)
        return

    frames = get_frames(current_folder)

    if frames and len(frames) > 0:
        current_frame_index %= len(frames)
        img = frames[current_frame_index]

        if current_image_id is not None:
            canvas.delete(current_image_id)

        width = img.width()
        height = img.height()

        current_image_id = canvas.create_image(
            width // 2, height // 2, image=img, anchor="center"
        )

        canvas.config(width=width, height=height)
        current_frame_index += 1

    root.after(90, animate)


# =========================
# 🟢 弹窗（修复版 - 背景虚化）
# =========================
def show_popup():
    global is_completed, current_frame_index

    is_completed = True

    # 播放提示音
    try:
        import winsound

        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except:
        pass

    popup = tk.Toplevel(root)
    popup.title("🐶 久坐提醒")
    popup.geometry("420x300")
    popup.attributes("-topmost", True)
    popup.resizable(False, False)

    # 定义退出函数
    def exit_app_from_popup():
        root.destroy()

    # 点击叉叉时退出程序
    popup.protocol("WM_DELETE_WINDOW", exit_app_from_popup)

    # 设置背景为白色
    BG_COLOR = "#FFFFFF"
    popup.config(bg=BG_COLOR)

    # 居中显示
    popup.update_idletasks()
    width = popup.winfo_width()
    height = popup.winfo_height()
    x = (popup.winfo_screenwidth() // 2) - (width // 2)
    y = (popup.winfo_screenheight() // 2) - (height // 2)
    popup.geometry(f"+{x}+{y}")

    # 定义重启函数
    def restart():
        global start_time, reminded, current_x, current_y, is_completed, current_frame_index
        start_time = time.time()
        reminded = False
        is_completed = False
        current_x = 0
        current_y = screen_h - 260
        root.geometry(f"+{current_x}+{current_y}")
        current_frame_index = 0
        popup.destroy()

    # 🖼️ 尝试加载背景图片
    try:
        # 加载图片
        bg_image_path = get_resource_path("bg.jpeg")
        bg_image = Image.open(bg_image_path)

        # 背景模糊
        blur_radius = 15
        bg_image_blurred = bg_image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        # 处理正方形图片
        target_width = 420
        target_height = 300

        orig_width, orig_height = bg_image_blurred.size

        scale_w = target_width / orig_width
        scale_h = target_height / orig_height
        scale = min(scale_w, scale_h)

        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        bg_image_resized = bg_image_blurred.resize(
            (new_width, new_height), Image.Resampling.LANCZOS
        )

        # 背景色为白色
        bg_color = (255, 255, 255)
        final_image = Image.new("RGB", (target_width, target_height), bg_color)

        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2

        final_image.paste(bg_image_resized, (x_offset, y_offset))

        bg_photo = ImageTk.PhotoImage(final_image)

        # 使用Canvas显示背景
        canvas_bg = tk.Canvas(
            popup, width=420, height=300, highlightthickness=0, bg="#FFFFFF"
        )
        canvas_bg.pack(fill=tk.BOTH, expand=True)
        canvas_bg.create_image(0, 0, image=bg_photo, anchor="nw")
        canvas_bg.image = bg_photo

        # 标题文字
        canvas_bg.create_text(
            210,
            25,
            text="⏰ 该起来活动一下啦！",
            font=("Microsoft YaHei", 18, "bold"),
            fill="#FF6B6B",
        )

        # 提示文字
        canvas_bg.create_text(
            210,
            105,
            text="你已经坐了很长时间了\n站起来走动一下吧 🚶",
            font=("Microsoft YaHei", 12),
            fill="#333333",
            justify="center",
        )

        # 🎨 按钮 - 直接放在Canvas上，背景透明
        # 创建"好的"按钮（透明背景）
        btn_ok = tk.Button(
            popup,
            text="✔ 好的，去活动",
            command=restart,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            relief="flat",
            bd=0,
            highlightthickness=0,
            activebackground="#45a049",  # 点击时的背景色
            activeforeground="white",
        )
        btn_ok.place(x=85, y=195, width=145, height=40)

        # 悬停效果
        def on_enter_ok(e):
            btn_ok.config(bg="#45a049")

        def on_leave_ok(e):
            btn_ok.config(bg="#4CAF50")

        btn_ok.bind("<Enter>", on_enter_ok)
        btn_ok.bind("<Leave>", on_leave_ok)

        # 创建"退出"按钮（透明背景）
        btn_exit = tk.Button(
            popup,
            text="✖ 退出",
            command=exit_app_from_popup,
            bg="#f44336",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            relief="flat",
            bd=0,
            highlightthickness=0,
            activebackground="#da190b",  # 点击时的背景色
            activeforeground="white",
        )
        btn_exit.place(x=240, y=195, width=100, height=40)

        # 悬停效果
        def on_enter_exit(e):
            btn_exit.config(bg="#da190b")

        def on_leave_exit(e):
            btn_exit.config(bg="#f44336")

        btn_exit.bind("<Enter>", on_enter_exit)
        btn_exit.bind("<Leave>", on_leave_exit)

        # 底部提示（使用Canvas绘制，透明背景）
        canvas_bg.create_text(
            210,
            275,
            text='💡 点击"好的"重新计时',
            font=("Microsoft YaHei", 9),
            fill="#999999",
        )

        btn_ok.focus_set()

    except Exception as e:
        # 如果图片加载失败，使用纯白色背景
        print(f"背景图片加载失败: {e}")
        print("使用默认纯白色背景")

        popup.config(bg="#FFFFFF")

        # 创建主框架
        main_frame = tk.Frame(popup, bg="#FFFFFF")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        title_label = tk.Label(
            main_frame,
            text="⏰ 该起来活动一下啦！",
            font=("Microsoft YaHei", 16, "bold"),
            fg="#FF6B6B",
            bg="#FFFFFF",
        )
        title_label.pack(pady=(0, 10))

        # 提示文字
        desc_label = tk.Label(
            main_frame,
            text="你已经坐了很长时间了\n站起来走动一下吧 🚶",
            font=("Microsoft YaHei", 11),
            fg="#333333",
            bg="#FFFFFF",
            justify="center",
        )
        desc_label.pack(pady=(0, 15))

        # 装饰线
        separator = tk.Frame(main_frame, height=2, bg="#FFD700")
        separator.pack(fill=tk.X, pady=(5, 15))

        # 按钮框架
        btn_frame = tk.Frame(main_frame, bg="#FFFFFF")
        btn_frame.pack(pady=(0, 10))

        # 按钮
        btn_ok = tk.Button(
            btn_frame,
            text="✔ 好的，去活动",
            command=restart,
            bg="#4CAF50",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        btn_ok.pack(side=tk.LEFT, padx=5)

        # 悬停效果
        def on_enter_ok(e):
            btn_ok.config(bg="#45a049")

        def on_leave_ok(e):
            btn_ok.config(bg="#4CAF50")

        btn_ok.bind("<Enter>", on_enter_ok)
        btn_ok.bind("<Leave>", on_leave_ok)

        btn_exit = tk.Button(
            btn_frame,
            text="✖ 退出程序",
            command=exit_app_from_popup,
            bg="#f44336",
            fg="white",
            font=("Microsoft YaHei", 10, "bold"),
            padx=20,
            pady=8,
            cursor="hand2",
            relief="flat",
            bd=0,
            highlightthickness=0,
        )
        btn_exit.pack(side=tk.LEFT, padx=5)

        # 悬停效果
        def on_enter_exit(e):
            btn_exit.config(bg="#da190b")

        def on_leave_exit(e):
            btn_exit.config(bg="#f44336")

        btn_exit.bind("<Enter>", on_enter_exit)
        btn_exit.bind("<Leave>", on_leave_exit)

        # 底部提示
        tip_label = tk.Label(
            main_frame,
            text='💡 点击"好的"重新计时',
            font=("Microsoft YaHei", 9),
            fg="#999999",
            bg="#FFFFFF",
        )
        tip_label.pack()

        btn_ok.focus_set()


# =========================
# 🟢 主循环
# =========================
def update():
    global current_x, current_y, reminded, is_completed

    if not paused and not is_completed:
        t = time.time() - start_time
        progress = min(t / TOTAL_TIME, 1.0)

        phase = get_phase(t)
        update_frames_by_phase(phase)

        new_x = int(progress * (screen_w - 120))

        if not dragging:
            current_x = new_x
            if current_y is None or current_y == 0:
                current_y = screen_h - 260
            root.geometry(f"+{int(current_x)}+{int(current_y)}")

        if progress >= 1.0 and not reminded:
            reminded = True
            show_popup()
    elif is_completed:
        pass

    root.after(100, update)


# =========================
# 🟢 启动
# =========================
root.geometry(f"+{current_x}+{current_y}")

animate()
update()
root.mainloop()
