import tkinter as tk
from tkinter import ttk, filedialog, messagebox, Label
import cv2
import threading
import queue
from PIL import Image, ImageTk
import random
import os


class BirthdayWisherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("生日快乐祝福程序 (最终完整版)")
        self.geometry("1200x800")
        self.minsize(800, 600)

        # --- 核心路径与资源 ---
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.media_dir = os.path.join(self.app_dir, "media")
        self.video_path = os.path.join(self.media_dir, "birthday_video.mp4")
        self.image_paths = self._get_image_files()
        self.wishes = self._load_wishes()

        # --- 视频播放相关变量 ---
        self.cap = None
        self.is_playing = False
        self.video_thread = None
        self.current_frame = None
        self.delay = 33
        self.frame_queue = queue.Queue(maxsize=10)

        # --- UI组件变量 ---
        self.video_label = None
        self.progress_var = None

        # --- 创建界面 ---
        self.create_widgets()
        # 延迟加载缩略图，确保video_label已渲染
        self.after(100, self.load_video_thumbnail)

    def _get_image_files(self):
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')
        if not os.path.exists(self.media_dir):
            try:
                os.makedirs(self.media_dir)
            except OSError as e:
                messagebox.showwarning("警告", f"无法创建媒体文件夹: {e}")
        try:
            return sorted([os.path.join(self.media_dir, f) for f in os.listdir(self.media_dir) if
                           f.lower().endswith(image_extensions)])
        except OSError as e:
            messagebox.showwarning("警告", f"无法访问媒体文件夹: {e}")
            return []

    def _load_wishes(self):
        wishes_path = os.path.join(self.media_dir, "wishes.txt")
        default_wishes = ["生日快乐！愿所有美好都如期而至！", "祝你今天像公主一样闪耀！", "新的一岁，暴富暴美！",
                          "愿你的每一天都充满阳光和欢笑！"]
        try:
            with open(wishes_path, 'r', encoding='utf-8') as f:
                wishes = [line.strip() for line in f if line.strip()]
            return wishes if wishes else default_wishes
        except FileNotFoundError:
            try:
                with open(wishes_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(default_wishes))
            except OSError as e:
                messagebox.showwarning("警告", f"无法创建祝福文件: {e}")
            return default_wishes
        except OSError as e:
            messagebox.showwarning("警告", f"无法读取祝福文件: {e}")
            return default_wishes

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- 视频播放区域 ---
        video_frame = ttk.LabelFrame(main_frame, text="生日视频", padding="10")
        video_frame.pack(expand=True, fill=tk.BOTH, pady=10)
        # 视频标签用tk.Label（支持bg属性）
        self.video_label = tk.Label(video_frame, text="正在准备视频...", bg="black", fg="white", font=("Arial", 16))
        self.video_label.pack(expand=True, fill=tk.BOTH)

        video_controls = ttk.Frame(video_frame)
        video_controls.pack(fill=tk.X, pady=5)
        self.play_video_btn = ttk.Button(video_controls, text="播放视频", command=self.toggle_video_play)
        self.play_video_btn.pack(side=tk.LEFT, padx=5)
        self.stop_video_btn = ttk.Button(video_controls, text="停止视频", command=self.stop_video, state=tk.DISABLED)
        self.stop_video_btn.pack(side=tk.LEFT, padx=5)
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(video_controls, variable=self.progress_var, mode='determinate')
        progress_bar.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # --- 互动按钮区域 ---
        interaction_frame = ttk.Frame(main_frame)
        interaction_frame.pack(fill=tk.X, pady=20)
        self.show_pic_btn = ttk.Button(interaction_frame, text="点击查看生日图片", command=self.open_image_browser)
        self.show_pic_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        self.show_wish_btn = ttk.Button(interaction_frame, text="点击获取生日祝福", command=self.show_random_wish)
        self.show_wish_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)

    # --- 视频播放相关方法 ---
    def load_video_thumbnail(self):
        if not os.path.exists(self.video_path):
            self.video_label.config(text="未找到视频文件 (birthday_video.mp4)", fg="red")
            return

        cap = None
        try:
            cap = cv2.VideoCapture(self.video_path)
            if not cap.isOpened():
                self.video_label.config(text="无法打开视频文件", fg="red")
                return

            ret, frame = cap.read()
            if ret:
                self._display_frame(frame)
            else:
                self.video_label.config(text="视频文件损坏或为空", fg="red")
        except Exception as e:
            self.video_label.config(text=f"加载视频出错: {str(e)[:50]}...", fg="red")
        finally:
            if cap:
                cap.release()

    def _display_frame(self, frame):
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w = frame_rgb.shape[:2]

            # 确保获取到有效尺寸
            label_w = self.video_label.winfo_width()
            label_h = self.video_label.winfo_height()
            if label_w <= 1 or label_h <= 1:
                label_w = self.winfo_width() - 80  # 减去padding和边框
                label_h = self.winfo_height() // 2 - 40

            # 计算缩放比例，确保不小于1
            scale = min(label_w / w, label_h / h)
            scale = max(scale, 0.1)  # 最小缩放比例

            new_w, new_h = int(w * scale), int(h * scale)
            new_w = max(new_w, 100)  # 确保宽度至少100
            new_h = max(new_h, 100)  # 确保高度至少100

            resized_frame = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
            image = Image.fromarray(resized_frame)
            self.current_frame = ImageTk.PhotoImage(image=image)
            self.video_label.config(image=self.current_frame, text="")
        except Exception as e:
            print(f"显示视频帧出错: {e}")
            self.video_label.config(text="视频帧显示失败", fg="red")

    def toggle_video_play(self):
        if not self.cap:
            self.start_video()
        else:
            self.is_playing = not self.is_playing
            if self.is_playing:
                self.play_video_btn.config(text="暂停")
                self._update_ui_with_frame()
            else:
                self.play_video_btn.config(text="继续")

    def start_video(self):
        if not os.path.exists(self.video_path):
            messagebox.showerror("错误", f"视频文件未找到: {self.video_path}")
            return

        self.stop_video()  # 先停止之前的视频

        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                raise ValueError("无法打开视频文件")

            self.is_playing = True
            self.play_video_btn.config(text="暂停")
            self.stop_video_btn.config(state=tk.NORMAL)

            fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.delay = int(1000 / fps) if fps > 0 else 33

            self.video_thread = threading.Thread(target=self._video_read_loop, daemon=True)
            self.video_thread.start()
            self._update_ui_with_frame()
        except Exception as e:
            messagebox.showerror("错误", f"启动视频失败: {e}")
            self.cap = None

    def _video_read_loop(self):
        while self.is_playing and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret:
                    break

                frame = self._resize_frame_for_queue(frame)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                try:
                    self.frame_queue.put(frame_rgb, timeout=0.1)
                except queue.Full:
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(frame_rgb)
                    except:
                        pass
            except Exception as e:
                print(f"读取视频帧出错: {e}")
                break

        self.is_playing = False
        self.after(0, self.stop_video)

    def _resize_frame_for_queue(self, frame):
        # 为队列中的帧使用固定尺寸，减少内存占用
        h, w = frame.shape[:2]
        max_size = 800
        if w > max_size or h > max_size:
            scale = max_size / max(w, h)
            new_w, new_h = int(w * scale), int(h * scale)
            return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        return frame

    def _update_ui_with_frame(self):
        if not self.is_playing or not self.cap.isOpened():
            return

        try:
            frame_rgb = self.frame_queue.get_nowait()
            image = Image.fromarray(frame_rgb)

            # 再次缩放以匹配标签大小
            label_w, label_h = self.video_label.winfo_width(), self.video_label.winfo_height()
            if label_w > 50 and label_h > 50:
                image.thumbnail((label_w - 10, label_h - 10), Image.Resampling.LANCZOS)

            self.current_frame = ImageTk.PhotoImage(image=image)
            self.video_label.config(image=self.current_frame, text="")

            # 更新进度条
            current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if total_frames > 0:
                self.progress_var.set((current_pos / total_frames) * 100)

            self.after(self.delay, self._update_ui_with_frame)
        except queue.Empty:
            self.after(10, self._update_ui_with_frame)
        except Exception as e:
            print(f"更新UI出错: {e}")
            self.is_playing = False
            self.after(0, self.stop_video)

    def stop_video(self):
        self.is_playing = False
        if self.video_thread and self.video_thread.is_alive():
            try:
                self.video_thread.join(timeout=1.0)
            except:
                pass

        if self.cap:
            self.cap.release()
        self.cap = None

        self.play_video_btn.config(text="播放视频")
        self.stop_video_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.load_video_thumbnail()

    # --- 图片浏览器相关方法 ---
    def open_image_browser(self):
        if not self.image_paths:
            messagebox.showinfo("提示", "媒体文件夹中没有找到任何图片。")
            return
        # 创建图片浏览器实例
        self.browser = ImageBrowser(self, self.image_paths)

    # --- 生日祝福相关方法 ---
    def show_random_wish(self):
        if not self.wishes:
            messagebox.showerror("错误", "没有找到任何祝福语句。")
            return
        selected_wish = random.choice(self.wishes)
        wish_window = tk.Toplevel(self)
        wish_window.title("生日祝福")
        wish_window.geometry("650x350")
        wish_window.configure(bg="#fefbd8")

        # 祝福标签用tk.Label（支持bg/fg属性）
        wish_label = tk.Label(wish_window, text=selected_wish, font=("Microsoft YaHei", 28, "bold"),
                              fg="#d32f2f", bg="#fefbd8", wraplength=600, justify=tk.CENTER, padx=30, pady=50)
        wish_label.pack(expand=True, fill=tk.BOTH)

        ttk.Button(wish_window, text="关闭", command=wish_window.destroy).pack(pady=10)


