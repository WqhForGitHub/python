# -*- coding: utf-8 -*-
"""
GUI 图片查看器
- 纯 Python 实现，仅依赖标准库（tkinter）
- 功能：
    1. 打开单张图片 / 打开文件夹（自动加载文件夹内所有图片）
    2. 上一张 / 下一张
    3. 放大 / 缩小 / 还原 / 适应窗口
    4. 状态栏显示文件名、序号、原始尺寸、当前缩放
    5. 快捷键支持

由于 tkinter 内置 PhotoImage 仅原生支持 GIF / PNG / PGM / PPM，
本 Demo 不依赖 Pillow，所以只支持 .png / .gif / .pgm / .ppm 格式。
"""
import os
import tkinter as tk
from tkinter import filedialog, messagebox


SUPPORTED_EXTS = (".png", ".gif", ".pgm", ".ppm")


class ImageViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("图片查看器 - 未打开")
        self.geometry("900x650")
        self.minsize(500, 400)

        # 状态
        self.image_list = []     # 当前目录下的图片路径列表
        self.index = -1          # 当前显示图片索引
        self.original_image = None   # 原始 PhotoImage
        self.display_image = None    # 当前显示用的 PhotoImage（缩放后）
        self.zoom_factor = 1.0       # 当前缩放因子（>1 放大，<1 缩小）
        # tkinter PhotoImage 的 zoom/subsample 只接受整数，所以用整数表示
        self.zoom_num = 1            # 放大倍数
        self.sub_num = 1             # 缩小倍数

        self._build_menu()
        self._build_toolbar()
        self._build_canvas()
        self._build_status()
        self._bind_keys()

    # ---------- UI ----------
    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="打开图片...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="打开文件夹...", accelerator="Ctrl+D", command=self.open_dir)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.destroy)
        menubar.add_cascade(label="文件", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="上一张", accelerator="←", command=self.prev_image)
        view_menu.add_command(label="下一张", accelerator="→", command=self.next_image)
        view_menu.add_separator()
        view_menu.add_command(label="放大", accelerator="+", command=self.zoom_in)
        view_menu.add_command(label="缩小", accelerator="-", command=self.zoom_out)
        view_menu.add_command(label="原始大小", accelerator="0", command=self.zoom_reset)
        view_menu.add_command(label="适应窗口", accelerator="F", command=self.fit_window)
        menubar.add_cascade(label="查看", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(
            label="关于",
            command=lambda: messagebox.showinfo(
                "关于",
                "纯 Python (tkinter) 图片查看器 Demo\n支持格式：PNG / GIF / PGM / PPM",
            ),
        )
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.config(menu=menubar)

    def _build_toolbar(self):
        bar = tk.Frame(self, bd=1, relief="raised")
        bar.pack(side="top", fill="x")

        tk.Button(bar, text="打开", width=8, command=self.open_file).pack(side="left", padx=2, pady=2)
        tk.Button(bar, text="文件夹", width=8, command=self.open_dir).pack(side="left", padx=2, pady=2)
        tk.Frame(bar, width=2, bg="gray").pack(side="left", fill="y", padx=4)

        tk.Button(bar, text="◀ 上一张", width=10, command=self.prev_image).pack(side="left", padx=2, pady=2)
        tk.Button(bar, text="下一张 ▶", width=10, command=self.next_image).pack(side="left", padx=2, pady=2)
        tk.Frame(bar, width=2, bg="gray").pack(side="left", fill="y", padx=4)

        tk.Button(bar, text="＋ 放大", width=8, command=self.zoom_in).pack(side="left", padx=2, pady=2)
        tk.Button(bar, text="－ 缩小", width=8, command=self.zoom_out).pack(side="left", padx=2, pady=2)
        tk.Button(bar, text="原始", width=6, command=self.zoom_reset).pack(side="left", padx=2, pady=2)
        tk.Button(bar, text="适应窗口", width=8, command=self.fit_window).pack(side="left", padx=2, pady=2)

    def _build_canvas(self):
        frame = tk.Frame(self, bg="#222")
        frame.pack(fill="both", expand=True)

        self.h_scroll = tk.Scrollbar(frame, orient="horizontal")
        self.h_scroll.pack(side="bottom", fill="x")
        self.v_scroll = tk.Scrollbar(frame, orient="vertical")
        self.v_scroll.pack(side="right", fill="y")

        self.canvas = tk.Canvas(
            frame,
            bg="#222",
            highlightthickness=0,
            xscrollcommand=self.h_scroll.set,
            yscrollcommand=self.v_scroll.set,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)

        self.image_id = None
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_status(self):
        self.status = tk.Label(self, text="就绪", anchor="w", bd=1, relief="sunken")
        self.status.pack(side="bottom", fill="x")

    def _bind_keys(self):
        self.bind_all("<Control-o>", lambda e: self.open_file())
        self.bind_all("<Control-d>", lambda e: self.open_dir())
        self.bind_all("<Left>", lambda e: self.prev_image())
        self.bind_all("<Right>", lambda e: self.next_image())
        self.bind_all("<plus>", lambda e: self.zoom_in())
        self.bind_all("<KP_Add>", lambda e: self.zoom_in())
        self.bind_all("=", lambda e: self.zoom_in())
        self.bind_all("<minus>", lambda e: self.zoom_out())
        self.bind_all("<KP_Subtract>", lambda e: self.zoom_out())
        self.bind_all("0", lambda e: self.zoom_reset())
        self.bind_all("f", lambda e: self.fit_window())
        self.bind_all("F", lambda e: self.fit_window())

    # ---------- 文件操作 ----------
    def open_file(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[
                ("图片文件", "*.png *.gif *.pgm *.ppm"),
                ("PNG", "*.png"),
                ("GIF", "*.gif"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        directory = os.path.dirname(path)
        self._load_dir(directory)
        try:
            self.index = self.image_list.index(os.path.abspath(path))
        except ValueError:
            self.image_list = [os.path.abspath(path)]
            self.index = 0
        self._show_current()

    def open_dir(self):
        directory = filedialog.askdirectory(title="选择图片文件夹")
        if not directory:
            return
        self._load_dir(directory)
        if not self.image_list:
            messagebox.showinfo("提示", "该文件夹下没有受支持格式的图片。")
            return
        self.index = 0
        self._show_current()

    def _load_dir(self, directory):
        files = []
        try:
            for name in sorted(os.listdir(directory)):
                if name.lower().endswith(SUPPORTED_EXTS):
                    files.append(os.path.abspath(os.path.join(directory, name)))
        except OSError as e:
            messagebox.showerror("读取失败", str(e))
        self.image_list = files

    # ---------- 图片显示 ----------
    def _show_current(self):
        if not self.image_list or self.index < 0:
            return
        path = self.image_list[self.index]
        try:
            self.original_image = tk.PhotoImage(file=path)
        except tk.TclError as e:
            messagebox.showerror("加载失败", f"无法加载图片：\n{path}\n\n{e}")
            return
        self.zoom_num = 1
        self.sub_num = 1
        self._refresh_display()
        self.title(f"图片查看器 - {os.path.basename(path)}")

    def _refresh_display(self):
        if self.original_image is None:
            return
        img = self.original_image
        if self.zoom_num > 1:
            img = img.zoom(self.zoom_num, self.zoom_num)
        if self.sub_num > 1:
            img = img.subsample(self.sub_num, self.sub_num)
        self.display_image = img

        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.display_image)
        w = self.display_image.width()
        h = self.display_image.height()
        self.canvas.config(scrollregion=(0, 0, w, h))
        self._center_image()
        self._update_status()

    def _center_image(self):
        if self.display_image is None or self.image_id is None:
            return
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        iw = self.display_image.width()
        ih = self.display_image.height()
        x = max((cw - iw) // 2, 0)
        y = max((ch - ih) // 2, 0)
        self.canvas.coords(self.image_id, x, y)
        self.canvas.config(scrollregion=(0, 0, max(cw, iw), max(ch, ih)))

    def _on_canvas_resize(self, _event):
        self._center_image()

    def _update_status(self):
        if not self.image_list:
            self.status.config(text="就绪")
            return
        path = self.image_list[self.index]
        ow = self.original_image.width() if self.original_image else 0
        oh = self.original_image.height() if self.original_image else 0
        zoom_pct = int(round(self.zoom_num / self.sub_num * 100))
        self.status.config(
            text=f"[{self.index + 1}/{len(self.image_list)}]  "
                 f"{os.path.basename(path)}   "
                 f"原始: {ow}x{oh}   "
                 f"缩放: {zoom_pct}%"
        )

    # ---------- 切换 ----------
    def prev_image(self):
        if not self.image_list:
            return
        self.index = (self.index - 1) % len(self.image_list)
        self._show_current()

    def next_image(self):
        if not self.image_list:
            return
        self.index = (self.index + 1) % len(self.image_list)
        self._show_current()

    # ---------- 缩放 ----------
    def zoom_in(self):
        if self.original_image is None:
            return
        if self.sub_num > 1:
            self.sub_num -= 1
        else:
            if self.zoom_num < 8:  # 限制最大放大
                self.zoom_num += 1
        self._refresh_display()

    def zoom_out(self):
        if self.original_image is None:
            return
        if self.zoom_num > 1:
            self.zoom_num -= 1
        else:
            if self.sub_num < 8:  # 限制最大缩小
                self.sub_num += 1
        self._refresh_display()

    def zoom_reset(self):
        if self.original_image is None:
            return
        self.zoom_num = 1
        self.sub_num = 1
        self._refresh_display()

    def fit_window(self):
        """按整数倍缩小到适应窗口（只能整数级别）"""
        if self.original_image is None:
            return
        cw = max(self.canvas.winfo_width(), 1)
        ch = max(self.canvas.winfo_height(), 1)
        iw = self.original_image.width()
        ih = self.original_image.height()
        self.zoom_num = 1
        if iw <= cw and ih <= ch:
            self.sub_num = 1
        else:
            # 求最小整数 sub 使得图片不超过画布
            sub_w = (iw + cw - 1) // cw
            sub_h = (ih + ch - 1) // ch
            self.sub_num = max(sub_w, sub_h, 1)
        self._refresh_display()


if __name__ == "__main__":
    ImageViewer().mainloop()
