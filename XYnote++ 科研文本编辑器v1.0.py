import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, font, colorchooser, simpledialog
import os
import re
import json
import time
import subprocess
import threading
import datetime
import webbrowser
from PIL import Image, ImageTk
import importlib.util
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sympy as sp
import pandas as pd

class XYnotePlusPlus:
    def __init__(self, root):
        self.root = root
        self.root.title("XYnote++ 科研文本编辑器")
        self.root.geometry("1400x900")
        
        # 开发者信息
        self.developer = "蜗客小顽童"
        self.email = "surezx4@163.com"
        
        # 当前主题
        self.current_theme = "light"
        
        # 插件系统
        self.plugins = {}
        
        # 项目管理
        self.current_project = None
        self.project_files = {}
        
        # 宏录制
        self.recording_macro = False
        self.macro_actions = []
        
        # 代码折叠
        self.folding_regions = {}
        
        # 代码自动完成
        self.autocomplete_active = False
        self.autocomplete_listbox = None
        self.autocomplete_words = set()
        
        # Git集成
        self.git_available = self.check_git_available()
        
        # 科研相关变量
        self.latex_preview_window = None
        self.data_visualization_frame = None
        self.equation_counter = 1
        self.reference_counter = 1
        
        # 初始化界面
        self.setup_ui()
        self.create_menu()
        self.create_toolbar()
        self.create_sidebar()
        
        # 绑定事件
        self.bind_events()
        
        # 初始化一个标签页
        self.create_new_tab()
        
        # 状态栏初始化
        self.update_status_bar()
        
    def setup_ui(self):
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左右分割面板
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧边栏框架
        self.sidebar_frame = ttk.Frame(self.paned_window, width=250)
        self.paned_window.add(self.sidebar_frame, weight=0)
        
        # 右侧主内容框架
        self.content_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.content_frame, weight=1)
        
        # 创建标签控件
        self.tab_control = ttk.Notebook(self.content_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # 创建状态栏
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 状态栏左侧信息
        self.status_left = ttk.Label(self.status_bar, text="行: 1, 列: 1", relief=tk.SUNKEN, anchor=tk.W)
        self.status_left.pack(side=tk.LEFT, fill=tk.X, padx=2, pady=1)
        
        # 状态栏中间信息
        self.status_center = ttk.Label(self.status_bar, text="UTF-8 | 普通文本", relief=tk.SUNKEN, anchor=tk.CENTER)
        self.status_center.pack(side=tk.LEFT, fill=tk.X, padx=2, pady=1, expand=True)
        
        # 状态栏右侧信息
        self.status_right = ttk.Label(self.status_bar, text="就绪", relief=tk.SUNKEN, anchor=tk.E)
        self.status_right.pack(side=tk.RIGHT, fill=tk.X, padx=2, pady=1)
        
    def create_sidebar(self):
        # 创建侧边栏选项卡
        self.sidebar_notebook = ttk.Notebook(self.sidebar_frame)
        self.sidebar_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 文件浏览器
        self.file_browser_frame = ttk.Frame(self.sidebar_notebook)
        self.sidebar_notebook.add(self.file_browser_frame, text="文件")
        
        # 文件浏览器工具栏
        file_toolbar = ttk.Frame(self.file_browser_frame)
        file_toolbar.pack(fill=tk.X)
        
        ttk.Button(file_toolbar, text="刷新", command=self.refresh_file_browser).pack(side=tk.LEFT, padx=2, pady=2)
        ttk.Button(file_toolbar, text="向上", command=self.navigate_up).pack(side=tk.LEFT, padx=2, pady=2)
        
        # 当前路径显示
        self.current_path_var = tk.StringVar()
        self.current_path_label = ttk.Label(self.file_browser_frame, textvariable=self.current_path_var)
        self.current_path_label.pack(fill=tk.X, padx=5, pady=2)
        
        # 文件树
        self.file_tree_frame = ttk.Frame(self.file_browser_frame)
        self.file_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建文件树和滚动条
        self.file_tree_scrollbar = ttk.Scrollbar(self.file_tree_frame)
        self.file_tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_tree = ttk.Treeview(
            self.file_tree_frame, 
            yscrollcommand=self.file_tree_scrollbar.set,
            selectmode="browse"
        )
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.file_tree_scrollbar.config(command=self.file_tree.yview)
        
        # 初始化文件浏览器到当前目录
        self.current_directory = os.getcwd()
        self.current_path_var.set(self.current_directory)
        self.populate_file_tree()
        
        # 绑定文件树事件
        self.file_tree.bind("<Double-1>", self.on_file_double_click)
        self.file_tree.bind("<<TreeviewOpen>>", self.on_folder_expand)
        
        # Git面板
        self.git_frame = ttk.Frame(self.sidebar_notebook)
        self.sidebar_notebook.add(self.git_frame, text="Git")
        
        if self.git_available:
            self.setup_git_panel()
        else:
            ttk.Label(self.git_frame, text="Git未安装").pack(pady=10)
        
        # 科研工具面板
        self.research_frame = ttk.Frame(self.sidebar_notebook)
        self.sidebar_notebook.add(self.research_frame, text="科研工具")
        self.setup_research_tools()
        
        # 代码大纲面板
        self.outline_frame = ttk.Frame(self.sidebar_notebook)
        self.sidebar_notebook.add(self.outline_frame, text="大纲")
        
        ttk.Label(self.outline_frame, text="代码大纲将在这里显示").pack(pady=10)
        
    def setup_research_tools(self):
        """设置科研工具面板"""
        # 创建工具栏
        research_toolbar = ttk.Frame(self.research_frame)
        research_toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(research_toolbar, text="科研工具", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # 工具按钮框架
        tools_frame = ttk.Frame(self.research_frame)
        tools_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # LaTeX工具
        latex_frame = ttk.LabelFrame(tools_frame, text="LaTeX工具")
        latex_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(latex_frame, text="插入LaTeX公式", command=self.insert_latex_equation).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(latex_frame, text="LaTeX预览", command=self.preview_latex).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(latex_frame, text="插入参考文献", command=self.insert_reference).pack(fill=tk.X, padx=5, pady=2)
        
        # 数据可视化工具
        data_frame = ttk.LabelFrame(tools_frame, text="数据可视化")
        data_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(data_frame, text="绘制图表", command=self.open_data_visualization).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(data_frame, text="导入数据", command=self.import_data).pack(fill=tk.X, padx=5, pady=2)
        
        # 符号计算工具
        calc_frame = ttk.LabelFrame(tools_frame, text="符号计算")
        calc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(calc_frame, text="符号计算", command=self.open_symbolic_calculator).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(calc_frame, text="方程求解", command=self.solve_equation).pack(fill=tk.X, padx=5, pady=2)
        
        # 文献管理工具
        ref_frame = ttk.LabelFrame(tools_frame, text="文献管理")
        ref_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(ref_frame, text="管理参考文献", command=self.manage_references).pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(ref_frame, text="生成参考文献", command=self.generate_bibliography).pack(fill=tk.X, padx=5, pady=2)
        
    def setup_git_panel(self):
        # Git状态
        git_status_frame = ttk.Frame(self.git_frame)
        git_status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(git_status_frame, text="Git状态:").pack(anchor=tk.W)
        
        self.git_status_text = scrolledtext.ScrolledText(
            git_status_frame, 
            height=10,
            state=tk.DISABLED
        )
        self.git_status_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Git操作按钮
        git_buttons_frame = ttk.Frame(self.git_frame)
        git_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(git_buttons_frame, text="刷新状态", command=self.refresh_git_status).pack(side=tk.LEFT, padx=2)
        ttk.Button(git_buttons_frame, text="提交", command=self.git_commit).pack(side=tk.LEFT, padx=2)
        ttk.Button(git_buttons_frame, text="推送", command=self.git_push).pack(side=tk.LEFT, padx=2)
        ttk.Button(git_buttons_frame, text="拉取", command=self.git_pull).pack(side=tk.LEFT, padx=2)
        
        # 初始刷新Git状态
        self.refresh_git_status()
    
    def populate_file_tree(self):
        """填充文件树"""
        self.file_tree.delete(*self.file_tree.get_children())
        
        # 添加上一级目录
        parent_dir = os.path.dirname(self.current_directory)
        if parent_dir != self.current_directory:
            self.file_tree.insert("", "end", iid=parent_dir, text="..", values=("DIR",))
        
        # 添加当前目录下的文件和文件夹
        try:
            for item in sorted(os.listdir(self.current_directory)):
                full_path = os.path.join(self.current_directory, item)
                if os.path.isdir(full_path):
                    # 是目录，添加并标记为有子节点
                    self.file_tree.insert("", "end", iid=full_path, text=item, values=("DIR",))
                    # 预先添加一个虚拟节点，以便显示展开箭头
                    self.file_tree.insert(full_path, "end", text="加载中...")
                else:
                    # 是文件，添加文件
                    self.file_tree.insert("", "end", iid=full_path, text=item, values=("FILE",))
        except PermissionError:
            messagebox.showerror("错误", "无法访问目录")
    
    def on_folder_expand(self, event):
        """文件夹展开事件"""
        item = self.file_tree.focus()
        if item:
            # 清除虚拟节点
            children = self.file_tree.get_children(item)
            for child in children:
                self.file_tree.delete(child)
            
            # 添加实际内容
            try:
                for sub_item in sorted(os.listdir(item)):
                    full_path = os.path.join(item, sub_item)
                    if os.path.isdir(full_path):
                        self.file_tree.insert(item, "end", iid=full_path, text=sub_item, values=("DIR",))
                        # 预先添加一个虚拟节点
                        self.file_tree.insert(full_path, "end", text="加载中...")
                    else:
                        self.file_tree.insert(item, "end", iid=full_path, text=sub_item, values=("FILE",))
            except PermissionError:
                messagebox.showerror("错误", "无法访问目录")
    
    def on_file_double_click(self, event):
        """文件双击事件"""
        item = self.file_tree.selection()[0]
        if self.file_tree.item(item, "values")[0] == "FILE":
            # 打开文件
            self.open_file(file_path=item)
        elif self.file_tree.item(item, "values")[0] == "DIR":
            if item == os.path.dirname(self.current_directory):
                # 向上导航
                self.navigate_up()
            else:
                # 进入目录
                self.current_directory = item
                self.current_path_var.set(self.current_directory)
                self.populate_file_tree()
    
    def navigate_up(self):
        """向上导航"""
        parent_dir = os.path.dirname(self.current_directory)
        if parent_dir != self.current_directory:
            self.current_directory = parent_dir
            self.current_path_var.set(self.current_directory)
            self.populate_file_tree()
    
    def refresh_file_browser(self):
        """刷新文件浏览器"""
        self.populate_file_tree()
    
    def check_git_available(self):
        """检查Git是否可用"""
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def refresh_git_status(self):
        """刷新Git状态"""
        if not self.git_available:
            return
        
        # 在工作线程中执行Git命令
        def git_status_thread():
            try:
                # 获取Git状态
                result = subprocess.run(
                    ["git", "status", "--porcelain"],
                    cwd=self.current_directory,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # 获取当前分支
                branch_result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=self.current_directory,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                branch_name = branch_result.stdout.strip()
                
                # 更新UI
                self.root.after(0, lambda: self.update_git_status_display(result.stdout, branch_name))
                
            except subprocess.CalledProcessError as e:
                # 检查是否是因为不在Git仓库中
                if "not a git repository" in e.stderr.lower():
                    status_text = "当前目录不是Git仓库"
                else:
                    status_text = f"错误: {e.stderr}"
                
                # 安全地更新UI
                try:
                    self.root.after(0, lambda: self.git_status_text.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.git_status_text.delete(1.0, tk.END))
                    self.root.after(0, lambda: self.git_status_text.insert(tk.END, status_text))
                    self.root.after(0, lambda: self.git_status_text.config(state=tk.DISABLED))
                except:
                    pass  # 如果主循环已经结束，忽略错误
        
        threading.Thread(target=git_status_thread, daemon=True).start()
    
    def update_git_status_display(self, status_output, branch_name):
        """更新Git状态显示"""
        self.git_status_text.config(state=tk.NORMAL)
        self.git_status_text.delete(1.0, tk.END)
        
        self.git_status_text.insert(tk.END, f"分支: {branch_name}\n\n")
        
        if status_output:
            self.git_status_text.insert(tk.END, "变更文件:\n")
            self.git_status_text.insert(tk.END, status_output)
        else:
            self.git_status_text.insert(tk.END, "工作区干净，没有变更")
        
        self.git_status_text.config(state=tk.DISABLED)
    
    def git_commit(self):
        """Git提交"""
        if not self.git_available:
            messagebox.showinfo("信息", "Git未安装")
            return
        
        commit_message = simpledialog.askstring("Git提交", "输入提交消息:")
        if commit_message:
            try:
                result = subprocess.run(
                    ["git", "commit", "-a", "-m", commit_message],
                    cwd=self.current_directory,
                    capture_output=True,
                    text=True,
                    check=True
                )
                messagebox.showinfo("成功", "提交成功")
                self.refresh_git_status()
            except subprocess.CalledProcessError as e:
                messagebox.showerror("错误", f"提交失败: {e.stderr}")
    
    def git_push(self):
        """Git推送"""
        if not self.git_available:
            messagebox.showinfo("信息", "Git未安装")
            return
        
        try:
            result = subprocess.run(
                ["git", "push"],
                cwd=self.current_directory,
                capture_output=True,
                text=True,
                check=True
            )
            messagebox.showinfo("成功", "推送成功")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("错误", f"推送失败: {e.stderr}")
    
    def git_pull(self):
        """Git拉取"""
        if not self.git_available:
            messagebox.showinfo("信息", "Git未安装")
            return
        
        try:
            result = subprocess.run(
                ["git", "pull"],
                cwd=self.current_directory,
                capture_output=True,
                text=True,
                check=True
            )
            messagebox.showinfo("成功", "拉取成功")
            self.refresh_git_status()
        except subprocess.CalledProcessError as e:
            messagebox.showerror("错误", f"拉取失败: {e.stderr}")
    
    def create_new_tab(self, filename="未命名"):
        # 创建新框架作为标签页
        tab_frame = ttk.Frame(self.tab_control)
        
        # 创建文本区域和滚动条
        text_frame = ttk.Frame(tab_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(text_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 文本区域
        text_area = tk.Text(
            text_frame, 
            wrap=tk.NONE, 
            undo=True, 
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            font=("Consolas", 10)
        )
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 配置滚动条
        v_scrollbar.config(command=text_area.yview)
        h_scrollbar.config(command=text_area.xview)
        
        # 添加行号和折叠区域
        line_numbers = TextLineNumbers(text_frame, width=30, text_widget=text_area, editor=self)
        line_numbers.attach(text_area)
        line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # 存储标签页数据
        tab_data = {
            "text_area": text_area,
            "line_numbers": line_numbers,
            "filename": filename,
            "modified": False,
            "syntax_language": "plain",
            "folding_regions": {}
        }
        
        # 将数据添加到tab_frame的属性中
        for key, value in tab_data.items():
            setattr(tab_frame, key, value)
        
        # 添加标签页
        self.tab_control.add(tab_frame, text=filename)
        self.tab_control.select(tab_frame)
        
        # 绑定事件
        text_area.bind("<KeyRelease>", self.on_text_change)
        text_area.bind("<ButtonRelease>", self.on_text_change)
        text_area.bind("<Control-f>", self.find_text)
        text_area.bind("<Control-h>", self.replace_text)
        text_area.bind("<Control-space>", self.trigger_autocomplete)
        text_area.bind("<KeyPress>", self.record_macro_action)  # 修复：改为正确的方法名
        
        # 应用当前主题
        self.apply_theme_to_textwidget(text_area)
        
        return tab_frame
    
    def get_current_tab_data(self):
        """获取当前标签页的数据"""
        current_tab = self.tab_control.select()
        if current_tab:
            tab_widget = self.tab_control.nametowidget(current_tab)
            return current_tab, tab_widget
        return None, None
    
    def on_text_change(self, event=None):
        """文本变化时的回调"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            # 更新行号
            if hasattr(tab_widget, 'line_numbers'):
                tab_widget.line_numbers.redraw()
            
            # 更新状态栏
            self.update_status_bar()
            
            # 标记为已修改
            self.mark_tab_modified(tab_id, True)
            
            # 语法高亮
            self.highlight_syntax()
            
            # 更新代码折叠
            self.update_code_folding()
            
            # 更新自动完成词库
            self.update_autocomplete_words()
    
    def update_status_bar(self):
        """更新状态栏信息"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            text_area = tab_widget.text_area
            line, col = text_area.index(tk.INSERT).split('.')
            self.status_left.config(text=f"行: {line}, 列: {int(col)+1}")
            
            # 更新编码和语言信息
            language = getattr(tab_widget, 'syntax_language', 'plain')
            self.status_center.config(text=f"UTF-8 | {language}")
            
            # 更新状态信息
            if hasattr(tab_widget, 'modified') and tab_widget.modified:
                self.status_right.config(text="已修改")
            else:
                self.status_right.config(text="就绪")
    
    def mark_tab_modified(self, tab_id, modified):
        """标记标签页是否已修改"""
        if tab_id:
            tab_text = self.tab_control.tab(tab_id, "text")
            if modified and not tab_text.endswith(" *"):
                self.tab_control.tab(tab_id, text=tab_text + " *")
                tab_widget = self.tab_control.nametowidget(tab_id)
                if hasattr(tab_widget, 'modified'):
                    tab_widget.modified = True
            elif not modified and tab_text.endswith(" *"):
                self.tab_control.tab(tab_id, text=tab_text[:-2])
                tab_widget = self.tab_control.nametowidget(tab_id)
                if hasattr(tab_widget, 'modified'):
                    tab_widget.modified = False
    
    def create_menu(self):
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="打开...", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="保存", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="另存为...", accelerator="Ctrl+Shift+S", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="全部保存", command=self.save_all_files)
        file_menu.add_separator()
        
        # 项目管理子菜单
        project_menu = tk.Menu(file_menu, tearoff=0)
        project_menu.add_command(label="新建项目", command=self.new_project)
        project_menu.add_command(label="打开项目", command=self.open_project)
        project_menu.add_command(label="保存项目", command=self.save_project)
        project_menu.add_command(label="关闭项目", command=self.close_project)
        file_menu.add_cascade(label="项目", menu=project_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="退出", accelerator="Alt+F4", command=self.exit_app)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="撤销", accelerator="Ctrl+Z", command=self.undo)
        edit_menu.add_command(label="重做", accelerator="Ctrl+Y", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="剪切", accelerator="Ctrl+X", command=self.cut)
        edit_menu.add_command(label="复制", accelerator="Ctrl+C", command=self.copy)
        edit_menu.add_command(label="粘贴", accelerator="Ctrl+V", command=self.paste)
        edit_menu.add_separator()
        edit_menu.add_command(label="查找", accelerator="Ctrl+F", command=self.find_text)
        edit_menu.add_command(label="替换", accelerator="Ctrl+H", command=self.replace_text)
        edit_menu.add_separator()
        edit_menu.add_command(label="全选", accelerator="Ctrl+A", command=self.select_all)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        
        # 主题子菜单
        theme_menu = tk.Menu(view_menu, tearoff=0)
        theme_menu.add_command(label="浅色主题", command=lambda: self.change_theme("light"))
        theme_menu.add_command(label="深色主题", command=lambda: self.change_theme("dark"))
        theme_menu.add_command(label="自定义主题", command=self.custom_theme)
        view_menu.add_cascade(label="主题", menu=theme_menu)
        
        # 缩放子菜单
        zoom_menu = tk.Menu(view_menu, tearoff=0)
        zoom_menu.add_command(label="放大", accelerator="Ctrl++", command=self.zoom_in)
        zoom_menu.add_command(label="缩小", accelerator="Ctrl+-", command=self.zoom_out)
        zoom_menu.add_command(label="重置缩放", accelerator="Ctrl+0", command=self.zoom_reset)
        view_menu.add_cascade(label="缩放", menu=zoom_menu)
        
        view_menu.add_separator()
        self.show_status = tk.BooleanVar()
        self.show_status.set(True)
        view_menu.add_checkbutton(label="状态栏", variable=self.show_status, command=self.toggle_statusbar)
        
        self.show_sidebar = tk.BooleanVar()
        self.show_sidebar.set(True)
        view_menu.add_checkbutton(label="侧边栏", variable=self.show_sidebar, command=self.toggle_sidebar)
        menubar.add_cascade(label="视图", menu=view_menu)
        
        # 科研菜单
        research_menu = tk.Menu(menubar, tearoff=0)
        research_menu.add_command(label="插入LaTeX公式", command=self.insert_latex_equation)
        research_menu.add_command(label="LaTeX预览", command=self.preview_latex)
        research_menu.add_separator()
        research_menu.add_command(label="数据可视化", command=self.open_data_visualization)
        research_menu.add_command(label="符号计算", command=self.open_symbolic_calculator)
        research_menu.add_separator()
        research_menu.add_command(label="管理参考文献", command=self.manage_references)
        research_menu.add_command(label="生成参考文献", command=self.generate_bibliography)
        menubar.add_cascade(label="科研", menu=research_menu)
        
        # 宏菜单
        macro_menu = tk.Menu(menubar, tearoff=0)
        macro_menu.add_command(label="开始录制宏", accelerator="Ctrl+Shift+R", command=self.start_macro_recording)
        macro_menu.add_command(label="停止录制宏", accelerator="Ctrl+Shift+S", command=self.stop_macro_recording)
        macro_menu.add_command(label="播放宏", accelerator="Ctrl+Shift+P", command=self.play_macro)
        macro_menu.add_command(label="保存宏", command=self.save_macro)
        macro_menu.add_command(label="加载宏", command=self.load_macro)
        menubar.add_cascade(label="宏", menu=macro_menu)
        
        # 语言菜单
        self.language_menu = tk.Menu(menubar, tearoff=0)
        self.language_menu.add_command(label="普通文本", command=lambda: self.set_syntax_highlighting("plain"))
        self.language_menu.add_command(label="Python", command=lambda: self.set_syntax_highlighting("python"))
        self.language_menu.add_command(label="Java", command=lambda: self.set_syntax_highlighting("java"))
        self.language_menu.add_command(label="C++", command=lambda: self.set_syntax_highlighting("cpp"))
        self.language_menu.add_command(label="HTML", command=lambda: self.set_syntax_highlighting("html"))
        self.language_menu.add_command(label="CSS", command=lambda: self.set_syntax_highlighting("css"))
        self.language_menu.add_command(label="JavaScript", command=lambda: self.set_syntax_highlighting("javascript"))
        self.language_menu.add_command(label="LaTeX", command=lambda: self.set_syntax_highlighting("latex"))
        self.language_menu.add_command(label="Markdown", command=lambda: self.set_syntax_highlighting("markdown"))
        menubar.add_cascade(label="语言", menu=self.language_menu)
        
        # 代码菜单
        code_menu = tk.Menu(menubar, tearoff=0)
        code_menu.add_command(label="折叠所有", command=self.fold_all)
        code_menu.add_command(label="展开所有", command=self.unfold_all)
        code_menu.add_separator()
        code_menu.add_command(label="格式化代码", command=self.format_code)
        menubar.add_cascade(label="代码", menu=code_menu)
        
        # 插件菜单
        self.plugin_menu = tk.Menu(menubar, tearoff=0)
        self.plugin_menu.add_command(label="加载插件", command=self.load_plugin)
        self.plugin_menu.add_command(label="管理插件", command=self.manage_plugins)
        menubar.add_cascade(label="插件", menu=self.plugin_menu)
        
        # Git菜单
        git_menu = tk.Menu(menubar, tearoff=0)
        git_menu.add_command(label="Git状态", command=self.refresh_git_status)
        git_menu.add_command(label="Git提交", command=self.git_commit)
        git_menu.add_command(label="Git推送", command=self.git_push)
        git_menu.add_command(label="Git拉取", command=self.git_pull)
        menubar.add_cascade(label="Git", menu=git_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用教程", command=self.show_tutorial)
        help_menu.add_command(label="关于", command=self.show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def create_toolbar(self):
        # 创建工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # 添加工具栏按钮
        buttons = [
            ("新建", self.new_file, None),
            ("打开", self.open_file, None),
            ("保存", self.save_file, None),
            ("", None, None),
            ("剪切", self.cut, None),
            ("复制", self.copy, None),
            ("粘贴", self.paste, None),
            ("", None, None),
            ("撤销", self.undo, None),
            ("重做", self.redo, None),
            ("", None, None),
            ("查找", self.find_text, None),
            ("", None, None),
            ("录制宏", self.start_macro_recording, "red"),
            ("播放宏", self.play_macro, "green"),
        ]
        
        for text, command, color in buttons:
            if text:
                if color:
                    btn = ttk.Button(toolbar, text=text, command=command, width=6, style=f"{color}.TButton")
                else:
                    btn = ttk.Button(toolbar, text=text, command=command, width=6)
                btn.pack(side=tk.LEFT, padx=2, pady=2)
            else:
                # 添加分隔符
                sep = ttk.Separator(toolbar, orient=tk.VERTICAL)
                sep.pack(side=tk.LEFT, padx=4, pady=4, fill=tk.Y)
    
    def bind_events(self):
        # 绑定快捷键
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-Shift-S>", lambda e: self.save_as_file())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<Control-Shift-R>", lambda e: self.start_macro_recording())
        self.root.bind("<Control-Shift-S>", lambda e: self.stop_macro_recording())
        self.root.bind("<Control-Shift-P>", lambda e: self.play_macro())
        
        # 标签页切换事件
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)
    
    def on_tab_changed(self, event):
        """标签页切换时的回调"""
        self.update_status_bar()
        self.highlight_syntax()
        self.update_code_folding()
    
    def toggle_sidebar(self):
        """显示/隐藏侧边栏"""
        if self.show_sidebar.get():
            self.sidebar_frame.pack(fill=tk.BOTH, expand=True)
        else:
            self.sidebar_frame.pack_forget()
    
    def new_file(self):
        """创建新文件"""
        self.create_new_tab()
    
    def open_file(self, file_path=None):
        """打开文件"""
        if not file_path:
            file_path = filedialog.askopenfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                # 创建新标签页
                tab_widget = self.create_new_tab(os.path.basename(file_path))
                tab_widget.text_area.insert(1.0, content)
                tab_widget.filename = file_path
                tab_widget.modified = False
                
                # 根据文件扩展名设置语法高亮
                ext = os.path.splitext(file_path)[1].lower()
                self.auto_set_syntax(ext)
                
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件: {str(e)}")
    
    def save_file(self):
        """保存文件"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'filename'):
            filename = tab_widget.filename
            if filename == "未命名":
                self.save_as_file()
            else:
                try:
                    content = tab_widget.text_area.get(1.0, tk.END)
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(content)
                    
                    # 更新标签页状态
                    self.mark_tab_modified(tab_id, False)
                    tab_widget.filename = filename
                    self.tab_control.tab(tab_id, text=os.path.basename(filename))
                    
                except Exception as e:
                    messagebox.showerror("错误", f"无法保存文件: {str(e)}")
    
    def save_as_file(self):
        """另存为文件"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            if file_path:
                try:
                    content = tab_widget.text_area.get(1.0, tk.END)
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(content)
                    
                    # 更新标签页状态
                    self.mark_tab_modified(tab_id, False)
                    tab_widget.filename = file_path
                    self.tab_control.tab(tab_id, text=os.path.basename(file_path))
                    
                    # 根据文件扩展名设置语法高亮
                    ext = os.path.splitext(file_path)[1].lower()
                    self.auto_set_syntax(ext)
                    
                except Exception as e:
                    messagebox.showerror("错误", f"无法保存文件: {str(e)}")
    
    def save_all_files(self):
        """保存所有文件"""
        for tab_id in self.tab_control.tabs():
            self.tab_control.select(tab_id)
            self.save_file()
    
    def new_project(self):
        """新建项目"""
        project_path = filedialog.askdirectory(title="选择项目目录")
        if project_path:
            self.current_project = {
                "name": os.path.basename(project_path),
                "path": project_path,
                "files": []
            }
            self.current_directory = project_path
            self.current_path_var.set(self.current_directory)
            self.populate_file_tree()
            messagebox.showinfo("成功", f"已创建项目: {self.current_project['name']}")
    
    def open_project(self):
        """打开项目"""
        project_file = filedialog.askopenfilename(
            title="选择项目文件",
            filetypes=[("XYnote++ 项目", "*.xyp"), ("所有文件", "*.*")]
        )
        
        if project_file:
            try:
                with open(project_file, "r", encoding="utf-8") as f:
                    project_data = json.load(f)
                
                self.current_project = project_data
                self.current_directory = project_data["path"]
                self.current_path_var.set(self.current_directory)
                self.populate_file_tree()
                
                # 打开项目中的文件
                for file_path in project_data["files"]:
                    if os.path.exists(file_path):
                        self.open_file(file_path)
                
                messagebox.showinfo("成功", f"已打开项目: {self.current_project['name']}")
                
            except Exception as e:
                messagebox.showerror("错误", f"无法打开项目: {str(e)}")
    
    def save_project(self):
        """保存项目"""
        if not self.current_project:
            messagebox.showinfo("信息", "没有当前项目")
            return
        
        # 收集所有打开的文件
        open_files = []
        for tab_id in self.tab_control.tabs():
            tab_widget = self.tab_control.nametowidget(tab_id)
            if hasattr(tab_widget, 'filename') and tab_widget.filename != "未命名":
                open_files.append(tab_widget.filename)
        
        self.current_project["files"] = open_files
        
        # 保存项目文件
        project_file = os.path.join(self.current_project["path"], f"{self.current_project['name']}.xyp")
        try:
            with open(project_file, "w", encoding="utf-8") as f:
                json.dump(self.current_project, f, indent=4)
            
            messagebox.showinfo("成功", f"项目已保存: {project_file}")
            
        except Exception as e:
            messagebox.showerror("错误", f"无法保存项目: {str(e)}")
    
    def close_project(self):
        """关闭项目"""
        self.current_project = None
        messagebox.showinfo("信息", "项目已关闭")
    
    def exit_app(self):
        """退出应用程序"""
        if messagebox.askokcancel("退出", "确定要退出吗？"):
            self.root.destroy()
    
    def undo(self):
        """撤销操作"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            try:
                tab_widget.text_area.event_generate("<<Undo>>")
            except:
                pass
    
    def redo(self):
        """重做操作"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            try:
                tab_widget.text_area.event_generate("<<Redo>>")
            except:
                pass
    
    def cut(self):
        """剪切文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            tab_widget.text_area.event_generate("<<Cut>>")
    
    def copy(self):
        """复制文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            tab_widget.text_area.event_generate("<<Copy>>")
    
    def paste(self):
        """粘贴文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            tab_widget.text_area.event_generate("<<Paste>>")
    
    def select_all(self):
        """全选文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            tab_widget.text_area.tag_add(tk.SEL, "1.0", tk.END)
            tab_widget.text_area.mark_set(tk.INSERT, "1.0")
            tab_widget.text_area.see(tk.INSERT)
    
    def find_text(self, event=None):
        """查找文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            text_area = tab_widget.text_area
            
            # 创建查找窗口
            find_window = tk.Toplevel(self.root)
            find_window.title("查找")
            find_window.geometry("400x150")
            find_window.resizable(False, False)
            find_window.transient(self.root)
            find_window.grab_set()
            
            ttk.Label(find_window, text="查找:").pack(pady=5)
            find_entry = ttk.Entry(find_window, width=40)
            find_entry.pack(pady=5)
            find_entry.focus_set()
            
            # 添加选项框架
            options_frame = ttk.Frame(find_window)
            options_frame.pack(pady=5)
            
            match_case = tk.BooleanVar()
            match_case_check = ttk.Checkbutton(options_frame, text="区分大小写", variable=match_case)
            match_case_check.pack(side=tk.LEFT, padx=10)
            
            whole_word = tk.BooleanVar()
            whole_word_check = ttk.Checkbutton(options_frame, text="全字匹配", variable=whole_word)
            whole_word_check.pack(side=tk.LEFT, padx=10)
            
            def find():
                # 清除之前的标记
                text_area.tag_remove("found", "1.0", tk.END)
                
                search_text = find_entry.get()
                if search_text:
                    start_pos = "1.0"
                    flags = 0
                    
                    if match_case.get():
                        flags = re.IGNORECASE
                    
                    while True:
                        if whole_word.get():
                            # 全字匹配
                            pattern = r'\b' + re.escape(search_text) + r'\b'
                            start_pos = text_area.search(pattern, start_pos, stopindex=tk.END, regexp=True, flags=flags)
                        else:
                            start_pos = text_area.search(search_text, start_pos, stopindex=tk.END, nocase=not match_case.get())
                        
                        if not start_pos:
                            break
                            
                        end_pos = f"{start_pos}+{len(search_text)}c"
                        text_area.tag_add("found", start_pos, end_pos)
                        start_pos = end_pos
                    
                    text_area.tag_config("found", background="yellow")
                    text_area.focus_set()
            
            button_frame = ttk.Frame(find_window)
            button_frame.pack(pady=5)
            
            ttk.Button(button_frame, text="查找", command=find).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="关闭", command=find_window.destroy).pack(side=tk.LEFT, padx=10)
    
    def replace_text(self, event=None):
        """替换文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            text_area = tab_widget.text_area
            
            # 创建替换窗口
            replace_window = tk.Toplevel(self.root)
            replace_window.title("替换")
            replace_window.geometry("400x200")
            replace_window.resizable(False, False)
            replace_window.transient(self.root)
            replace_window.grab_set()
            
            ttk.Label(replace_window, text="查找:").pack(pady=2)
            find_entry = ttk.Entry(replace_window, width=40)
            find_entry.pack(pady=2)
            find_entry.focus_set()
            
            ttk.Label(replace_window, text="替换为:").pack(pady=2)
            replace_entry = ttk.Entry(replace_window, width=40)
            replace_entry.pack(pady=2)
            
            # 添加选项框架
            options_frame = ttk.Frame(replace_window)
            options_frame.pack(pady=5)
            
            match_case = tk.BooleanVar()
            match_case_check = ttk.Checkbutton(options_frame, text="区分大小写", variable=match_case)
            match_case_check.pack(side=tk.LEFT, padx=10)
            
            whole_word = tk.BooleanVar()
            whole_word_check = ttk.Checkbutton(options_frame, text="全字匹配", variable=whole_word)
            whole_word_check.pack(side=tk.LEFT, padx=10)
            
            def replace():
                find_text = find_entry.get()
                replace_text = replace_entry.get()
                
                if find_text:
                    content = text_area.get(1.0, tk.END)
                    
                    if whole_word.get():
                        pattern = r'\b' + re.escape(find_text) + r'\b'
                        if match_case.get():
                            new_content = re.sub(pattern, replace_text, content)
                        else:
                            new_content = re.sub(pattern, replace_text, content, flags=re.IGNORECASE)
                    else:
                        if match_case.get():
                            new_content = content.replace(find_text, replace_text)
                        else:
                            # 不区分大小写替换
                            pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                            new_content = pattern.sub(replace_text, content)
                    
                    text_area.delete(1.0, tk.END)
                    text_area.insert(1.0, new_content)
            
            def replace_all():
                find_text = find_entry.get()
                replace_text = replace_entry.get()
                
                if find_text:
                    content = text_area.get(1.0, tk.END)
                    
                    if whole_word.get():
                        pattern = r'\b' + re.escape(find_text) + r'\b'
                        if match_case.get():
                            new_content = re.sub(pattern, replace_text, content)
                        else:
                            new_content = re.sub(pattern, replace_text, content, flags=re.IGNORECASE)
                    else:
                        if match_case.get():
                            new_content = content.replace(find_text, replace_text)
                        else:
                            # 不区分大小写替换
                            pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                            new_content = pattern.sub(replace_text, content)
                    
                    text_area.delete(1.0, tk.END)
                    text_area.insert(1.0, new_content)
            
            button_frame = ttk.Frame(replace_window)
            button_frame.pack(pady=5)
            
            ttk.Button(button_frame, text="替换", command=replace).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="全部替换", command=replace_all).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="关闭", command=replace_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def toggle_statusbar(self):
        """显示/隐藏状态栏"""
        if self.show_status.get():
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        else:
            self.status_bar.pack_forget()
    
    def change_theme(self, theme):
        """更改主题"""
        self.current_theme = theme
        
        if theme == "light":
            bg_color = "#ffffff"
            fg_color = "#000000"
            cursor_color = "#000000"
        else:  # dark theme
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            cursor_color = "#ffffff"
        
        # 更新所有文本区域的样式
        for tab_id in self.tab_control.tabs():
            tab_widget = self.tab_control.nametowidget(tab_id)
            if hasattr(tab_widget, 'text_area'):
                text_area = tab_widget.text_area
                text_area.config(bg=bg_color, fg=fg_color, insertbackground=cursor_color)
                
                # 更新行号区域
                if hasattr(tab_widget, 'line_numbers'):
                    line_numbers = tab_widget.line_numbers
                    line_numbers.config(bg="#f0f0f0" if theme == "light" else "#3c3f41", 
                                    fg="#666666" if theme == "light" else "#aaaaaa")
                    line_numbers.redraw()
        
        # 更新状态栏
        for widget in self.status_bar.winfo_children():
            widget.config(background="#e0e0e0" if theme == "light" else "#3c3f41",
                         foreground="#000000" if theme == "light" else "#ffffff")
        
        # 重新应用语法高亮
        self.highlight_syntax()
    
    def custom_theme(self):
        """自定义主题"""
        # 选择背景色
        bg_color = colorchooser.askcolor(title="选择背景色", initialcolor="#ffffff")
        if bg_color[1]:
            # 选择前景色
            fg_color = colorchooser.askcolor(title="选择文本颜色", initialcolor="#000000")
            if fg_color[1]:
                # 更新所有文本区域的样式
                for tab_id in self.tab_control.tabs():
                    tab_widget = self.tab_control.nametowidget(tab_id)
                    if hasattr(tab_widget, 'text_area'):
                        text_area = tab_widget.text_area
                        text_area.config(bg=bg_color[1], fg=fg_color[1])
                        
                        # 重新应用语法高亮
                        self.highlight_syntax()
    
    def zoom_in(self):
        """放大文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            text_area = tab_widget.text_area
            current_font = font.Font(font=text_area.cget("font"))
            size = current_font.actual()["size"] + 1
            text_area.config(font=(current_font.actual()["family"], size))
            
            # 更新行号区域
            if hasattr(tab_widget, 'line_numbers'):
                line_numbers = tab_widget.line_numbers
                line_numbers.config(font=(current_font.actual()["family"], size))
                line_numbers.redraw()
    
    def zoom_out(self):
        """缩小文本"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            text_area = tab_widget.text_area
            current_font = font.Font(font=text_area.cget("font"))
            size = max(6, current_font.actual()["size"] - 1)  # 最小字体大小为6
            text_area.config(font=(current_font.actual()["family"], size))
            
            # 更新行号区域
            if hasattr(tab_widget, 'line_numbers'):
                line_numbers = tab_widget.line_numbers
                line_numbers.config(font=(current_font.actual()["family"], size))
                line_numbers.redraw()
    
    def zoom_reset(self):
        """重置缩放"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            text_area = tab_widget.text_area
            text_area.config(font=("Consolas", 10))
            
            # 更新行号区域
            if hasattr(tab_widget, 'line_numbers'):
                line_numbers = tab_widget.line_numbers
                line_numbers.config(font=("Consolas", 10))
                line_numbers.redraw()
    
    def set_syntax_highlighting(self, language):
        """设置语法高亮语言"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget:
            tab_widget.syntax_language = language
            self.highlight_syntax()
    
    def auto_set_syntax(self, extension):
        """根据文件扩展名自动设置语法高亮"""
        language_map = {
            '.py': 'python',
            '.java': 'java',
            '.cpp': 'cpp',
            '.h': 'cpp',
            '.hpp': 'cpp',
            '.c': 'cpp',
            '.cs': 'cpp',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.js': 'javascript',
            '.ts': 'javascript',
            '.json': 'javascript',
            '.xml': 'html',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.sql': 'sql',
            '.tex': 'latex',
            '.bib': 'latex',
            '.md': 'markdown',
            '.txt': 'plain',
            '.log': 'plain'
        }
        
        language = language_map.get(extension, 'plain')
        self.set_syntax_highlighting(language)
    
    def highlight_syntax(self):
        """应用语法高亮"""
        tab_id, tab_widget = self.get_current_tab_data()
        if tab_widget and hasattr(tab_widget, 'text_area'):
            text_area = tab_widget.text_area
            language = getattr(tab_widget, 'syntax_language', 'plain')
            
            # 清除所有标签
            for tag in text_area.tag_names():
                if tag != "sel" and tag != "folded":  # 不要清除选择标签和折叠标签
                    text_area.tag_delete(tag)
            
            if language == 'plain':
                return  # 普通文本不需要语法高亮
            
            # 获取文本内容
            content = text_area.get(1.0, tk.END)
            
            # 定义不同语言的语法规则
            syntax_rules = {
                'python': [
                    (r'#.*$', 'comment'),  # 注释
                    (r'\b(and|as|assert|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b', 'keyword'),  # 关键字
                    (r'\b(True|False|None)\b', 'constant'),  # 常量
                    (r'"[^"\\]*(\\.[^"\\]*)*"', 'string'),  # 双引号字符串
                    (r"'[^'\\]*(\\.[^'\\]*)*'", 'string'),  # 单引号字符串
                    (r'\b([0-9]+(\.[0-9]+)?)\b', 'number'),  # 数字
                ],
                'java': [
                    (r'//.*$', 'comment'),  # 单行注释
                    (r'/\*[\s\S]*?\*/', 'comment'),  # 多行注释
                    (r'\b(abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|native|new|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while)\b', 'keyword'),  # 关键字
                    (r'\b(true|false|null)\b', 'constant'),  # 常量
                    (r'"[^"\\]*(\\.[^"\\]*)*"', 'string'),  # 字符串
                    (r'\b([0-9]+(\.[0-9]+)?)\b', 'number'),  # 数字
                ],
                'cpp': [
                    (r'//.*$', 'comment'),  # 单行注释
                    (r'/\*[\s\S]*?\*/', 'comment'),  # 多行注释
                    (r'\b(alignas|alignof|and|and_eq|asm|auto|bitand|bitor|bool|break|case|catch|char|char8_t|char16_t|char32_t|class|compl|concept|const|consteval|constexpr|constinit|const_cast|continue|co_await|co_return|co_yield|decltype|default|delete|do|double|dynamic_cast|else|enum|explicit|export|extern|false|float|for|friend|goto|if|inline|int|long|mutable|namespace|new|noexcept|not|not_eq|nullptr|operator|or|or_eq|private|protected|public|register|reinterpret_cast|requires|return|short|signed|sizeof|static|static_assert|static_cast|struct|switch|template|this|thread_local|throw|true|try|typedef|typeid|typename|union|unsigned|using|virtual|void|volatile|wchar_t|while|xor|xor_eq)\b', 'keyword'),  # 关键字
                    (r'"[^"\\]*(\\.[^"\\]*)*"', 'string'),  # 字符串
                    (r"'[^'\\]*(\\.[^'\\]*)*'", 'string'),  # 字符
                    (r'\b([0-9]+(\.[0-9]+)?)\b', 'number'),  # 数字
                ],
                'html': [
                    (r'<!--[\s\S]*?-->', 'comment'),  # 注释
                    (r'<!DOCTYPE\s+html>', 'doctype'),  # DOCTYPE
                    (r'</?[a-zA-Z][^>]*>', 'tag'),  # 标签
                    (r'&[a-zA-Z]+;', 'entity'),  # HTML实体
                    (r'#?[a-zA-Z][a-zA-Z0-9]*', 'attribute'),  # 属性
                ],
                'css': [
                    (r'/\*[\s\S]*?\*/', 'comment'),  # 注释
                    (r'#[0-9a-fA-F]{3,6}', 'color'),  # 颜色值
                    (r'\b([0-9]+(\.[0-9]+)?)(px|em|%|pt|cm|mm|in|pc|ex|ch|rem|vw|vh|vmin|vmax)?\b', 'number'),  # 数字和单位
                    (r'\b(margin|padding|border|width|height|color|background|font|display|position|float|clear|overflow|visibility|text|line|list|table|content|counter|quotes|outline|box|flex|grid|align|justify|animation|transition|transform|cursor|opacity|z-index|box-sizing|float|clear|overflow|visibility|text-align|vertical-align|white-space|word-break|word-wrap|word-spacing|letter-spacing|text-decoration|text-indent|text-shadow|text-transform|line-height|list-style|list-style-type|list-style-position|list-style-image|border-radius|border-width|border-style|border-color|border-collapse|border-spacing|table-layout|empty-cells|caption-side)\b', 'property'),  # CSS属性
                    (r':[a-zAZ-]+', 'pseudo'),  # 伪类
                    (r'\.[a-zA-Z][a-zA-Z0-9-]*', 'class'),  # 类选择器
                    (r'#[a-zA-Z][a-zA-Z0-9-]*', 'id'),  # ID选择器
                ],
                'javascript': [
                    (r'//.*$', 'comment'),  # 单行注释
                    (r'/\*[\s\S]*?\*/', 'comment'),  # 多行注释
                    (r'\b(break|case|catch|class|const|continue|debugger|default|delete|do|else|export|extends|finally|for|function|if|import|in|instanceof|new|return|super|switch|this|throw|try|typeof|var|void|while|with|yield)\b', 'keyword'),  # 关键字
                    (r'\b(true|false|null|undefined|NaN|Infinity)\b', 'constant'),  # 常量
                    (r'"[^"\\]*(\\.[^"\\]*)*"', 'string'),  # 双引号字符串
                    (r"'[^'\\]*(\\.[^'\\]*)*'", 'string'),  # 单引号字符串
                    (r'`[^`\\]*(\\.[^`\\]*)*`', 'string'),  # 模板字符串
                    (r'\b([0-9]+(\.[0-9]+)?)\b', 'number'),  # 数字
                    (r'\$?[a-zA-Z_][a-zA-Z0-9_]*', 'variable'),  # 变量
                ],
                'latex': [
                    (r'%.*$', 'comment'),  # 注释
                    (r'\\(begin|end|documentclass|usepackage|section|subsection|subsubsection|caption|label|ref|cite|textbf|textit|emph|texttt|mathrm|mathbf|mathit|mathsf|mathtt|mathcal|mathfrak|mathbb|mathscr|ldots|cdots|vdots|ddots|frac|sqrt|sum|prod|int|oint|lim|infty|alpha|beta|gamma|delta|epsilon|zeta|eta|theta|iota|kappa|lambda|mu|nu|xi|omicron|pi|rho|sigma|tau|upsilon|phi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega)\b', 'keyword'),  # LaTeX命令
                    (r'\\[a-zA-Z]+', 'function'),  # 其他命令
                    (r'\$[^$]*\$', 'formula'),  # 行内公式
                    (r'\\\[[^\]]*\\\]', 'formula'),  # 显示公式
                    (r'\\\([^)]*\\\)', 'formula'),  # 行内公式
                ],
                'markdown': [
                    (r'#.*$', 'header'),  # 标题
                    (r'\*[^*]+\*', 'emphasis'),  # 强调
                    (r'\_[^_]+\_', 'emphasis'),  # 强调
                    (r'\*\*[^*]+\*\*', 'strong'),  # 粗体
                    (r'\_\_[^_]+\_\_', 'strong'),  # 粗体
                    (r'`[^`]+`', 'code'),  # 行内代码
                    (r'\[[^\]]+\]\([^)]+\)', 'link'),  # 链接
                    (r'!\[[^\]]+\]\([^)]+\)', 'image'),  # 图片
                ]
            }
            
            # 定义标签样式
            tag_styles = {
                'comment': {'foreground': '#008000' if self.current_theme == 'light' else '#6a9955'},
                'keyword': {'foreground': '#0000ff' if self.current_theme == 'light' else '#569cd6'},
                'constant': {'foreground': '#0000ff' if self.current_theme == 'light' else '#569cd6'},
                'string': {'foreground': '#a31515' if self.current_theme == 'light' else '#ce9178'},
                'number': {'foreground': '#098658' if self.current_theme == 'light' else '#b5cea8'},
                'doctype': {'foreground': '#808080' if theme == "light" else '#808080'},
                'tag': {'foreground': '#800000' if self.current_theme == 'light' else '#808080'},
                'entity': {'foreground': '#800000' if self.current_theme == 'light' else '#d7ba7d'},
                'attribute': {'foreground': '#ff0000' if self.current_theme == 'light' else '#9cdcfe'},
                'color': {'foreground': '#098658' if self.current_theme == 'light' else '#b5cea8'},
                'property': {'foreground': '#ff0000' if self.current_theme == 'light' else '#9cdcfe'},
                'pseudo': {'foreground': '#800000' if self.current_theme == 'light' else '#d7ba7d'},
                'class': {'foreground': '#800000' if self.current_theme == 'light' else '#d7ba7d'},
                'id': {'foreground': '#800000' if self.current_theme == 'light' else '#d7ba7d'},
                'variable': {'foreground': '#001080' if self.current_theme == 'light' else '#9cdcfe'},
                'function': {'foreground': '#795E26' if self.current_theme == 'light' else '#DCDCAA'},
                'formula': {'foreground': '#0000ff' if self.current_theme == 'light' else '#569cd6'},
                'header': {'foreground': '#0000ff' if self.current_theme == 'light' else '#569cd6', 'font': ('Arial', 12, 'bold')},
                'emphasis': {'foreground': '#800000' if self.current_theme == 'light' else '#ce9178', 'font': ('Arial', 10, 'italic')},
                'strong': {'foreground': '#800000' if self.current_theme == 'light' else '#ce9178', 'font': ('Arial', 10, 'bold')},
                'code': {'foreground': '#a31515' if self.current_theme == 'light' else '#ce9178', 'font': ('Consolas', 10)},
                'link': {'foreground': '#0451a5' if self.current_theme == 'light' else '#9cdcfe', 'underline': True},
                'image': {'foreground': '#0451a5' if self.current_theme == 'light' else '#9cdcfe', 'underline': True},
            }
            
            # 配置标签样式
            for tag_name, style in tag_styles.items():
                text_area.tag_configure(tag_name, **style)
            
            # 应用语法高亮规则
            if language in syntax_rules:
                for pattern, tag_name in syntax_rules[language]:
                    self.apply_highlighting(text_area, pattern, tag_name)
    
    def apply_highlighting(self, text_area, pattern, tag_name):
        """应用高亮规则"""
        content = text_area.get(1.0, tk.END)
        
        for match in re.finditer(pattern, content, re.MULTILINE):
            start = match.start()
            end = match.end()
            
            # 计算行和列
            start_line = content.count('\n', 0, start) + 1
            start_col = start - content.rfind('\n', 0, start)
            end_line = content.count('\n', 0, end) + 1
            end_col = end - content.rfind('\n', 0, end)
            
            # 应用标签
            text_area.tag_add(tag_name, f"{start_line}.{start_col}", f"{end_line}.{end_col}")
    
    def apply_theme_to_textwidget(self, text_widget):
        """应用当前主题到文本组件"""
        if self.current_theme == "light":
            text_widget.config(bg="#ffffff", fg="#000000", insertbackground="#000000")
        else:
            text_widget.config(bg="#2b2b2b", fg="#ffffff", insertbackground="#ffffff")
    
    def start_macro_recording(self):
        """开始录制宏"""
        if self.recording_macro:
            messagebox.showinfo("信息", "已经在录制宏")
            return
        
        self.recording_macro = True
        self.macro_actions = []
        self.status_right.config(text="正在录制宏...")
        messagebox.showinfo("信息", "开始录制宏")
    
    def stop_macro_recording(self):
        """停止录制宏"""
        if not self.recording_macro:
            messagebox.showinfo("信息", "没有在录制宏")
            return
        
        self.recording_macro = False
        self.status_right.config(text="就绪")
        messagebox.showinfo("信息", f"停止录制宏，录制了 {len(self.macro_actions)} 个动作")
    
    def record_macro_action(self, event):
        """录制宏动作"""
        if self.recording_macro:
            action = {
                'type': 'keypress',
                'keysym': event.keysym,
                'char': event.char,
                'time': time.time()
            }
            self.macro_actions.append(action)
    
    def play_macro(self):
        """播放宏"""
        if not self.macro_actions:
            messagebox.showinfo("信息", "没有可播放的宏")
            return
        
        self.status_right.config(text="正在播放宏...")
        
        # 在后台线程中播放宏
        def play_macro_thread():
            tab_id, tab_widget = self.get_current_tab_data()
            if not tab_widget or not hasattr(tab_widget, 'text_area'):
                return
            
            text_area = tab_widget.text_area
            
            # 记录开始时间
            start_time = self.macro_actions[0]['time']
            
            for action in self.macro_actions:
                # 计算延迟
                delay = action['time'] - start_time
                if delay > 0:
                    time.sleep(delay)
                
                # 执行动作
                if action['type'] == 'keypress':
                    if action['char']:
                        text_area.insert(tk.INSERT, action['char'])
                    elif action['keysym'] == 'BackSpace':
                        # 处理退格键
                        text_area.delete(f"{tk.INSERT}-1c", tk.INSERT)
                    elif action['keysym'] == 'Return':
                        text_area.insert(tk.INSERT, '\n')
                    # 可以添加更多特殊键的处理
            
            self.root.after(0, lambda: self.status_right.config(text="就绪"))
        
        threading.Thread(target=play_macro_thread, daemon=True).start()
    
    def save_macro(self):
        """保存宏"""
        if not self.macro_actions:
            messagebox.showinfo("信息", "没有可保存的宏")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xym",
            filetypes=[("XYnote++ 宏", "*.xym"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.macro_actions, f, indent=4)
                
                messagebox.showinfo("成功", f"宏已保存: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法保存宏: {str(e)}")
    
    def load_macro(self):
        """加载宏"""
        file_path = filedialog.askopenfilename(
            filetypes=[("XYnote++ 宏", "*.xym"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.macro_actions = json.load(f)
                
                messagebox.showinfo("成功", f"宏已加载: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载宏: {str(e)}")
    
    def update_code_folding(self):
        """更新代码折叠"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        language = getattr(tab_widget, 'syntax_language', 'plain')
        
        # 清除之前的折叠标记
        if hasattr(tab_widget, 'folding_regions'):
            for region in tab_widget.folding_regions.values():
                text_area.tag_remove("folded", region['start'], region['end'])
        
        tab_widget.folding_regions = {}
        
        # 只有支持的语言才进行代码折叠
        if language not in ['python', 'java', 'cpp', 'javascript']:
            return
        
        content = text_area.get(1.0, tk.END)
        
        # 根据语言确定折叠模式
        if language == 'python':
            # Python: 基于缩进
            self.detect_python_folding(text_area, content, tab_widget)
        else:
            # 其他语言: 基于大括号
            self.detect_brace_folding(text_area, content, tab_widget)
    
    def detect_python_folding(self, text_area, content, tab_widget):
        """检测Python代码的折叠区域"""
        lines = content.split('\n')
        indent_levels = []
        regions = {}
        
        for i, line in enumerate(lines):
            if not line.strip():  # 空行
                continue
                
            indent = len(line) - len(line.lstrip())
            
            if not indent_levels or indent > indent_levels[-1]:
                # 增加缩进，开始新的区域
                indent_levels.append(indent)
                regions[i] = {'indent': indent, 'start': i}
            elif indent < indent_levels[-1]:
                # 减少缩进，结束区域
                while indent_levels and indent < indent_levels[-1]:
                    start_line = list(regions.keys())[-1]
                    regions[start_line]['end'] = i - 1
                    indent_levels.pop()
        
        # 应用折叠区域
        for start_line, region in regions.items():
            if 'end' in region:
                start_index = f"{start_line + 1}.0"
                end_index = f"{region['end'] + 1}.0"
                
                # 添加折叠标记
                text_area.tag_add("folded", start_index, end_index)
                tab_widget.folding_regions[start_line] = {
                    'start': start_index,
                    'end': end_index,
                    'folded': False
                }
    
    def detect_brace_folding(self, text_area, content, tab_widget):
        """检测基于大括号的代码折叠区域"""
        brace_stack = []
        regions = {}
        
        for match in re.finditer(r'[{}]', content):
            brace = match.group()
            pos = match.start()
            
            # 计算行和列
            line = content.count('\n', 0, pos) + 1
            col = pos - content.rfind('\n', 0, pos)
            
            if brace == '{':
                # 开始新区域
                brace_stack.append((line, col))
            elif brace == '}' and brace_stack:
                # 结束区域
                start_line, start_col = brace_stack.pop()
                start_index = f"{start_line}.{start_col}"
                end_index = f"{line}.{col + 1}"
                
                # 添加折叠区域
                regions[(start_line, start_col)] = {
                    'start': start_index,
                    'end': end_index,
                    'folded': False
                }
        
        # 应用折叠区域
        tab_widget.folding_regions = regions
        
        # 配置折叠样式
        text_area.tag_configure("folded", elide=True)
    
    def fold_all(self):
        """折叠所有代码区域"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        
        for region_id, region in tab_widget.folding_regions.items():
            if not region['folded']:
                text_area.tag_add("folded", region['start'], region['end'])
                region['folded'] = True
        
        # 更新行号显示
        if hasattr(tab_widget, 'line_numbers'):
            tab_widget.line_numbers.redraw()
    
    def unfold_all(self):
        """展开所有代码区域"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        
        for region_id, region in tab_widget.folding_regions.items():
            if region['folded']:
                text_area.tag_remove("folded", region['start'], region['end'])
                region['folded'] = False
        
        # 更新行号显示
        if hasattr(tab_widget, 'line_numbers'):
            tab_widget.line_numbers.redraw()
    
    def toggle_fold(self, line):
        """切换指定行的折叠状态"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        
        # 查找包含该行的折叠区域
        for region_id, region in tab_widget.folding_regions.items():
            start_line = int(region['start'].split('.')[0])
            end_line = int(region['end'].split('.')[0])
            
            if start_line <= line <= end_line:
                if region['folded']:
                    text_area.tag_remove("folded", region['start'], region['end'])
                    region['folded'] = False
                else:
                    text_area.tag_add("folded", region['start'], region['end'])
                    region['folded'] = True
                
                # 更新行号显示
                if hasattr(tab_widget, 'line_numbers'):
                    tab_widget.line_numbers.redraw()
                break
    
    def format_code(self):
        """格式化代码"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        language = getattr(tab_widget, 'syntax_language', 'plain')
        
        content = text_area.get(1.0, tk.END)
        
        # 简单的代码格式化
        if language == 'python':
            # Python: 规范化缩进
            lines = content.split('\n')
            formatted_lines = []
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                if not stripped:  # 空行
                    formatted_lines.append('')
                    continue
                
                # 减少缩进
                if stripped.startswith(('elif ', 'else:', 'except', 'finally:')):
                    indent_level = max(0, indent_level - 1)
                
                # 添加缩进
                formatted_line = '    ' * indent_level + stripped
                formatted_lines.append(formatted_line)
                
                # 增加缩进
                if stripped.endswith(':'):
                    indent_level += 1
                # 减少缩进
                elif stripped in ('return', 'break', 'continue', 'pass'):
                    indent_level = max(0, indent_level - 1)
            
            formatted_content = '\n'.join(formatted_lines)
            text_area.delete(1.0, tk.END)
            text_area.insert(1.0, formatted_content)
        
        elif language in ['java', 'cpp', 'javascript']:
            # C风格语言: 规范化大括号
            formatted_content = content.replace('){', ') {')
            formatted_content = formatted_content.replace('} else', '} else')
            formatted_content = formatted_content.replace('} catch', '} catch')
            
            text_area.delete(1.0, tk.END)
            text_area.insert(1.0, formatted_content)
    
    def update_autocomplete_words(self):
        """更新自动完成词库"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        content = text_area.get(1.0, tk.END)
        
        # 提取单词
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', content)
        self.autocomplete_words.update(words)
    
    def trigger_autocomplete(self, event=None):
        """触发自动完成"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        
        # 获取当前单词
        current_pos = text_area.index(tk.INSERT)
        line, col = current_pos.split('.')
        line_text = text_area.get(f"{line}.0", f"{line}.end")
        
        # 提取当前单词
        word_start = col
        while word_start > 0 and line_text[word_start-1].isalnum():
            word_start -= 1
        
        current_word = line_text[word_start:int(col)]
        
        # 获取匹配的单词
        matches = [word for word in self.autocomplete_words if word.startswith(current_word) and word != current_word]
        
        if matches:
            # 显示自动完成列表
            self.show_autocomplete(matches, text_area, f"{line}.{word_start}")
    
    def show_autocomplete(self, matches, text_widget, start_pos):
        """显示自动完成列表"""
        # 隐藏之前的列表
        self.hide_autocomplete()
        
        # 创建列表窗口
        x, y, _, _ = text_widget.bbox(start_pos)
        x += text_widget.winfo_rootx()
        y += text_widget.winfo_rooty() + 20
        
        self.autocomplete_window = tk.Toplevel(text_widget)
        self.autocomplete_window.wm_overrideredirect(True)
        self.autocomplete_window.wm_geometry(f"+{x}+{y}")
        
        self.autocomplete_listbox = tk.Listbox(
            self.autocomplete_window,
            height=min(10, len(matches)),
            selectmode=tk.SINGLE
        )
        self.autocomplete_listbox.pack()
        
        # 添加匹配项
        for match in matches:
            self.autocomplete_listbox.insert(tk.END, match)
        
        # 选择第一项
        self.autocomplete_listbox.selection_set(0)
        
        # 绑定事件
        self.autocomplete_listbox.bind("<Double-Button-1>", lambda e: self.select_autocomplete())
        self.autocomplete_window.bind("<FocusOut>", lambda e: self.hide_autocomplete())
        
        self.autocomplete_active = True
    
    def hide_autocomplete(self):
        """隐藏自动完成列表"""
        if self.autocomplete_window and self.autocomplete_window.winfo_exists():
            self.autocomplete_window.destroy()
        
        self.autocomplete_active = False
        self.autocomplete_listbox = None
        self.autocomplete_window = None
    
    def navigate_autocomplete(self, direction):
        """在自动完成列表中导航"""
        if not self.autocomplete_listbox:
            return
        
        current_selection = self.autocomplete_listbox.curselection()
        if not current_selection:
            return
        
        current_index = current_selection[0]
        new_index = max(0, min(self.autocomplete_listbox.size() - 1, current_index + direction))
        
        self.autocomplete_listbox.selection_clear(0, tk.END)
        self.autocomplete_listbox.selection_set(new_index)
        self.autocomplete_listbox.activate(new_index)
    
    def select_autocomplete(self):
        """选择自动完成项"""
        if not self.autocomplete_listbox:
            return
        
        selection = self.autocomplete_listbox.curselection()
        if not selection:
            return
        
        selected_word = self.autocomplete_listbox.get(selection[0])
        
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        
        # 获取当前单词位置
        current_pos = text_area.index(tk.INSERT)
        line, col = current_pos.split('.')
        line_text = text_area.get(f"{line}.0", f"{line}.end")
        
        # 提取当前单词
        word_start = int(col)
        while word_start > 0 and line_text[word_start-1].isalnum():
            word_start -= 1
        
        # 替换单词
        text_area.delete(f"{line}.{word_start}", current_pos)
        text_area.insert(f"{line}.{word_start}", selected_word)
        
        self.hide_autocomplete()
    
    # 科研功能实现
    def insert_latex_equation(self):
        """插入LaTeX公式"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        
        # 创建公式输入对话框
        equation_window = tk.Toplevel(self.root)
        equation_window.title("插入LaTeX公式")
        equation_window.geometry("500x300")
        equation_window.resizable(True, True)
        equation_window.transient(self.root)
        equation_window.grab_set()
        
        ttk.Label(equation_window, text="输入LaTeX公式:").pack(pady=5)
        
        equation_text = scrolledtext.ScrolledText(equation_window, height=10)
        equation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        equation_text.focus_set()
        
        # 常用公式模板
        templates_frame = ttk.Frame(equation_window)
        templates_frame.pack(fill=tk.X, padx=5, pady=5)
        
        templates = [
            ("分数", "\\frac{分子}{分母}"),
            ("平方根", "\\sqrt{表达式}"),
            ("积分", "\\int_{下限}^{上限} 表达式 dx"),
            ("求和", "\\sum_{i=1}^{n} 表达式"),
            ("矩阵", "\\begin{bmatrix}\n  1 & 2 \\\\\n  3 & 4\n\\end{bmatrix}"),
        ]
        
        for name, template in templates:
            def insert_template(t=template):
                equation_text.insert(tk.INSERT, t)
            
            ttk.Button(templates_frame, text=name, command=insert_template, width=10).pack(side=tk.LEFT, padx=2)
        
        def insert_equation():
            equation = equation_text.get(1.0, tk.END).strip()
            if equation:
                # 插入带标签的公式
                label = f"eq:{self.equation_counter}"
                formatted_equation = f"\\begin{{equation}}\n{equation}\n\\label{{{label}}}\n\\end{{equation}}"
                text_area.insert(tk.INSERT, formatted_equation)
                self.equation_counter += 1
                equation_window.destroy()
        
        button_frame = ttk.Frame(equation_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="插入", command=insert_equation).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=equation_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def preview_latex(self):
        """预览LaTeX文档"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        content = tab_widget.text_area.get(1.0, tk.END)
        
        # 检查是否包含LaTeX内容
        if not any(cmd in content for cmd in ['\\documentclass', '\\begin{document}', '\\section']):
            messagebox.showinfo("信息", "未检测到LaTeX内容")
            return
        
        # 创建临时文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex', delete=False) as f:
            f.write(content)
            temp_file = f.name
        
        # 尝试编译LaTeX文档
        try:
            # 这里只是示例，实际需要安装LaTeX发行版
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", temp_file],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(temp_file)
            )
            
            if result.returncode == 0:
                pdf_file = temp_file.replace('.tex', '.pdf')
                if os.path.exists(pdf_file):
                    # 打开PDF文件
                    if os.name == 'nt':  # Windows
                        os.startfile(pdf_file)
                    elif os.name == 'posix':  # macOS, Linux
                        subprocess.run(["open", pdf_file] if sys.platform == "darwin" else ["xdg-open", pdf_file])
                else:
                    messagebox.showerror("错误", "PDF文件未生成")
            else:
                messagebox.showerror("错误", f"LaTeX编译失败:\n{result.stderr}")
        
        except FileNotFoundError:
            messagebox.showerror("错误", "未找到LaTeX编译器，请安装TeX Live或MiKTeX")
        
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
                for ext in ['.aux', '.log', '.out']:
                    temp_file_with_ext = temp_file.replace('.tex', ext)
                    if os.path.exists(temp_file_with_ext):
                        os.unlink(temp_file_with_ext)
            except:
                pass
    
    def insert_reference(self):
        """插入参考文献引用"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        text_area = tab_widget.text_area
        
        # 创建参考文献对话框
        ref_window = tk.Toplevel(self.root)
        ref_window.title("插入参考文献")
        ref_window.geometry("600x400")
        ref_window.resizable(True, True)
        ref_window.transient(self.root)
        ref_window.grab_set()
        
        # 参考文献列表
        ttk.Label(ref_window, text="参考文献:").pack(pady=5)
        
        ref_listbox = tk.Listbox(ref_window)
        ref_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 示例参考文献
        references = [
            "作者. 标题. 期刊, 年份, 卷(期): 页码",
            "作者. 书名. 出版社, 出版年份",
            "作者. 论文标题. 学位论文, 学校, 年份",
        ]
        
        for ref in references:
            ref_listbox.insert(tk.END, ref)
        
        def insert_reference():
            selection = ref_listbox.curselection()
            if selection:
                ref_text = ref_listbox.get(selection[0])
                label = f"ref:{self.reference_counter}"
                citation = f"\\cite{{{label}}}"
                text_area.insert(tk.INSERT, citation)
                
                # 添加到参考文献库
                if not hasattr(self, 'reference_library'):
                    self.reference_library = {}
                self.reference_library[label] = ref_text
                
                self.reference_counter += 1
                ref_window.destroy()
        
        button_frame = ttk.Frame(ref_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="插入", command=insert_reference).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", command=ref_window.destroy).pack(side=tk.RRIGHT, padx=5)
    
    def open_data_visualization(self):
        """打开数据可视化工具"""
        if self.data_visualization_frame and self.data_visualization_frame.winfo_exists():
            self.data_visualization_frame.deiconify()
            return
        
        # 创建数据可视化窗口
        self.data_visualization_frame = tk.Toplevel(self.root)
        self.data_visualization_frame.title("数据可视化")
        self.data_visualization_frame.geometry("800x600")
        
        # 创建绘图区域
        figure = plt.Figure(figsize=(6, 4), dpi=100)
        canvas = FigureCanvasTkAgg(figure, self.data_visualization_frame)
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 创建控制面板
        control_frame = ttk.Frame(self.data_visualization_frame)
        control_frame.pack(side=tk.Bottom, fill=tk.X)
        
        # 示例数据
        x = np.linspace(0, 10, 100)
        y = np.sin(x)
        
        # 绘制示例图表
        ax = figure.add_subplot(111)
        ax.plot(x, y)
        ax.set_title('正弦波')
        ax.set_xlabel('X轴')
        ax.set_ylabel('Y轴')
        
        canvas.draw()
    
    def import_data(self):
        """导入数据文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("CSV文件", "*.csv"),
                ("Excel文件", "*.xlsx"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    data = pd.read_csv(file_path)
                elif file_path.endswith('.xlsx'):
                    data = pd.read_excel(file_path)
                else:
                    data = pd.read_csv(file_path, delimiter='\t')
                
                # 显示数据基本信息
                messagebox.showinfo("数据导入成功", 
                                  f"成功导入数据:\n"
                                  f"行数: {len(data)}\n"
                                  f"列数: {len(data.columns)}\n"
                                  f"列名: {', '.join(data.columns)}")
                
                # 存储数据供后续使用
                if not hasattr(self, 'imported_data'):
                    self.imported_data = {}
                self.imported_data[os.path.basename(file_path)] = data
                
            except Exception as e:
                messagebox.showerror("错误", f"导入数据失败: {str(e)}")
    
    def open_symbolic_calculator(self):
        """打开符号计算器"""
        calc_window = tk.Toplevel(self.root)
        calc_window.title("符号计算器")
        calc_window.geometry("500x400")
        
        ttk.Label(calc_window, text="输入表达式:").pack(pady=5)
        
        expression_entry = ttk.Entry(calc_window, width=50)
        expression_entry.pack(pady=5)
        expression_entry.focus_set()
        
        ttk.Label(calc_window, text="结果:").pack(pady=5)
        
        result_text = scrolledtext.ScrolledText(calc_window, height=10)
        result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        result_text.config(state=tk.DISABLED)
        
        def calculate():
            expression = expression_entry.get()
            if not expression:
                return
            
            try:
                # 使用sympy进行符号计算
                x, y, z = sp.symbols('x y z')
                expr = sp.sympify(expression)
                
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                
                # 显示各种计算结果
                result_text.insert(tk.END, f"表达式: {expr}\n\n")
                result_text.insert(tk.END, f"简化: {sp.simplify(expr)}\n\n")
                result_text.insert(tk.END, f"展开: {sp.expand(expr)}\n\n")
                result_text.insert(tk.END, f"因式分解: {sp.factor(expr)}\n\n")
                result_text.insert(tk.END, f"求导: {sp.diff(expr, x)}\n\n")
                result_text.insert(tk.END, f"积分: {sp.integrate(expr, x)}\n\n")
                
                result_text.config(state=tk.DISABLED)
                
            except Exception as e:
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.END, f"错误: {str(e)}")
                result_text.config(state=tk.DISABLED)
        
        button_frame = ttk.Frame(calc_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="计算", command=calculate).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="清除", command=lambda: expression_entry.delete(0, tk.END)).pack(side=tk.RIGHT, padx=5)
    
    def solve_equation(self):
        """解方程"""
        eq_window = tk.Toplevel(self.root)
        eq_window.title("方程求解")
        eq_window.geometry("500x300")
        
        ttk.Label(eq_window, text="输入方程 (例如: x**2 - 4 = 0):").pack(pady=5)
        
        equation_entry = ttk.Entry(eq_window, width=50)
        equation_entry.pack(pady=5)
        equation_entry.focus_set()
        
        ttk.Label(eq_window, text="解:").pack(pady=5)
        
        solution_text = scrolledtext.ScrolledText(eq_window, height=10)
        solution_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        solution_text.config(state=tk.DISABLED)
        
        def solve():
            equation = equation_entry.get()
            if not equation:
                return
            
            try:
                # 解析方程
                x = sp.symbols('x')
                eq = sp.sympify(equation)
                
                # 求解方程
                solutions = sp.solve(eq, x)
                
                solution_text.config(state=tk.NORMAL)
                solution_text.delete(1.0, tk.END)
                
                if solutions:
                    solution_text.insert(tk.END, f"方程: {eq} = 0\n\n")
                    solution_text.insert(tk.END, f"解:\n")
                    for i, sol in enumerate(solutions):
                        solution_text.insert(tk.END, f"x{i+1} = {sol}\n")
                else:
                    solution_text.insert(tk.END, "无解或无法求解")
                
                solution_text.config(state=tk.DISABLED)
                
            except Exception as e:
                solution_text.config(state=tk.NORMAL)
                solution_text.delete(1.0, tk.END)
                solution_text.insert(tk.END, f"错误: {str(e)}")
                solution_text.config(state=tk.DISABLED)
        
        button_frame = ttk.Frame(eq_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="求解", command=solve).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="清除", command=lambda: equation_entry.delete(0, tk.END)).pack(side=tk.RIGHT, padx=5)
    
    def manage_references(self):
        """管理参考文献"""
        ref_window = tk.Toplevel(self.root)
        ref_window.title("参考文献管理")
        ref_window.geometry("700x500")
        
        # 创建参考文献列表
        ttk.Label(ref_window, text="参考文献库:").pack(pady=5)
        
        ref_listbox = tk.Listbox(ref_window)
        ref_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 加载参考文献
        if hasattr(self, 'reference_library'):
            for label, ref in self.reference_library.items():
                ref_listbox.insert(tk.END, f"{label}: {ref}")
        
        # 操作按钮
        button_frame = ttk.Frame(ref_window)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        def add_reference():
            add_window = tk.Toplevel(ref_window)
            add_window.title("添加参考文献")
            add_window.geometry("500x300")
            
            ttk.Label(add_window, text="参考文献格式:").pack(pady=5)
            
            ref_text = scrolledtext.ScrolledText(add_window, height=10)
            ref_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            ref_text.focus_set()
            
            def save_reference():
                reference = ref_text.get(1.0, tk.END).strip()
                if reference:
                    label = f"ref:{self.reference_counter}"
                    if not hasattr(self, 'reference_library'):
                        self.reference_library = {}
                    self.reference_library[label] = reference
                    ref_listbox.insert(tk.END, f"{label}: {reference}")
                    self.reference_counter += 1
                    add_window.destroy()
            
            ttk.Button(add_window, text="保存", command=save_reference).pack(side=tk.RIGHT, padx=5, pady=5)
            ttk.Button(add_window, text="取消", command=add_window.destroy).pack(side=tk.RIGHT, padx=5, pady=5)
        
        def export_references():
            file_path = filedialog.asksaveasfilename(
                defaultextension=".bib",
                filetypes=[("BibTeX文件", "*.bib"), ("所有文件", "*.*")]
            )
            
            if file_path and hasattr(self, 'reference_library'):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        for label, ref in self.reference_library.items():
                            f.write(f"@misc{{{label},\n")
                            f.write(f"  note = {{{ref}}}\n")
                            f.write("}\n\n")
                    
                    messagebox.showinfo("成功", f"参考文献已导出到: {file_path}")
                except Exception as e:
                    messagebox.showerror("错误", f"导出失败: {str(e)}")
        
        ttk.Button(button_frame, text="添加", command=add_reference).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出", command=export_references).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=ref_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def generate_bibliography(self):
        """生成参考文献列表"""
        tab_id, tab_widget = self.get_current_tab_data()
        if not tab_widget or not hasattr(tab_widget, 'text_area'):
            return
        
        if not hasattr(self, 'reference_library') or not self.reference_library:
            messagebox.showinfo("信息", "参考文献库为空")
            return
        
        text_area = tab_widget.text_area
        
        # 插入参考文献章节
        bibliography = "\n\n\\section*{参考文献}\n\\begin{thebibliography}{99}\n"
        
        for label, ref in self.reference_library.items():
            bibliography += f"\\bibitem{{{label}}} {ref}\n"
        
        bibliography += "\\end{thebibliography}"
        
        text_area.insert(tk.END, bibliography)
        messagebox.showinfo("成功", "参考文献已生成")
    
    def load_plugin(self):
        """加载插件"""
        plugin_path = filedialog.askopenfilename(
            title="选择插件文件",
            filetypes=[("Python文件", "*.py"), ("所有文件", "*.*")]
        )
        
        if plugin_path:
            try:
                # 动态加载插件模块
                spec = importlib.util.spec_from_file_location("plugin", plugin_path)
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                # 初始化插件
                plugin_name = os.path.basename(plugin_path).replace('.py', '')
                plugin_instance = plugin_module.Plugin(self)
                self.plugins[plugin_name] = plugin_instance
                
                # 添加插件菜单
                self.plugin_menu.add_command(
                    label=plugin_instance.name,
                    command=plugin_instance.execute
                )
                
                messagebox.showinfo("成功", f"插件 '{plugin_name}' 加载成功")
                
            except Exception as e:
                messagebox.showerror("错误", f"加载插件失败: {str(e)}")
    
    def manage_plugins(self):
        """管理插件"""
        manage_window = tk.Toplevel(self.root)
        manage_window.title("插件管理")
        manage_window.geometry("400x300")
        
        ttk.Label(manage_window, text="已加载的插件:").pack(pady=10)
        
        # 插件列表
        plugin_list = tk.Listbox(manage_window)
        plugin_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        for plugin_name in self.plugins:
            plugin_list.insert(tk.END, plugin_name)
        
        def remove_plugin():
            selection = plugin_list.curselection()
            if selection:
                plugin_name = plugin_list.get(selection[0])
                del self.plugins[plugin_name]
                plugin_list.delete(selection[0])
                
                # 从菜单中移除
                for i in range(self.plugin_menu.index(tk.END) + 1):
                    if self.plugin_menu.entrycget(i, 'label') == plugin_name:
                        self.plugin_menu.delete(i)
                        break
        
        button_frame = ttk.Frame(manage_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="移除插件", command=remove_plugin).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=manage_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_tutorial(self):
        """显示使用教程"""
        tutorial_text = """
        XYnote++ 使用教程
        
        1. 文件操作
          - 新建文件: Ctrl+N
          - 打开文件: Ctrl+O
          - 保存文件: Ctrl+S
          - 另存为: Ctrl+Shift+S
        
        2. 编辑功能
          - 撤销: Ctrl+Z
          - 重做: Ctrl+Y
          - 查找: Ctrl+F
          - 替换: Ctrl+H
        
        3. 科研功能
          - 插入LaTeX公式: 通过科研菜单或侧边栏
          - 数据可视化: 打开数据绘图工具
          - 符号计算: 使用符号计算器
          - 参考文献管理: 管理并生成参考文献
        
        4. 其他功能
          - 宏录制: Ctrl+Shift+R 开始, Ctrl+Shift+S 停止
          - 宏播放: Ctrl+Shift+P
          - 语法高亮: 通过语言菜单选择
        
        更多帮助请联系开发者: 蜗客小顽童 (surezx4@163.com)
        """
        
        tutorial_window = tk.Toplevel(self.root)
        tutorial_window.title("使用教程")
        tutorial_window.geometry("500x400")
        
        tutorial_text_area = scrolledtext.ScrolledText(tutorial_window, wrap=tk.WORD)
        tutorial_text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tutorial_text_area.insert(1.0, tutorial_text)
        tutorial_text_area.config(state=tk.DISABLED)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
        XYnote++ 科研文本编辑器
        
        版本 2.0
        开发者: {self.developer}
        邮箱: {self.email}
        
        基于 Python 和 Tkinter 构建的高级文本编辑器
        专为科研人员设计，支持LaTeX、数据可视化、符号计算等功能
        
        版权所有 © 2025 {self.developer}
        保留所有权利
        """
        
        about_window = tk.Toplevel(self.root)
        about_window.title("关于 XYnote++")
        about_window.geometry("400x300")
        
        about_text_area = scrolledtext.ScrolledText(about_window, wrap=tk.WORD)
        about_text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        about_text_area.insert(1.0, about_text)
        about_text_area.config(state=tk.DISABLED)
        
        # 添加关闭按钮
        ttk.Button(about_window, text="关闭", command=about_window.destroy).pack(pady=10)


class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        self.text_widget = kwargs.pop('text_widget', None)
        self.editor = kwargs.pop('editor', None)
        tk.Canvas.__init__(self, *args, **kwargs)
        self.config(width=50)
        
    def attach(self, text_widget):
        self.text_widget = text_widget
        
    def redraw(self, *args):
        """重绘行号"""
        self.delete("all")
        
        if self.text_widget:
            # 获取可见文本的行数
            i = self.text_widget.index("@0,0")
            while True:
                dline = self.text_widget.dlineinfo(i)
                if dline is None:
                    break
                y = dline[1]
                linenum = str(i).split(".")[0]
                self.create_text(40, y, anchor="ne", text=linenum, fill="#666666")
                
                # 添加折叠标记
                if self.editor:
                    line = int(linenum)
                    tab_id, tab_widget = self.editor.get_current_tab_data()
                    if tab_widget and hasattr(tab_widget, 'folding_regions'):
                        for region_id, region in tab_widget.folding_regions.items():
                            start_line = int(region['start'].split('.')[0])
                            if line == start_line:
                                # 绘制折叠标记
                                marker = "-" if region['folded'] else "+"
                                self.create_text(20, y, anchor="ne", text=marker, fill="#666666")
                                break
                
                i = self.text_widget.index("%s+1line" % i)


# 插件基类
class PluginBase:
    def __init__(self, editor):
        self.editor = editor
        self.name = "未命名插件"
        
    def execute(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    
    # 创建样式
    style = ttk.Style()
    style.configure("red.TButton", foreground="red")
    style.configure("green.TButton", foreground="green")
    
    app = XYnotePlusPlus(root)
    root.mainloop()