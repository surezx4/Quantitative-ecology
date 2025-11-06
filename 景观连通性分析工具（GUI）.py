# -*- coding: utf-8 -*-
"""
Created on Wed Aug  6 22:55:14 2025

@author: surez
"""


import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class LandscapeConnectivityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("景观连通性分析工具")
        self.root.geometry("1000x700")
        
        self.create_widgets()
        self.data = None
        self.distance_matrix = None
        self.probability_matrix = None
        
    def create_widgets(self):
        # 菜单栏
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="打开文件", command=self.load_file)
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        self.root.config(menu=menubar)
        
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧控制面板
        control_frame = tk.Frame(main_frame, width=250, relief=tk.RIDGE, borderwidth=2)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        
        tk.Label(control_frame, text="分析参数", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # 距离阈值
        tk.Label(control_frame, text="最大距离阈值:").pack(anchor=tk.W)
        self.distance_threshold = tk.Entry(control_frame)
        self.distance_threshold.insert(0, "1000")
        self.distance_threshold.pack(fill=tk.X, padx=5, pady=5)
        
        # 扩散概率
        tk.Label(control_frame, text="扩散概率参数:").pack(anchor=tk.W)
        self.dispersion_param = tk.Entry(control_frame)
        self.dispersion_param.insert(0, "0.5")
        self.dispersion_param.pack(fill=tk.X, padx=5, pady=5)
        
        # 分析按钮
        tk.Button(control_frame, text="计算连通性", command=self.analyze_connectivity, 
                 bg="#4CAF50", fg="white").pack(pady=10, fill=tk.X)
        
        # 结果显示区域
        self.result_text = tk.Text(control_frame, height=10, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 右侧可视化区域
        viz_frame = tk.Frame(main_frame, relief=tk.RIDGE, borderwidth=2)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.figure = plt.figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status = tk.StringVar()
        self.status.set("准备就绪")
        tk.Label(self.root, textvariable=self.status, bd=1, relief=tk.SUNKEN, anchor=tk.W).pack(side=tk.BOTTOM, fill=tk.X)
    
    def load_file(self):
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.data = pd.read_csv(file_path)
                else:
                    self.data = pd.read_excel(file_path)
                self.status.set(f"已加载文件: {file_path.split('/')[-1]}")
                self.show_data_preview()
            except Exception as e:
                messagebox.showerror("错误", f"加载文件失败: {str(e)}")
    
    def show_data_preview(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if 'X' in self.data.columns and 'Y' in self.data.columns:
            ax.scatter(self.data['X'], self.data['Y'], s=self.data.get('Area', 50))
            ax.set_title("景观斑块分布")
            ax.set_xlabel("X坐标")
            ax.set_ylabel("Y坐标")
            
            for i, row in self.data.iterrows():
                ax.annotate(row.get('PatchID', i+1), (row['X'], row['Y']))
        else:
            ax.text(0.5, 0.5, "数据预览不可用\n请确保包含X/Y坐标列", 
                   ha='center', va='center')
        
        self.canvas.draw()
    
    def analyze_connectivity(self):
        if self.data is None:
            messagebox.showwarning("警告", "请先加载数据文件")
            return
        
        try:
            max_distance = float(self.distance_threshold.get())
            alpha = float(self.dispersion_param.get())
            
            # 计算距离矩阵
            coords = self.data[['X', 'Y']].values
            self.distance_matrix = self.calculate_distance_matrix(coords)
            
            # 计算概率矩阵
            self.probability_matrix = np.exp(-alpha * self.distance_matrix)
            self.probability_matrix[self.distance_matrix > max_distance] = 0
            np.fill_diagonal(self.probability_matrix, 0)
            
            # 计算连通性指标
            IIC = self.calculate_IIC(self.probability_matrix)
            PC = self.calculate_PC(self.probability_matrix, self.data['Area'].values)
            
            # 显示结果
            self.show_results(IIC, PC)
            self.visualize_connectivity()
            
        except ValueError as e:
            messagebox.showerror("错误", f"参数错误: {str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"分析失败: {str(e)}")
    
    def calculate_distance_matrix(self, coords):
        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        return np.sqrt(np.sum(diff**2, axis=-1))
    
    def calculate_IIC(self, prob_matrix):
        return np.sum(prob_matrix) / (prob_matrix.shape[0]**2)
    
    def calculate_PC(self, prob_matrix, areas):
        total_area = np.sum(areas)
        a_ij = np.outer(areas, areas) / (total_area**2)
        return np.sum(a_ij * prob_matrix)
    
    def show_results(self, IIC, PC):
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        results = f"""连通性分析结果:
-------------------------
斑块数量: {len(self.data)}
最大距离阈值: {self.distance_threshold.get()}
扩散参数: {self.dispersion_param.get()}

整体连通性指数 (IIC): {IIC:.4f}
概率连通性指数 (PC): {PC:.4f}
"""
        self.result_text.insert(tk.END, results)
        self.result_text.config(state=tk.DISABLED)
    
    def visualize_connectivity(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        coords = self.data[['X', 'Y']].values
        ax.scatter(coords[:,0], coords[:,1], s=self.data['Area']/10)
        
        # 绘制连接线
        for i in range(len(coords)):
            for j in range(i+1, len(coords)):
                if self.probability_matrix[i,j] > 0:
                    ax.plot([coords[i,0], coords[j,0]], 
                           [coords[i,1], coords[j,1]], 
                           'b-', alpha=self.probability_matrix[i,j], 
                           linewidth=self.probability_matrix[i,j]*3)
        
        ax.set_title("景观连通性网络")
        ax.set_xlabel("X坐标")
        ax.set_ylabel("Y坐标")
        
        for i, row in self.data.iterrows():
            ax.annotate(row.get('PatchID', i+1), (row['X'], row['Y']))
        
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = LandscapeConnectivityApp(root)
    root.mainloop()
