# -*- coding: utf-8 -*-
"""
Created on Wed Aug 13 17:24:45 2025

@author: 10681
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import igraph as ig
from igraph.drawing.colors import GradientPalette
import numpy as np
from PIL import Image, ImageTk
import os

class IgraphGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("igraph图形分析工具")
        self.geometry("1200x800")
        self.current_graph = None
        self.current_layout = None
        self.image = None
        self.photo_image = None
        
        # 设置中文字体支持
        self.style = ttk.Style()
        self.style.configure(".", font=("SimHei", 10))
        
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()
        
    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建图形", command=self.new_graph)
        file_menu.add_separator()
        file_menu.add_command(label="导入图形...", command=self.import_graph)
        file_menu.add_command(label="导出图形...", command=self.export_graph)
        file_menu.add_separator()
        file_menu.add_command(label="导入数据...", command=self.import_data)
        file_menu.add_command(label="导出数据...", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="添加顶点", command=self.add_vertex)
        edit_menu.add_command(label="添加边", command=self.add_edge)
        edit_menu.add_command(label="删除顶点", command=self.delete_vertex)
        edit_menu.add_command(label="删除边", command=self.delete_edge)
        edit_menu.add_separator()
        edit_menu.add_command(label="清空图形", command=self.clear_graph)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        
        # 分析菜单
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="计算度分布", command=self.calculate_degree_distribution)
        analysis_menu.add_command(label="计算最短路径", command=self.calculate_shortest_path)
        analysis_menu.add_command(label="社区检测", command=self.community_detection)
        analysis_menu.add_command(label="图形属性", command=self.show_graph_properties)
        menubar.add_cascade(label="分析", menu=analysis_menu)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        self.layout_var = tk.StringVar(value="kamada_kawai")
        layouts = ["kamada_kawai", "fr", "circle", "drl", "grid", "random"]
        for layout in layouts:
            view_menu.add_radiobutton(label=layout, variable=self.layout_var, 
                                     value=layout, command=self.redraw_graph)
        
        view_menu.add_separator()
        self.vertex_color_var = tk.StringVar(value="blue")
        vertex_colors = ["blue", "red", "green", "purple", "orange", "gray"]
        for color in vertex_colors:
            view_menu.add_radiobutton(label=color, variable=self.vertex_color_var, 
                                     value=color, command=self.redraw_graph)
        
        menubar.add_cascade(label="视图", menu=view_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        help_menu.add_command(label="帮助", command=self.show_help)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.config(menu=menubar)
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(toolbar, text="新建", command=self.new_graph).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导入", command=self.import_graph).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="导出", command=self.export_graph).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="添加顶点", command=self.add_vertex).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="添加边", command=self.add_edge).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        ttk.Button(toolbar, text="分析", command=self.show_graph_properties).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="社区检测", command=self.community_detection).pack(side=tk.LEFT, padx=2)
    
    def _create_main_layout(self):
        """创建主布局"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧图形显示区域
        self.graph_frame = ttk.LabelFrame(main_frame, text="图形显示", padding="10")
        self.graph_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.graph_canvas = tk.Canvas(self.graph_frame, bg="white")
        self.graph_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 右侧属性面板
        self.properties_frame = ttk.LabelFrame(main_frame, text="属性面板", padding="10")
        self.properties_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 图形信息
        ttk.Label(self.properties_frame, text="图形信息:").pack(anchor=tk.W, pady=(0, 5))
        self.graph_info = tk.Text(self.properties_frame, height=10, width=30, state=tk.DISABLED)
        self.graph_info.pack(fill=tk.X, pady=(0, 10))
        
        # 顶点列表
        ttk.Label(self.properties_frame, text="顶点:").pack(anchor=tk.W, pady=(0, 5))
        self.vertices_list = tk.Listbox(self.properties_frame, height=10, width=30)
        self.vertices_list.pack(fill=tk.X, pady=(0, 10))
        
        # 边列表
        ttk.Label(self.properties_frame, text="边:").pack(anchor=tk.W, pady=(0, 5))
        self.edges_list = tk.Listbox(self.properties_frame, height=10, width=30)
        self.edges_list.pack(fill=tk.X)
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def new_graph(self):
        """创建新图形"""
        try:
            num_vertices = simpledialog.askinteger("新建图形", "请输入顶点数量:", minvalue=1)
            if num_vertices is None:
                return
                
            self.current_graph = ig.Graph(directed=False)
            self.current_graph.add_vertices(num_vertices)
            self.status_var.set(f"已创建新图形，包含 {num_vertices} 个顶点")
            self.update_graph_info()
            self.redraw_graph()
        except Exception as e:
            messagebox.showerror("错误", f"创建新图形失败: {str(e)}")
    
    def import_graph(self):
        """导入图形文件"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("GML文件", "*.gml"),
                    ("GraphML文件", "*.graphml"),
                    ("Pajek文件", "*.net"),
                    ("LGL文件", "*.lgl"),
                    ("所有支持的文件", "*.[gml|graphml|net|lgl]"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            self.current_graph = ig.load(file_path)
            self.status_var.set(f"已导入图形: {os.path.basename(file_path)}")
            self.update_graph_info()
            self.redraw_graph()
        except Exception as e:
            messagebox.showerror("错误", f"导入图形失败: {str(e)}")
    
    def export_graph(self):
        """导出图形文件"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "没有可导出的图形")
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".gml",
                filetypes=[
                    ("GML文件", "*.gml"),
                    ("GraphML文件", "*.graphml"),
                    ("Pajek文件", "*.net"),
                    ("LGL文件", "*.lgl"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            self.current_graph.save(file_path)
            self.status_var.set(f"已导出图形: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"导出图形失败: {str(e)}")
    
    def import_data(self):
        """导入数据创建图形"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("CSV文件", "*.csv"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            # 尝试从边列表创建图形
            edges = []
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            u = int(parts[0])
                            v = int(parts[1])
                            edges.append((u, v))
                        except ValueError:
                            pass
            
            if edges:
                # 找到最大顶点编号
                max_vertex = max(max(u, v) for u, v in edges)
                self.current_graph = ig.Graph(directed=False)
                self.current_graph.add_vertices(max_vertex + 1)
                self.current_graph.add_edges(edges)
                
                self.status_var.set(f"已从数据文件创建图形: {os.path.basename(file_path)}")
                self.update_graph_info()
                self.redraw_graph()
            else:
                messagebox.showwarning("警告", "无法从文件中解析有效的边数据")
        except Exception as e:
            messagebox.showerror("错误", f"导入数据失败: {str(e)}")
    
    def export_data(self):
        """导出图形数据"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "没有可导出的数据")
            return
            
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[
                    ("文本文件", "*.txt"),
                    ("CSV文件", "*.csv"),
                    ("所有文件", "*.*")
                ]
            )
            
            if not file_path:
                return
                
            # 导出边列表
            with open(file_path, 'w') as f:
                for edge in self.current_graph.get_edgelist():
                    f.write(f"{edge[0]} {edge[1]}\n")
            
            self.status_var.set(f"已导出图形数据: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"导出数据失败: {str(e)}")
    
    def add_vertex(self):
        """添加顶点"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        try:
            self.current_graph.add_vertex()
            self.status_var.set(f"已添加顶点，当前顶点数: {self.current_graph.vcount()}")
            self.update_graph_info()
            self.redraw_graph()
        except Exception as e:
            messagebox.showerror("错误", f"添加顶点失败: {str(e)}")
    
    def add_edge(self):
        """添加边"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        if self.current_graph.vcount() < 2:
            messagebox.showwarning("警告", "至少需要2个顶点才能添加边")
            return
            
        try:
            u = simpledialog.askinteger("添加边", "请输入起点顶点编号:")
            if u is None:
                return
                
            v = simpledialog.askinteger("添加边", "请输入终点顶点编号:")
            if v is None:
                return
                
            if u < 0 or u >= self.current_graph.vcount() or v < 0 or v >= self.current_graph.vcount():
                messagebox.showwarning("警告", "顶点编号超出范围")
                return
                
            self.current_graph.add_edge(u, v)
            self.status_var.set(f"已添加边 ({u}, {v})")
            self.update_graph_info()
            self.redraw_graph()
        except Exception as e:
            messagebox.showerror("错误", f"添加边失败: {str(e)}")
    
    def delete_vertex(self):
        """删除顶点"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        if self.current_graph.vcount() == 0:
            messagebox.showwarning("警告", "没有顶点可删除")
            return
            
        try:
            v = simpledialog.askinteger("删除顶点", "请输入要删除的顶点编号:")
            if v is None:
                return
                
            if v < 0 or v >= self.current_graph.vcount():
                messagebox.showwarning("警告", "顶点编号超出范围")
                return
                
            self.current_graph.delete_vertices(v)
            self.status_var.set(f"已删除顶点 {v}")
            self.update_graph_info()
            self.redraw_graph()
        except Exception as e:
            messagebox.showerror("错误", f"删除顶点失败: {str(e)}")
    
    def delete_edge(self):
        """删除边"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        if self.current_graph.ecount() == 0:
            messagebox.showwarning("警告", "没有边可删除")
            return
            
        try:
            u = simpledialog.askinteger("删除边", "请输入起点顶点编号:")
            if u is None:
                return
                
            v = simpledialog.askinteger("删除边", "请输入终点顶点编号:")
            if v is None:
                return
                
            edge_id = self.current_graph.get_eid(u, v, directed=False, error=False)
            if edge_id == -1:
                messagebox.showwarning("警告", f"边 ({u}, {v}) 不存在")
                return
                
            self.current_graph.delete_edges(edge_id)
            self.status_var.set(f"已删除边 ({u}, {v})")
            self.update_graph_info()
            self.redraw_graph()
        except Exception as e:
            messagebox.showerror("错误", f"删除边失败: {str(e)}")
    
    def clear_graph(self):
        """清空图形"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "没有图形可清空")
            return
            
        if messagebox.askyesno("确认", "确定要清空当前图形吗?"):
            self.current_graph = None
            self.graph_canvas.delete("all")
            self.update_graph_info()
            self.status_var.set("已清空图形")
    
    def redraw_graph(self):
        """重绘图形"""
        if self.current_graph is None:
            return
            
        try:
            # 清除画布
            self.graph_canvas.delete("all")
            
            # 获取画布尺寸
            canvas_width = self.graph_canvas.winfo_width() or 800
            canvas_height = self.graph_canvas.winfo_height() or 600
            
            # 创建图形布局
            layout_name = self.layout_var.get()
            if self.current_layout is None or layout_name != self.current_layout:
                self.current_layout = layout_name
                layout = self.current_graph.layout(layout_name)
            else:
                layout = self.current_graph.layout(self.current_layout)
            
            # 创建绘图参数
            visual_style = {
                "layout": layout,
                "bbox": (canvas_width - 40, canvas_height - 40),
                "margin": 20,
                "vertex_color": self.vertex_color_var.get(),
                "vertex_size": 20,
                "vertex_label_size": 12,
                "edge_width": 2,
                "bbox_version": 1,
            }
            
            # 绘制图形到图像
            self.image = self.current_graph.plot(**visual_style)
            
            # 转换为Tkinter可用的图像
            self.photo_image = ImageTk.PhotoImage(image=self.image)
            
            # 在画布上显示图像
            self.graph_canvas.create_image(canvas_width//2, canvas_height//2, image=self.photo_image)
            
            self.status_var.set(f"已绘制图形，布局: {layout_name}")
        except Exception as e:
            messagebox.showerror("错误", f"绘制图形失败: {str(e)}")
    
    def update_graph_info(self):
        """更新图形信息面板"""
        # 清空列表
        self.vertices_list.delete(0, tk.END)
        self.edges_list.delete(0, tk.END)
        self.graph_info.config(state=tk.NORMAL)
        self.graph_info.delete(1.0, tk.END)
        
        if self.current_graph is None:
            self.graph_info.insert(tk.END, "没有图形数据")
            self.graph_info.config(state=tk.DISABLED)
            return
        
        # 更新图形信息
        info = f"顶点数: {self.current_graph.vcount()}\n"
        info += f"边数: {self.current_graph.ecount()}\n"
        info += f"是否有向: {self.current_graph.is_directed()}\n"
        info += f"连通分量数: {self.current_graph.components().count()}\n"
        info += f"平均度: {np.mean(self.current_graph.degree()):.2f}\n"
        
        self.graph_info.insert(tk.END, info)
        self.graph_info.config(state=tk.DISABLED)
        
        # 更新顶点列表
        for i in range(self.current_graph.vcount()):
            self.vertices_list.insert(tk.END, f"顶点 {i}: 度 = {self.current_graph.degree(i)}")
        
        # 更新边列表
        edges = self.current_graph.get_edgelist()
        for i, (u, v) in enumerate(edges):
            self.edges_list.insert(tk.END, f"边 {i}: ({u}, {v})")
    
    def calculate_degree_distribution(self):
        """计算度分布"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        try:
            degrees = self.current_graph.degree()
            max_degree = max(degrees) if degrees else 0
            dist = [0] * (max_degree + 1)
            
            for d in degrees:
                dist[d] += 1
            
            # 创建结果窗口
            result_window = tk.Toplevel(self)
            result_window.title("度分布")
            result_window.geometry("600x400")
            
            # 创建文本区域显示结果
            text_area = tk.Text(result_window)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_area.insert(tk.END, "度分布:\n")
            text_area.insert(tk.END, "度 -> 顶点数\n")
            text_area.insert(tk.END, "-" * 20 + "\n")
            
            for d, count in enumerate(dist):
                if count > 0:
                    text_area.insert(tk.END, f"{d} -> {count}\n")
            
            text_area.config(state=tk.DISABLED)
            self.status_var.set("已计算度分布")
        except Exception as e:
            messagebox.showerror("错误", f"计算度分布失败: {str(e)}")
    
    def calculate_shortest_path(self):
        """计算最短路径"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        if self.current_graph.vcount() < 2:
            messagebox.showwarning("警告", "至少需要2个顶点才能计算最短路径")
            return
            
        try:
            u = simpledialog.askinteger("最短路径", "请输入起点顶点编号:")
            if u is None:
                return
                
            v = simpledialog.askinteger("最短路径", "请输入终点顶点编号:")
            if v is None:
                return
                
            if u < 0 or u >= self.current_graph.vcount() or v < 0 or v >= self.current_graph.vcount():
                messagebox.showwarning("警告", "顶点编号超出范围")
                return
            
            # 计算最短路径
            path = self.current_graph.get_shortest_paths(u, to=v, output="vpath")[0]
            distance = len(path) - 1 if path else -1
            
            # 显示结果
            result_window = tk.Toplevel(self)
            result_window.title("最短路径")
            result_window.geometry("400x300")
            
            text_area = tk.Text(result_window)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            if distance == -1:
                text_area.insert(tk.END, f"顶点 {u} 和 {v} 之间没有路径")
            else:
                text_area.insert(tk.END, f"顶点 {u} 到 {v} 的最短路径:\n")
                text_area.insert(tk.END, " -> ".join(map(str, path)) + "\n")
                text_area.insert(tk.END, f"\n路径长度: {distance}")
            
            text_area.config(state=tk.DISABLED)
            self.status_var.set(f"已计算顶点 {u} 到 {v} 的最短路径")
        except Exception as e:
            messagebox.showerror("错误", f"计算最短路径失败: {str(e)}")
    
    def community_detection(self):
        """社区检测"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        if self.current_graph.ecount() == 0:
            messagebox.showwarning("警告", "图形中没有边，无法进行社区检测")
            return
            
        try:
            # 使用快速贪心算法进行社区检测
            communities = self.current_graph.community_fastgreedy().as_clustering()
            
            # 创建结果窗口
            result_window = tk.Toplevel(self)
            result_window.title("社区检测结果")
            result_window.geometry("600x400")
            
            # 显示社区信息
            text_area = tk.Text(result_window)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text_area.insert(tk.END, f"检测到 {len(communities)} 个社区:\n\n")
            for i, community in enumerate(communities):
                text_area.insert(tk.END, f"社区 {i}: {community}\n")
            
            text_area.config(state=tk.DISABLED)
            
            # 重新绘制图形，按社区着色
            palette = GradientPalette("#e41a1c", "#4daf4a")
            colors = [palette.get(i / len(communities)) for i in communities.membership]
            
            # 获取画布尺寸
            canvas_width = self.graph_canvas.winfo_width() or 800
            canvas_height = self.graph_canvas.winfo_height() or 600
            
            # 创建绘图参数
            visual_style = {
                "layout": self.current_graph.layout(self.layout_var.get()),
                "bbox": (canvas_width - 40, canvas_height - 40),
                "margin": 20,
                "vertex_color": colors,
                "vertex_size": 20,
                "vertex_label_size": 12,
                "edge_width": 2,
                "bbox_version": 1,
            }
            
            # 绘制图形
            self.image = self.current_graph.plot(** visual_style)
            self.photo_image = ImageTk.PhotoImage(image=self.image)
            self.graph_canvas.delete("all")
            self.graph_canvas.create_image(canvas_width//2, canvas_height//2, image=self.photo_image)
            
            self.status_var.set("已完成社区检测")
        except Exception as e:
            messagebox.showerror("错误", f"社区检测失败: {str(e)}")
    
    def show_graph_properties(self):
        """显示图形属性"""
        if self.current_graph is None:
            messagebox.showwarning("警告", "请先创建或导入一个图形")
            return
            
        try:
            # 计算各种图形属性
            properties = {}
            properties["顶点数"] = self.current_graph.vcount()
            properties["边数"] = self.current_graph.ecount()
            properties["是否有向"] = "是" if self.current_graph.is_directed() else "否"
            properties["是否加权"] = "是" if self.current_graph.is_weighted() else "否"
            properties["连通分量数"] = self.current_graph.components().count()
            
            if self.current_graph.vcount() > 0:
                degrees = self.current_graph.degree()
                properties["平均度"] = f"{np.mean(degrees):.2f}"
                properties["最大度"] = max(degrees)
                properties["最小度"] = min(degrees)
            
            if self.current_graph.ecount() > 0 and self.current_graph.vcount() > 1:
                properties["平均路径长度"] = f"{self.current_graph.average_path_length():.2f}"
                properties["直径"] = self.current_graph.diameter()
                properties["聚类系数"] = f"{self.current_graph.transitivity_undirected():.4f}"
            
            # 创建结果窗口
            result_window = tk.Toplevel(self)
            result_window.title("图形属性")
            result_window.geometry("400x400")
            
            # 显示属性
            text_area = tk.Text(result_window)
            text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            for prop, value in properties.items():
                text_area.insert(tk.END, f"{prop}: {value}\n\n")
            
            text_area.config(state=tk.DISABLED)
            self.status_var.set("已显示图形属性")
        except Exception as e:
            messagebox.showerror("错误", f"获取图形属性失败: {str(e)}")
    
    def show_about(self):
        """显示关于信息"""
        about_text = """igraph图形分析工具 v1.0
整合了igraph库的主要功能
支持图形的创建、编辑、分析和可视化
具有数据导入导出功能

使用说明:
- 通过文件菜单可以新建、导入和导出图形
- 通过编辑菜单可以添加或删除顶点和边
- 通过分析菜单可以进行各种图形分析
- 通过视图菜单可以更改图形的显示方式
"""
        messagebox.showinfo("关于", about_text)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """igraph图形分析工具 使用帮助

基本操作:
1. 创建新图形: 文件 -> 新建图形
2. 导入图形: 文件 -> 导入图形
3. 导出图形: 文件 -> 导出图形
4. 导入数据: 文件 -> 导入数据 (边列表格式)
5. 导出数据: 文件 -> 导出数据 (边列表格式)

编辑功能:
1. 添加顶点: 编辑 -> 添加顶点
2. 添加边: 编辑 -> 添加边
3. 删除顶点: 编辑 -> 删除顶点
4. 删除边: 编辑 -> 删除边

分析功能:
1. 度分布: 分析 -> 计算度分布
2. 最短路径: 分析 -> 计算最短路径
3. 社区检测: 分析 -> 社区检测
4. 图形属性: 分析 -> 图形属性

视图设置:
1. 布局选择: 视图菜单中选择不同的布局算法
2. 顶点颜色: 视图菜单中选择顶点颜色
"""
        messagebox.showinfo("帮助", help_text)

if __name__ == "__main__":
    # 确保中文显示正常
    app = IgraphGUI()
    app.mainloop()
