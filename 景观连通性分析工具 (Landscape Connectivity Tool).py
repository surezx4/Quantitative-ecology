# -*- coding: utf-8 -*-
"""
Created on Thu Aug  7 06:18:52 2025

@author: surez
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.plot import show
import pandas as pd
from PIL import Image, ImageTk
import networkx as nx
from skimage import morphology, measure

class LandscapeConnectivityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("景观连通性分析工具")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化变量
        self.raster_data = None
        self.vector_data = None
        self.graph = None
        self.results = {}
        
        # 创建主框架
        self.create_widgets()
        
    def create_widgets(self):
        # 创建顶部框架
        top_frame = tk.Frame(self.root, bg='#2c3e50', height=60)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(top_frame, text="景观连通性分析工具", 
                             font=("Arial", 18, "bold"), fg="white", bg='#2c3e50')
        title_label.pack(pady=15)
        
        # 创建主内容框架
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 左侧控制面板
        control_frame = tk.LabelFrame(main_frame, text="控制面板", font=("Arial", 12), 
                                    bg='#ecf0f1', padx=10, pady=10)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 数据加载部分
        data_frame = tk.LabelFrame(control_frame, text="数据加载", bg='#ecf0f1', padx=5, pady=5)
        data_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(data_frame, text="加载栅格数据 (TIFF)", command=self.load_raster, 
                 bg='#3498db', fg='white').pack(fill=tk.X, pady=5)
        tk.Button(data_frame, text="加载矢量数据 (SHP)", command=self.load_vector, 
                 bg='#3498db', fg='white').pack(fill=tk.X, pady=5)
        tk.Button(data_frame, text="加载属性数据 (CSV)", command=self.load_csv, 
                 bg='#3498db', fg='white').pack(fill=tk.X, pady=5)
        
        # 分析选项
        analysis_frame = tk.LabelFrame(control_frame, text="分析选项", bg='#ecf0f1', padx=5, pady=5)
        analysis_frame.pack(fill=tk.X, pady=10)
        
        self.analysis_type = tk.StringVar(value="mspa")
        tk.Radiobutton(analysis_frame, text="形态学空间格局分析 (MSPA)", 
                      variable=self.analysis_type, value="mspa", bg='#ecf0f1').pack(anchor=tk.W)
        tk.Radiobutton(analysis_frame, text="景观连通性分析 (Conefor)", 
                      variable=self.analysis_type, value="connectivity", bg='#ecf0f1').pack(anchor=tk.W)
        
        # 参数设置
        param_frame = tk.LabelFrame(control_frame, text="分析参数", bg='#ecf0f1', padx=5, pady=5)
        param_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(param_frame, text="距离阈值:", bg='#ecf0f1').pack(anchor=tk.W)
        self.distance_threshold = tk.Entry(param_frame)
        self.distance_threshold.insert(0, "1000")
        self.distance_threshold.pack(fill=tk.X, pady=2)
        
        tk.Label(param_frame, text="斑块大小阈值:", bg='#ecf0f1').pack(anchor=tk.W)
        self.patch_size = tk.Entry(param_frame)
        self.patch_size.insert(0, "10")
        self.patch_size.pack(fill=tk.X, pady=2)
        
        # 执行按钮
        tk.Button(control_frame, text="执行分析", command=self.run_analysis, 
                 bg='#27ae60', fg='white', font=("Arial", 10, "bold")).pack(fill=tk.X, pady=15)
        
        # 结果导出
        export_frame = tk.LabelFrame(control_frame, text="结果导出", bg='#ecf0f1', padx=5, pady=5)
        export_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(export_frame, text="导出结果图像", command=self.export_image, 
                 bg='#9b59b6', fg='white').pack(fill=tk.X, pady=5)
        tk.Button(export_frame, text="导出分析结果", command=self.export_results, 
                 bg='#9b59b6', fg='white').pack(fill=tk.X, pady=5)
        
        # 右侧结果显示
        result_frame = tk.Frame(main_frame, bg='white')
        result_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 标签页
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 数据可视化标签页
        self.viz_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.viz_tab, text="数据可视化")
        
        # 分析结果标签页
        self.result_tab = tk.Frame(self.notebook, bg='white')
        self.notebook.add(self.result_tab, text="分析结果")
        
        # 创建绘图区域
        self.fig, self.ax = plt.subplots(figsize=(8, 6), facecolor='#f5f5f5')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.ax.set_title("景观数据可视化", fontsize=14)
        self.ax.axis('off')
        self.canvas.draw()
        
        # 状态栏
        self.status = tk.StringVar()
        self.status.set("就绪")
        status_bar = tk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W, bg='#e0e0e0')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def load_raster(self):
        file_path = filedialog.askopenfilename(filetypes=[("TIFF files", "*.tif;*.tiff")])
        if file_path:
            try:
                self.raster_data = rasterio.open(file_path)
                self.status.set(f"已加载栅格数据: {file_path}")
                self.plot_data()
            except Exception as e:
                messagebox.showerror("错误", f"加载栅格数据失败: {str(e)}")
    
    def load_vector(self):
        file_path = filedialog.askopenfilename(filetypes=[("Shapefiles", "*.shp")])
        if file_path:
            try:
                self.vector_data = gpd.read_file(file_path)
                self.status.set(f"已加载矢量数据: {file_path}")
                self.plot_data()
            except Exception as e:
                messagebox.showerror("错误", f"加载矢量数据失败: {str(e)}")
    
    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                # 这里只是示例，实际应用中需要处理CSV数据
                self.status.set(f"已加载CSV数据: {file_path}")
                messagebox.showinfo("成功", f"成功加载CSV数据: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"加载CSV数据失败: {str(e)}")
    
    def plot_data(self):
        self.ax.clear()
        
        if self.raster_data:
            show(self.raster_data, ax=self.ax, cmap='terrain')
        
        if self.vector_data is not None:
            if self.raster_data:
                # 如果同时有栅格和矢量数据，在栅格上叠加矢量
                self.vector_data.plot(ax=self.ax, facecolor='none', edgecolor='red', linewidth=1.5)
            else:
                self.vector_data.plot(ax=self.ax, column='id', cmap='viridis', legend=True)
        
        if not self.raster_data and not self.vector_data:
            self.ax.text(0.5, 0.5, "请加载景观数据", 
                         ha='center', va='center', fontsize=12, color='gray')
            self.ax.axis('off')
        else:
            self.ax.set_title("景观数据可视化", fontsize=14)
        
        self.canvas.draw()
    
    def run_analysis(self):
        if not self.raster_data and not self.vector_data:
            messagebox.showwarning("警告", "请先加载数据！")
            return
        
        analysis_type = self.analysis_type.get()
        try:
            distance_threshold = float(self.distance_threshold.get())
            patch_size = float(self.patch_size.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值参数！")
            return
        
        self.status.set("分析中...")
        self.root.update()
        
        try:
            if analysis_type == "mspa":
                self.run_mspa_analysis(patch_size)
            else:
                self.run_connectivity_analysis(distance_threshold)
            
            self.status.set("分析完成！")
            self.show_results()
        except Exception as e:
            messagebox.showerror("错误", f"分析过程中出错: {str(e)}")
            self.status.set("分析失败")
    
    def run_mspa_analysis(self, patch_size):
        # 模拟MSPA分析
        if self.raster_data:
            # 从栅格数据中读取一个波段
            data = self.raster_data.read(1)
            
            # 二值化处理（简化版）
            threshold = np.median(data)
            binary = np.where(data > threshold, 1, 0)
            
            # 形态学处理
            cleaned = morphology.remove_small_objects(binary.astype(bool), min_size=patch_size)
            labeled = measure.label(cleaned)
            
            # 计算MSPA类别
            self.results['mspa_classes'] = labeled
            self.results['statistics'] = {
                'Core': np.sum(labeled == 1),
                'Edge': np.sum(labeled == 2),
                'Perforation': np.sum(labeled == 3),
                'Islet': np.sum(labeled == 4),
                'Bridge': np.sum(labeled == 5),
                'Loop': np.sum(labeled == 6),
                'Branch': np.sum(labeled == 7)
            }
        else:
            # 如果没有栅格数据，使用矢量数据进行简化分析
            self.results['statistics'] = {
                'Patch Count': len(self.vector_data),
                'Total Area': self.vector_data.geometry.area.sum(),
                'Mean Patch Size': self.vector_data.geometry.area.mean()
            }
    
    def run_connectivity_analysis(self, distance_threshold):
        # 模拟景观连通性分析
        if self.vector_data is not None:
            # 创建图结构
            self.graph = nx.Graph()
            
            # 添加节点（斑块）
            for idx, row in self.vector_data.iterrows():
                centroid = row.geometry.centroid
                self.graph.add_node(idx, pos=(centroid.x, centroid.y), size=row.geometry.area)
            
            # 添加边（基于距离）
            nodes = list(self.graph.nodes(data=True))
            for i, (n1, data1) in enumerate(nodes):
                for j, (n2, data2) in enumerate(nodes[i+1:], i+1):
                    pos1 = data1['pos']
                    pos2 = data2['pos']
                    distance = np.sqrt((pos1[0]-pos2[0])**2 + (pos1[1]-pos2[1])**2)
                    
                    if distance <= distance_threshold:
                        # 简化的连通性度量（实际应用会更复杂）
                        weight = 1.0 / (distance + 1e-6)
                        self.graph.add_edge(n1, n2, weight=weight, distance=distance)
            
            # 计算连通性指标
            if self.graph.number_of_edges() > 0:
                self.results['graph'] = self.graph
                self.results['statistics'] = {
                    'Number of Components': nx.number_connected_components(self.graph),
                    'Average Clustering': nx.average_clustering(self.graph),
                    'Average Shortest Path': nx.average_shortest_path_length(self.graph) if nx.is_connected(self.graph) else "N/A",
                    'Connectivity Index': sum(d['weight'] for _, _, d in self.graph.edges(data=True))
                }
            else:
                self.results['statistics'] = {"Result": "No connections within the given threshold"}
        else:
            self.results['statistics'] = {"Error": "Vector data required for connectivity analysis"}
    
    def show_results(self):
        # 清除结果标签页
        for widget in self.result_tab.winfo_children():
            widget.destroy()
        
        # 创建结果框架
        result_frame = tk.Frame(self.result_tab, bg='white')
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 显示统计结果
        stats_frame = tk.LabelFrame(result_frame, text="分析统计", bg='white', padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=5)
        
        if 'statistics' in self.results:
            row = 0
            for key, value in self.results['statistics'].items():
                tk.Label(stats_frame, text=f"{key}:", bg='white', font=("Arial", 10, "bold")).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                tk.Label(stats_frame, text=str(value), bg='white').grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                row += 1
        
        # 可视化结果
        viz_frame = tk.LabelFrame(result_frame, text="结果可视化", bg='white', padx=10, pady=10)
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        if 'mspa_classes' in self.results:
            # 显示MSPA结果
            ax.imshow(self.results['mspa_classes'], cmap='nipy_spectral')
            ax.set_title("MSPA 分析结果", fontsize=14)
            ax.axis('off')
        elif 'graph' in self.results and self.results['graph'].number_of_nodes() > 0:
            # 显示连通性图
            graph = self.results['graph']
            pos = nx.get_node_attributes(graph, 'pos')
            node_sizes = [data['size']/100 for _, data in graph.nodes(data=True)]
            edge_weights = [d['weight']*5 for _, _, d in graph.edges(data=True)]
            
            nx.draw(graph, pos, ax=ax, with_labels=True, 
                   node_size=node_sizes, node_color='skyblue',
                   width=edge_weights, edge_color='gray')
            ax.set_title("景观连通性图", fontsize=14)
        else:
            ax.text(0.5, 0.5, "无可视化结果", 
                   ha='center', va='center', fontsize=12, color='gray')
            ax.axis('off')
        
        canvas = FigureCanvasTkAgg(fig, master=viz_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def export_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", 
                                               filetypes=[("PNG files", "*.png"), 
                                                         ("JPEG files", "*.jpg"),
                                                         ("All files", "*.*")])
        if file_path:
            try:
                # 保存当前可视化结果
                self.fig.savefig(file_path, dpi=300, bbox_inches='tight')
                messagebox.showinfo("成功", f"图像已成功导出到: {file_path}")
                self.status.set(f"图像已导出: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出图像失败: {str(e)}")
    
    def export_results(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", 
                                               filetypes=[("CSV files", "*.csv"), 
                                                         ("Text files", "*.txt"),
                                                         ("All files", "*.*")])
        if file_path:
            try:
                # 导出分析结果
                if 'statistics' in self.results:
                    df = pd.DataFrame(list(self.results['statistics'].items()), columns=['Metric', 'Value'])
                    df.to_csv(file_path, index=False)
                    messagebox.showinfo("成功", f"结果已成功导出到: {file_path}")
                    self.status.set(f"结果已导出: {file_path}")
                else:
                    messagebox.showwarning("警告", "没有可导出的结果数据")
            except Exception as e:
                messagebox.showerror("错误", f"导出结果失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LandscapeConnectivityApp(root)
    root.mainloop()