# ==============================================================================
# --- 图片浏览器类（优化：按钮显示、键盘切换、关闭逻辑） ---
# ==============================================================================
class ImageBrowser(tk.Toplevel):
    def __init__(self, master, image_paths):
        super().__init__(master)
        self.title("生日图片浏览器")
        self.geometry("1000x800")
        self.image_paths = image_paths
        self.current_image_index = -1
        self.thumbnails = []  # 存储缩略图的PhotoImage对象
        self.current_photo = None  # 存储当前大图的PhotoImage对象

        # 主容器
        self.main_container = ttk.Frame(self)
        self.main_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 两个界面：缩略图墙 + 大图查看
        self.thumbnail_frame = ttk.Frame(self.main_container)
        self.viewer_frame = ttk.Frame(self.main_container)

        # 绑定窗口关闭事件（区分大图/缩略图模式）
        self.protocol("WM_DELETE_WINDOW", self.handle_window_close)

        # 初始化缩略图界面
        self.create_thumbnail_view()

    def handle_window_close(self):
        """处理窗口右上角关闭按钮：大图模式返回缩略图，缩略图模式关闭窗口"""
        if self.viewer_frame.winfo_ismapped():  # 当前是大图模式
            self.return_to_thumbnails()
        else:  # 当前是缩略图模式
            self.destroy()

    def create_thumbnail_view(self):
        """创建可滚动的缩略图墙"""
        # 清空旧内容
        for widget in self.thumbnail_frame.winfo_children():
            widget.destroy()
        self.thumbnails.clear()

        # 滚动组件
        canvas = tk.Canvas(self.thumbnail_frame)
        scrollbar = ttk.Scrollbar(self.thumbnail_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 显示缩略图界面，隐藏大图界面
        self.thumbnail_frame.pack(expand=True, fill=tk.BOTH)
        self.viewer_frame.pack_forget()

        # 排列缩略图（4列）
        num_cols = 4
        for i, path in enumerate(self.image_paths):
            try:
                img = Image.open(path)
                img.thumbnail((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.thumbnails.append(photo)

                # 缩略图按钮（点击打开大图）
                btn = ttk.Button(scrollable_frame, image=photo, command=lambda idx=i: self.show_image_viewer(idx))
                btn.image = photo
                btn.grid(row=i // num_cols, column=i % num_cols, padx=5, pady=5, sticky="nsew")
            except Exception as e:
                print(f"加载缩略图出错: {path} - {e}")
                # 出错时显示文字按钮
                btn = ttk.Button(scrollable_frame, text="加载失败", command=lambda idx=i: self.show_image_viewer(idx))
                btn.grid(row=i // num_cols, column=i % num_cols, padx=5, pady=5, sticky="nsew")

        # 让缩略图按钮大小均匀
        for i in range(num_cols):
            scrollable_frame.grid_columnconfigure(i, weight=1)

    def show_image_viewer(self, index):
        """切换到大图查看模式（优化：显示< >按钮、绑定键盘切换）"""
        if not (0 <= index < len(self.image_paths)):
            messagebox.showerror("错误", "无效的图片索引。")
            return

        self.current_image_index = index

        # 清空旧内容
        for widget in self.viewer_frame.winfo_children():
            widget.destroy()

        # 大图显示标签（tk.Label支持背景色）
        self.image_label = tk.Label(self.viewer_frame, bg="black")

        # 控制按钮（显示< >符号）
        control_frame = ttk.Frame(self.viewer_frame)
        # 上一张按钮（显示<）
        prev_btn = ttk.Button(control_frame, text="< 上一张", command=self.show_previous_image)
        # 关闭按钮（返回缩略图）
        close_btn = ttk.Button(control_frame, text="关闭", command=self.return_to_thumbnails)
        # 下一张按钮（显示>）
        next_btn = ttk.Button(control_frame, text="下一张 >", command=self.show_next_image)

        # 布局按钮（确保< >显示）
        prev_btn.pack(side="left", expand=True, fill="x", padx=2)
        close_btn.pack(side="left", expand=True, fill="x", padx=2)
        next_btn.pack(side="left", expand=True, fill="x", padx=2)

        # 布局大图和控制区
        self.image_label.pack(expand=True, fill=tk.BOTH, pady=10)
        control_frame.pack(fill="x", pady=5)

        # 显示大图界面，隐藏缩略图界面
        self.viewer_frame.pack(expand=True, fill=tk.BOTH)
        self.thumbnail_frame.pack_forget()

        # 绑定键盘左右键切换
        self.viewer_frame.bind("<Left>", lambda e: self.show_previous_image())
        self.viewer_frame.bind("<Right>", lambda e: self.show_next_image())
        # 确保大图界面获得焦点，接收键盘事件
        self.viewer_frame.focus_set()

        # 加载并显示当前大图
        self.update_image_display()

    def update_image_display(self):
        """更新大图显示"""
        path = self.image_paths[self.current_image_index]
        try:
            img = Image.open(path)

            # 获取显示区域尺寸
            label_w, label_h = self.image_label.winfo_width(), self.image_label.winfo_height()
            if label_w <= 1 or label_h <= 1:
                label_w, label_h = self.winfo_width() - 40, self.winfo_height() - 80

            # 保持宽高比缩放（避免拉伸）
            img.thumbnail((label_w, label_h), Image.Resampling.LANCZOS)
            self.current_photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.current_photo, text="")

            # 更新窗口标题（显示图片序号）
            self.title(f"查看图片 ({self.current_image_index + 1}/{len(self.image_paths)}) - {os.path.basename(path)}")
        except Exception as e:
            error_msg = f"无法加载图片: {os.path.basename(path)}\n错误: {str(e)[:50]}..."
            print(error_msg)
            self.image_label.config(text=error_msg, fg="red", bg="black", wraplength=500)
            self.title(f"图片加载失败 - {os.path.basename(path)}")

    def show_previous_image(self):
        """切换到上一张图片（支持键盘左键）"""
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.update_image_display()
        else:
            messagebox.showinfo("提示", "已经是第一张图片了。")

    def show_next_image(self):
        """切换到下一张图片（支持键盘右键）"""
        if self.current_image_index < len(self.image_paths) - 1:
            self.current_image_index += 1
            self.update_image_display()
        else:
            messagebox.showinfo("提示", "已经是最后一张图片了。")

    def return_to_thumbnails(self):
        """从大图模式返回缩略图墙（优化：解除键盘绑定）"""
        # 解除键盘左右键绑定
        self.viewer_frame.unbind("<Left>")
        self.viewer_frame.unbind("<Right>")

        # 显示缩略图界面，隐藏大图界面
        self.thumbnail_frame.pack(expand=True, fill=tk.BOTH)
        self.viewer_frame.pack_forget()

        # 恢复窗口标题
        self.title("生日图片浏览器")

    def destroy(self):
        """关闭窗口时释放资源"""
        self.thumbnails.clear()
        self.current_photo = None
        super().destroy()


if __name__ == "__main__":
    app = BirthdayWisherApp()
    app.mainloop()