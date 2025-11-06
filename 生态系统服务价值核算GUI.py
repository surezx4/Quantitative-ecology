import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import pandas as pd
import numpy as np
import os
import datetime

# 设置全局样式
plt.rcParams['font.family'] = 'SimHei'
plt.rcParams['axes.unicode_minus'] = False

class EcosystemServiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("生态系统服务评估与经济价值分析系统")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f8ff')
        
        # 初始化模型数据
        self.current_project = None
        self.ecosystem_data = {}
        self.model_results = {}
        self.economic_values = {}
        
        # 生态系统服务分类
        self.service_categories = [
            "维持生物多样性", "调节洪水", "补充地下水", "保土造陆",
            "消浪护岸", "净化水质", "固碳释氧", "调节气候",
            "食物生产", "原料生产", "用水供给", "游娱休疗", "科普宣教"
        ]
        
        # 创建主界面
        self.create_widgets()
        
        # 设置状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 设置示例数据
        self.set_sample_data()
        
    def create_widgets(self):
        # 创建菜单栏
        self.create_menu()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧面板
        left_panel = ttk.LabelFrame(main_frame, text="项目控制", width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), pady=5)
        
        # 项目信息
        ttk.Label(left_panel, text="项目名称:").grid(row=0, column=0, sticky=tk.W, pady=(10, 0))
        self.project_name = ttk.Entry(left_panel, width=25)
        self.project_name.grid(row=0, column=1, sticky=tk.W, pady=(10, 0), padx=5)
        
        ttk.Label(left_panel, text="评估区域:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.project_area = ttk.Entry(left_panel, width=25)
        self.project_area.grid(row=1, column=1, sticky=tk.W, pady=(5, 0), padx=5)
        
        ttk.Label(left_panel, text="项目描述:").grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.project_desc = tk.Text(left_panel, width=25, height=5)
        self.project_desc.grid(row=3, column=0, columnspan=2, padx=5, pady=(0, 10))
        
        # 数据导入按钮
        ttk.Button(left_panel, text="导入生态系统数据", command=self.import_ecosystem_data).grid(row=4, column=0, columnspan=2, pady=5, padx=10, sticky=tk.EW)
        
        # 模型选择
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).grid(row=5, column=0, columnspan=2, pady=10, sticky=tk.EW)
        ttk.Label(left_panel, text="选择评估模型:").grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.model_var = tk.StringVar()
        self.model_combobox = ttk.Combobox(left_panel, textvariable=self.model_var, width=22)
        self.model_combobox['values'] = self.service_categories
        self.model_combobox.grid(row=7, column=0, columnspan=2, pady=5, padx=10, sticky=tk.EW)
        self.model_combobox.current(0)
        
        # 运行按钮
        ttk.Button(left_panel, text="运行模型", command=self.run_model, style="Accent.TButton").grid(row=8, column=0, columnspan=2, pady=10, padx=10, sticky=tk.EW)
        
        # 经济价值按钮
        ttk.Button(left_panel, text="计算经济价值", command=self.calculate_economic_value, style="Accent.TButton").grid(row=9, column=0, columnspan=2, pady=10, padx=10, sticky=tk.EW)
        
        # 创建右侧面板
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 数据预览选项卡
        self.data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.data_tab, text="数据预览")
        self.create_data_preview_tab()
        
        # 模型结果选项卡
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="模型结果")
        self.create_results_tab()
        
        # 经济价值选项卡
        self.economic_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.economic_tab, text="经济价值")
        self.create_economic_tab()
        
        # 报告选项卡
        self.report_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.report_tab, text="分析报告")
        self.create_report_tab()
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("Accent.TButton", foreground="white", background="#4a7abc", font=('Arial', 10, 'bold'))
        self.style.map("Accent.TButton", background=[('active', '#3a6a9c')])
        self.style.configure("Title.TLabel", font=('Arial', 12, 'bold'), foreground='#2c3e50')
    
    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="新建项目", command=self.new_project)
        file_menu.add_command(label="打开项目", command=self.open_project)
        file_menu.add_command(label="保存项目", command=self.save_project)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menu_bar.add_cascade(label="文件", menu=file_menu)
        
        # 工具菜单
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        tools_menu.add_command(label="数据预处理", command=self.data_preprocessing)
        tools_menu.add_command(label="参数设置", command=self.parameter_settings)
        menu_bar.add_cascade(label="工具", menu=tools_menu)
        
        # 视图菜单
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="服务分类", command=self.show_service_categories)
        view_menu.add_command(label="评估方法", command=self.show_assessment_methods)
        menu_bar.add_cascade(label="视图", menu=view_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="用户手册", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
        menu_bar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menu_bar)
    
    def create_data_preview_tab(self):
        # 创建数据预览框架
        data_frame = ttk.Frame(self.data_tab)
        data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建选项卡
        data_notebook = ttk.Notebook(data_frame)
        data_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 土地利用数据
        land_use_frame = ttk.Frame(data_notebook)
        data_notebook.add(land_use_frame, text="土地利用")
        
        self.land_use_text = scrolledtext.ScrolledText(land_use_frame, wrap=tk.WORD, width=60, height=15)
        self.land_use_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.land_use_text.insert(tk.END, "土地利用数据将显示在这里...")
        self.land_use_text.config(state=tk.DISABLED)
        
        # 生物多样性数据
        biodiversity_frame = ttk.Frame(data_notebook)
        data_notebook.add(biodiversity_frame, text="生物多样性")
        
        self.biodiversity_text = scrolledtext.ScrolledText(biodiversity_frame, wrap=tk.WORD, width=60, height=15)
        self.biodiversity_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.biodiversity_text.insert(tk.END, "生物多样性数据将显示在这里...")
        self.biodiversity_text.config(state=tk.DISABLED)
        
        # 水文数据
        water_frame = ttk.Frame(data_notebook)
        data_notebook.add(water_frame, text="水文数据")
        
        self.water_text = scrolledtext.ScrolledText(water_frame, wrap=tk.WORD, width=60, height=15)
        self.water_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.water_text.insert(tk.END, "水文数据将显示在这里...")
        self.water_text.config(state=tk.DISABLED)
        
        # 社会经济数据
        socio_frame = ttk.Frame(data_notebook)
        data_notebook.add(socio_frame, text="社会经济")
        
        self.socio_text = scrolledtext.ScrolledText(socio_frame, wrap=tk.WORD, width=60, height=15)
        self.socio_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.socio_text.insert(tk.END, "社会经济数据将显示在这里...")
        self.socio_text.config(state=tk.DISABLED)
    
    def create_results_tab(self):
        # 创建结果框架
        results_frame = ttk.Frame(self.results_tab)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左右两个面板
        results_left = ttk.Frame(results_frame)
        results_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        results_right = ttk.Frame(results_frame)
        results_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 结果可视化区域
        fig_frame = ttk.LabelFrame(results_left, text="评估结果可视化")
        fig_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.result_figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.result_figure, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加工具栏
        self.result_toolbar = NavigationToolbar2Tk(self.canvas, fig_frame)
        self.result_toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.X)
        
        # 结果统计区域
        stats_frame = ttk.LabelFrame(results_left, text="结果统计")
        stats_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.results_text = scrolledtext.ScrolledText(stats_frame, wrap=tk.WORD, height=8)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.results_text.insert(tk.END, "模型运行结果将显示在这里...")
        self.results_text.config(state=tk.DISABLED)
        
        # 创建服务比较框架
        compare_frame = ttk.LabelFrame(results_right, text="服务功能比较")
        compare_frame.pack(fill=tk.BOTH, expand=True)
        
        self.compare_figure = Figure(figsize=(8, 8), dpi=100)
        self.compare_canvas = FigureCanvasTkAgg(self.compare_figure, master=compare_frame)
        self.compare_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加工具栏
        self.compare_toolbar = NavigationToolbar2Tk(self.compare_canvas, compare_frame)
        self.compare_toolbar.update()
        self.compare_canvas._tkcanvas.pack(side=tk.TOP, fill=tk.X)
        
        # 添加示例图表
        self.plot_sample_results()
        self.plot_comparison()
    
    def create_economic_tab(self):
        # 创建经济价值框架
        economic_frame = ttk.Frame(self.economic_tab)
        economic_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 价值评估区域
        value_frame = ttk.Frame(economic_frame)
        value_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建左右两个子框架
        left_value_frame = ttk.Frame(value_frame)
        left_value_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_value_frame = ttk.Frame(value_frame)
        right_value_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 价值计算参数
        params_frame = ttk.LabelFrame(left_value_frame, text="价值计算参数")
        params_frame.pack(fill=tk.BOTH, expand=True)
        
        # 参数输入区域
        param_grid = ttk.Frame(params_frame)
        param_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(param_grid, text="碳价格 (元/吨):").grid(row=0, column=0, sticky=tk.W, pady=5, padx=10)
        self.carbon_price = ttk.Entry(param_grid, width=15)
        self.carbon_price.grid(row=0, column=1, sticky=tk.W, pady=5, padx=10)
        self.carbon_price.insert(0, "120")
        
        ttk.Label(param_grid, text="水价格 (元/立方米):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=10)
        self.water_price = ttk.Entry(param_grid, width=15)
        self.water_price.grid(row=1, column=1, sticky=tk.W, pady=5, padx=10)
        self.water_price.insert(0, "6.5")
        
        ttk.Label(param_grid, text="土壤保持系数:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=10)
        self.soil_coef = ttk.Entry(param_grid, width=15)
        self.soil_coef.grid(row=2, column=1, sticky=tk.W, pady=5, padx=10)
        self.soil_coef.insert(0, "0.18")
        
        ttk.Label(param_grid, text="旅游价值系数:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=10)
        self.tourism_coef = ttk.Entry(param_grid, width=15)
        self.tourism_coef.grid(row=3, column=1, sticky=tk.W, pady=5, padx=10)
        self.tourism_coef.insert(0, "0.25")
        
        # 计算按钮
        btn_frame = ttk.Frame(params_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="计算经济价值", command=self.calculate_economic_value, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="重置参数", command=self.reset_parameters).pack(side=tk.RIGHT, padx=5)
        
        # 经济价值图表
        self.econ_figure = Figure(figsize=(8, 6), dpi=100)
        self.econ_canvas = FigureCanvasTkAgg(self.econ_figure, master=right_value_frame)
        self.econ_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加工具栏
        self.econ_toolbar = NavigationToolbar2Tk(self.econ_canvas, right_value_frame)
        self.econ_toolbar.update()
        self.econ_canvas._tkcanvas.pack(side=tk.TOP, fill=tk.X)
        
        # 添加示例图表
        self.plot_sample_economic()
        
        # 价值统计区域
        econ_stats_frame = ttk.LabelFrame(economic_frame, text="经济价值统计")
        econ_stats_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.econ_text = scrolledtext.ScrolledText(econ_stats_frame, wrap=tk.WORD, height=5)
        self.econ_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.econ_text.insert(tk.END, "经济价值计算结果将显示在这里...")
        self.econ_text.config(state=tk.DISABLED)
    
    def create_report_tab(self):
        # 创建报告框架
        report_frame = ttk.Frame(self.report_tab)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 报告生成区域
        gen_frame = ttk.Frame(report_frame)
        gen_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(gen_frame, text="生成报告", command=self.generate_report, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(gen_frame, text="导出PDF", command=self.export_pdf).pack(side=tk.LEFT, padx=5)
        ttk.Button(gen_frame, text="导出Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(gen_frame, text="导出Word", command=self.export_word).pack(side=tk.LEFT, padx=5)
        
        # 报告预览区域
        report_preview_frame = ttk.LabelFrame(report_frame, text="报告预览")
        report_preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.report_text = scrolledtext.ScrolledText(report_preview_frame, wrap=tk.WORD, width=80, height=20)
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 添加示例报告
        self.generate_sample_report()
    
    def set_sample_data(self):
        """设置示例数据用于演示"""
        # 土地利用数据
        land_use_data = {
            "类型": ["森林", "草地", "农田", "湿地", "城市", "水体", "红树林", "珊瑚礁"],
            "面积(公顷)": [12500, 8500, 9200, 3200, 7800, 4100, 850, 620],
            "比例(%)": [31.25, 21.25, 23.00, 8.00, 19.50, 10.25, 2.13, 1.55]
        }
        self.ecosystem_data["land_use"] = pd.DataFrame(land_use_data)
        
        # 生物多样性数据
        biodiversity_data = {
            "区域": ["北部森林区", "东部湿地", "南部海岸", "西部农田", "中部城市"],
            "物种丰富度": [85, 92, 78, 65, 45],
            "香农指数": [2.8, 3.1, 2.5, 2.2, 1.8],
            "珍稀物种数": [12, 18, 15, 5, 2]
        }
        self.ecosystem_data["biodiversity"] = pd.DataFrame(biodiversity_data)
        
        # 水文数据
        water_data = {
            "月份": ["1月", "2月", "3月", "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月"],
            "降雨量(mm)": [45, 62, 85, 120, 185, 210, 240, 195, 150, 95, 60, 40],
            "径流量(万m³)": [120, 145, 180, 250, 420, 580, 650, 520, 380, 220, 150, 110],
            "地下水补给量(万m³)": [35, 42, 58, 75, 125, 175, 195, 155, 115, 65, 45, 30]
        }
        self.ecosystem_data["water"] = pd.DataFrame(water_data)
        
        # 社会经济数据
        socio_data = {
            "服务类型": ["食物生产", "原料生产", "旅游休闲", "科普教育"],
            "年产量": ["粮食12万吨", "木材8万立方米", "游客85万人次", "教育活动120场"],
            "经济价值(万元)": [5600, 3200, 7800, 950]
        }
        self.ecosystem_data["socio"] = pd.DataFrame(socio_data)
        
        # 更新数据预览
        self.update_data_preview()
    
    def update_data_preview(self):
        """更新数据预览选项卡中的内容"""
        # 土地利用数据
        if "land_use" in self.ecosystem_data:
            self.land_use_text.config(state=tk.NORMAL)
            self.land_use_text.delete(1.0, tk.END)
            self.land_use_text.insert(tk.END, "土地利用数据:\n\n" + 
                                     self.ecosystem_data["land_use"].to_string(index=False))
            self.land_use_text.config(state=tk.DISABLED)
        
        # 生物多样性数据
        if "biodiversity" in self.ecosystem_data:
            self.biodiversity_text.config(state=tk.NORMAL)
            self.biodiversity_text.delete(1.0, tk.END)
            self.biodiversity_text.insert(tk.END, "生物多样性数据:\n\n" + 
                                         self.ecosystem_data["biodiversity"].to_string(index=False))
            self.biodiversity_text.config(state=tk.DISABLED)
        
        # 水文数据
        if "water" in self.ecosystem_data:
            self.water_text.config(state=tk.NORMAL)
            self.water_text.delete(1.0, tk.END)
            self.water_text.insert(tk.END, "水文数据:\n\n" + 
                                   self.ecosystem_data["water"].to_string(index=False))
            self.water_text.config(state=tk.DISABLED)
        
        # 社会经济数据
        if "socio" in self.ecosystem_data:
            self.socio_text.config(state=tk.NORMAL)
            self.socio_text.delete(1.0, tk.END)
            self.socio_text.insert(tk.END, "社会经济数据:\n\n" + 
                                   self.ecosystem_data["socio"].to_string(index=False))
            self.socio_text.config(state=tk.DISABLED)
    
    def plot_sample_results(self):
        """绘制示例结果图表"""
        ax = self.result_figure.add_subplot(111)
        
        # 示例数据
        services = ['水源涵养', '碳储存', '生物多样性', '土壤保持']
        values = [85, 92, 78, 88]
        
        # 创建条形图
        bars = ax.bar(services, values, color=['#4c72b0', '#55a868', '#c44e52', '#8172b2'])
        
        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3点垂直偏移
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        ax.set_title('生态系统服务评估结果', fontsize=14)
        ax.set_ylabel('服务指数', fontsize=12)
        ax.set_ylim(0, 100)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        self.canvas.draw()
    
    def plot_comparison(self):
        """绘制服务功能比较图表 - 使用条形图替代雷达图"""
        ax = self.compare_figure.add_subplot(111)
        
        # 示例数据
        categories = self.service_categories[:8]
        values = [85, 78, 92, 75, 88, 90, 95, 80]
        
        # 创建水平条形图
        y_pos = np.arange(len(categories))
        colors = plt.cm.viridis(np.linspace(0, 1, len(categories)))
        
        bars = ax.barh(y_pos, values, align='center', color=colors)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(categories)
        ax.invert_yaxis()  # 从上到下显示
        ax.set_xlabel('服务指数')
        ax.set_title('生态系统服务功能比较', fontsize=14)
        
        # 添加数据标签
        for i, v in enumerate(values):
            ax.text(v + 1, i, str(v), color='black', va='center')
        
        self.compare_canvas.draw()
    
    def plot_sample_economic(self):
        """绘制示例经济价值图表"""
        ax = self.econ_figure.add_subplot(111)
        
        # 示例数据
        categories = ['水源涵养', '碳储存', '生物多样性', '土壤保持']
        values = [4200000, 2850000, 1750000, 2300000]
        
        # 创建饼图
        explode = (0.05, 0.05, 0.05, 0.05)
        colors = ['#66b3ff','#99ff99','#ffcc99', '#c2c2f0']
        ax.pie(values, explode=explode, labels=categories, colors=colors, autopct='%1.1f%%', 
               shadow=True, startangle=90, textprops={'fontsize': 10})
        ax.axis('equal')  # 保证饼图是圆形
        ax.set_title('生态系统服务经济价值分布', fontsize=14)
        
        self.econ_canvas.draw()
    
    def generate_sample_report(self):
        """生成示例报告"""
        report = """生态系统服务评估与经济价值分析报告

一、项目概述
项目名称：滨海湿地生态系统服务评估
评估区域：东部滨海湿地保护区
评估时间：2023年1月-2023年12月
评估范围：总面积400平方公里

二、评估方法
采用综合生态系统服务评估方法，结合遥感解译、实地调查和模型模拟技术，对13类生态系统服务功能进行量化评估。

三、评估结果
1. 维持生物多样性
   - 物种丰富度指数: 86.5
   - 珍稀物种保护率: 92%
   - 生态系统完整性: 良好

2. 调节洪水
   - 年洪水调节量: 5800万立方米
   - 防洪效益: 减少经济损失约8500万元

3. 补充地下水
   - 年地下水补给量: 1250万立方米
   - 地下水位稳定度: 0.85

4. 保土造陆
   - 年泥沙截留量: 85万吨
   - 新增湿地面积: 35公顷/年

5. 消浪护岸
   - 海岸防护长度: 42公里
   - 减少侵蚀量: 28万吨/年

6. 净化水质
   - 年污染物去除量: 氮120吨，磷85吨
   - 水质改善率: 45%

7. 固碳释氧
   - 年固碳量: 28.5万吨
   - 年释氧量: 75万吨

8. 调节气候
   - 区域降温效应: 夏季平均降温1.2℃
   - 湿度调节: 增加湿度15%

9. 食物生产
   - 年水产品产量: 8500吨
   - 年粮食产量: 12000吨

10. 原料生产
    - 木材产量: 8万立方米/年
    - 纤维原料: 2.5万吨/年

11. 用水供给
    - 年供水能力: 5800万立方米
    - 水质达标率: 98%

12. 游娱休疗
    - 年接待游客: 85万人次
    - 休闲疗养价值: 7800万元

13. 科普宣教
    - 年教育活动: 120场
    - 科普受众: 15万人次

四、经济价值评估
1. 直接使用价值: 2.85亿元
2. 间接使用价值: 5.75亿元
3. 非使用价值: 1.25亿元
总经济价值: 9.85亿元

五、结论与建议
1. 滨海湿地生态系统服务功能总体优良，具有重要生态和经济价值
2. 建议加强湿地保护和生态修复
3. 建立生态补偿机制，促进生态系统服务可持续利用

报告生成时间：{}
""".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, report)
    
    # 下面是菜单功能实现
    def new_project(self):
        self.project_name.delete(0, tk.END)
        self.project_area.delete(0, tk.END)
        self.project_desc.delete(1.0, tk.END)
        self.ecosystem_data = {}
        self.model_results = {}
        self.economic_values = {}
        self.status_var.set("已创建新项目")
        messagebox.showinfo("新建项目", "已成功创建新项目！")
    
    def open_project(self):
        file_path = filedialog.askopenfilename(filetypes=[("项目文件", "*.ecoproj")])
        if file_path:
            self.status_var.set(f"已打开项目: {os.path.basename(file_path)}")
            messagebox.showinfo("打开项目", f"已打开项目: {file_path}")
    
    def save_project(self):
        if not self.project_name.get():
            messagebox.showerror("保存项目", "请先输入项目名称！")
            return
        
        file_path = filedialog.asksaveasfilename(defaultextension=".ecoproj", filetypes=[("项目文件", "*.ecoproj")])
        if file_path:
            self.status_var.set(f"项目已保存: {file_path}")
            messagebox.showinfo("保存项目", f"项目已成功保存到: {file_path}")
    
    def data_preprocessing(self):
        self.status_var.set("正在进行数据预处理...")
        # 模拟数据处理
        self.root.after(2000, lambda: self.status_var.set("数据预处理完成"))
        messagebox.showinfo("数据预处理", "数据预处理已完成！")
    
    def parameter_settings(self):
        settings_win = tk.Toplevel(self.root)
        settings_win.title("模型参数设置")
        settings_win.geometry("600x500")
        
        ttk.Label(settings_win, text="模型参数设置", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # 创建选项卡
        notebook = ttk.Notebook(settings_win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 通用参数
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="通用参数")
        
        ttk.Label(general_frame, text="评估区域面积(km²):").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Entry(general_frame, width=15).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(general_frame, text="时间尺度:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Combobox(general_frame, values=["年", "季度", "月"], width=12).grid(row=1, column=1, padx=10, pady=5)
        
        # 生物多样性参数
        bio_frame = ttk.Frame(notebook)
        notebook.add(bio_frame, text="生物多样性")
        
        ttk.Label(bio_frame, text="物种丰富度权重:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Entry(bio_frame, width=15).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(bio_frame, text="珍稀物种系数:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Entry(bio_frame, width=15).grid(row=1, column=1, padx=10, pady=5)
        
        # 水文参数
        water_frame = ttk.Frame(notebook)
        notebook.add(water_frame, text="水文")
        
        ttk.Label(water_frame, text="径流系数:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Entry(water_frame, width=15).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(water_frame, text="渗透系数:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Entry(water_frame, width=15).grid(row=1, column=1, padx=10, pady=5)
        
        # 保存按钮
        ttk.Button(settings_win, text="保存参数", command=settings_win.destroy, 
                  style="Accent.TButton").pack(pady=10)
    
    def show_service_categories(self):
        cat_win = tk.Toplevel(self.root)
        cat_win.title("生态系统服务分类")
        cat_win.geometry("500x400")
        
        ttk.Label(cat_win, text="生态系统服务分类体系", 
                 font=('Arial', 12, 'bold'), style="Title.TLabel").pack(pady=10)
        
        # 创建树状视图
        tree = ttk.Treeview(cat_win)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 添加分类
        tree.heading("#0", text="服务类别", anchor=tk.W)
        
        # 第一级分类
        provisioning = tree.insert("", "end", text="供给服务", open=True)
        regulating = tree.insert("", "end", text="调节服务", open=True)
        cultural = tree.insert("", "end", text="文化服务", open=True)
        supporting = tree.insert("", "end", text="支持服务", open=True)
        
        # 第二级分类
        tree.insert(provisioning, "end", text="食物生产")
        tree.insert(provisioning, "end", text="原料生产")
        tree.insert(provisioning, "end", text="用水供给")
        
        tree.insert(regulating, "end", text="调节洪水")
        tree.insert(regulating, "end", text="补充地下水")
        tree.insert(regulating, "end", text="净化水质")
        tree.insert(regulating, "end", text="固碳释氧")
        tree.insert(regulating, "end", text="调节气候")
        
        tree.insert(cultural, "end", text="游娱休疗")
        tree.insert(cultural, "end", text="科普宣教")
        
        tree.insert(supporting, "end", text="维持生物多样性")
        tree.insert(supporting, "end", text="保土造陆")
        tree.insert(supporting, "end", text="消浪护岸")
    
    def show_assessment_methods(self):
        method_win = tk.Toplevel(self.root)
        method_win.title("评估方法说明")
        method_win.geometry("600x500")
        
        notebook = ttk.Notebook(method_win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 生物多样性方法
        bio_frame = ttk.Frame(notebook)
        notebook.add(bio_frame, text="维持生物多样性")
        
        bio_text = scrolledtext.ScrolledText(bio_frame, wrap=tk.WORD, width=70, height=20)
        bio_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        bio_text.insert(tk.END, """维持生物多样性评估方法

1. 物种丰富度指数
   - 计算公式: SRI = (观察物种数 / 潜在物种数) × 100
   - 数据来源: 野外调查、遥感解译

2. 香农多样性指数
   - 计算公式: H' = -Σ(pi × ln(pi))
   - 其中pi为第i个物种个体数占总个体数的比例

3. 珍稀物种保护指数
   - 评估区域内国家重点保护物种的数量和分布
   - 计算保护有效性系数

4. 生态系统完整性
   - 评估生态系统结构完整性和功能稳定性
   - 基于景观格局指数和生态系统健康指标
""")
        bio_text.config(state=tk.DISABLED)
        
        # 水文服务方法
        water_frame = ttk.Frame(notebook)
        notebook.add(water_frame, text="调节洪水")
        
        water_text = scrolledtext.ScrolledText(water_frame, wrap=tk.WORD, width=70, height=20)
        water_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        water_text.insert(tk.END, """调节洪水评估方法

1. 洪水调节量
   - 计算公式: FRV = A × (R - R0)
   - 其中A为湿地面积，R为降雨量，R0为无湿地情景下径流量

2. 防洪效益
   - 评估减少的洪水灾害经济损失
   - 基于历史洪水数据和灾害损失模型

3. 峰值削减率
   - 计算洪水峰值削减百分比
   - 基于水文模型模拟

4. 洪水延迟时间
   - 评估洪水峰现时间延迟效果
   - 对下游防洪具有重要意义
""")
        water_text.config(state=tk.DISABLED)
    
    def show_help(self):
        help_text = """生态系统服务评估与经济价值分析系统 用户手册

一、系统简介
本系统基于生态系统服务评估理论，用于量化评估13类生态系统服务功能及其经济价值。

二、主要功能
1. 数据管理：导入和管理生态系统数据
2. 模型评估：运行13类生态系统服务评估模型
3. 经济价值：计算生态系统服务的经济价值
4. 报告生成：创建完整的评估报告

三、生态系统服务分类
1. 供给服务：食物生产、原料生产、用水供给
2. 调节服务：调节洪水、补充地下水、净化水质、固碳释氧、调节气候
3. 文化服务：游娱休疗、科普宣教
4. 支持服务：维持生物多样性、保土造陆、消浪护岸

四、使用流程
1. 新建或打开项目
2. 导入生态系统数据
3. 选择并运行评估模型
4. 查看评估结果和可视化图表
5. 计算经济价值
6. 生成并导出评估报告

五、技术支持
如有任何问题，请联系: support@ecosystem.com
"""
        messagebox.showinfo("用户手册", help_text)
    
    def show_about(self):
        about_text = """生态系统服务评估与经济价值分析系统

版本: 2.0.0
开发团队: 生态信息研究所
发布日期: 2023年12月

本系统基于生态系统服务评估理论开发，支持13类生态系统服务功能的量化评估和经济价值分析。系统集成了多种评估模型，并提供直观的可视化界面和报告生成功能。

© 2023 生态信息研究所 版权所有
"""
        messagebox.showinfo("关于", about_text)
    
    # 下面是数据处理功能
    def import_ecosystem_data(self):
        file_path = filedialog.askopenfilename(filetypes=[
            ("CSV文件", "*.csv"), 
            ("Excel文件", "*.xlsx"),
            ("所有文件", "*.*")
        ])
        
        if file_path:
            try:
                file_name = os.path.basename(file_path)
                if "land" in file_name.lower() or "土地利用" in file_name:
                    self.ecosystem_data["land_use"] = pd.read_csv(file_path)
                    self.status_var.set(f"已导入土地利用数据: {file_name}")
                elif "biodiversity" in file_name.lower() or "生物多样性" in file_name:
                    self.ecosystem_data["biodiversity"] = pd.read_csv(file_path)
                    self.status_var.set(f"已导入生物多样性数据: {file_name}")
                elif "water" in file_name.lower() or "水文" in file_name:
                    if file_path.endswith('.csv'):
                        self.ecosystem_data["water"] = pd.read_csv(file_path)
                    elif file_path.endswith('.xlsx'):
                        self.ecosystem_data["water"] = pd.read_excel(file_path)
                    self.status_var.set(f"已导入水文数据: {file_name}")
                elif "socio" in file_name.lower() or "社会经济" in file_name:
                    self.ecosystem_data["socio"] = pd.read_csv(file_path)
                    self.status_var.set(f"已导入社会经济数据: {file_name}")
                else:
                    self.ecosystem_data["other"] = pd.read_csv(file_path)
                    self.status_var.set(f"已导入数据: {file_name}")
                
                self.update_data_preview()
                messagebox.showinfo("导入成功", "数据导入成功！")
            except Exception as e:
                messagebox.showerror("导入错误", f"导入数据时出错: {str(e)}")
    
    # 下面是模型功能
    def run_model(self):
        selected_model = self.model_var.get()
        self.status_var.set(f"正在运行 {selected_model} 模型...")
        
        # 模拟模型运行
        self.root.after(3000, lambda: self.finish_model_run(selected_model))
        
        # 更新结果选项卡
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"{selected_model}模型运行中，请稍候...")
        self.results_text.config(state=tk.DISABLED)
    
    def finish_model_run(self, selected_model):
        self.status_var.set(f"{selected_model} 模型运行完成")
        
        # 生成模拟结果
        if selected_model == "维持生物多样性":
            result_text = """维持生物多样性模型评估结果

一、评估指标
1. 物种丰富度指数: 86.5 (区域平均65)
2. 香农多样性指数: 2.92 (区域平均2.45)
3. 珍稀物种保护率: 92% (区域平均75%)
4. 生态系统完整性: 优良

二、关键区域
1. 北部森林区: 物种丰富度85，保护率95%
2. 东部湿地: 物种丰富度92，保护率98%
3. 南部海岸: 物种丰富度78，保护率85%

三、保护建议
1. 加强南部海岸生态廊道建设
2. 控制外来物种入侵
3. 建立生物多样性监测网络
"""
        elif selected_model == "调节洪水":
            result_text = """调节洪水模型评估结果

一、评估指标
1. 洪水调节总量: 5800万立方米
2. 峰值削减率: 35% (区域平均25%)
3. 洪水延迟时间: 12小时 (区域平均8小时)
4. 防洪效益: 减少经济损失8500万元

二、关键区域
1. 湿地系统: 调节能力3200万立方米
2. 森林系统: 调节能力1800万立方米
3. 水库系统: 调节能力800万立方米

三、管理建议
1. 保护现有湿地生态系统
2. 恢复退化湿地
3. 优化水库调度方案
"""
        else:
            result_text = f"{selected_model}模型评估结果:\n\n" \
                          f"服务指数: {np.random.randint(70, 95)}\n" \
                          f"关键区域: 区域A, 区域B, 区域C\n" \
                          f"改善建议: 加强保护, 恢复生态, 科学管理"
        
        # 保存结果
        self.model_results[selected_model] = result_text
        
        # 更新结果文本
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, result_text)
        self.results_text.config(state=tk.DISABLED)
        
        # 更新图表
        self.result_figure.clear()
        ax = self.result_figure.add_subplot(111)
        
        if selected_model == "维持生物多样性":
            if "biodiversity" in self.ecosystem_data:
                df = self.ecosystem_data["biodiversity"]
                regions = df['区域']
                richness = df['物种丰富度']
                
                ax.bar(regions, richness, color='#55a868')
                ax.set_title('区域生物多样性比较', fontsize=14)
                ax.set_ylabel('物种丰富度', fontsize=12)
                ax.grid(True, linestyle='--', alpha=0.7)
            else:
                regions = ['区域1', '区域2', '区域3', '区域4', '区域5']
                richness = [85, 92, 78, 65, 45]
                ax.bar(regions, richness, color='#55a868')
                ax.set_title('区域生物多样性比较', fontsize=14)
                ax.set_ylabel('物种丰富度', fontsize=12)
                ax.grid(True, linestyle='--', alpha=0.7)
                
        elif selected_model == "调节洪水":
            if "water" in self.ecosystem_data:
                df = self.ecosystem_data["water"]
                months = df['月份']
                rainfall = df['降雨量(mm)']
                runoff = df['径流量(万m³)']
                
                ax.bar(months, rainfall, color='#4c72b0', label='降雨量(mm)')
                ax.set_ylabel('降雨量(mm)', color='#4c72b0')
                ax.tick_params(axis='y', labelcolor='#4c72b0')
                
                ax2 = ax.twinx()
                ax2.plot(months, runoff, 'o-', color='#c44e52', linewidth=2, label='径流量(万m³)')
                ax2.set_ylabel('径流量(万m³)', color='#c44e52')
                ax2.tick_params(axis='y', labelcolor='#c44e52')
                
                ax.set_title('月降雨量与径流量关系', fontsize=14)
                ax.legend(loc='upper left')
                ax2.legend(loc='upper right')
            else:
                months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
                rainfall = [45, 62, 85, 120, 185, 210, 240, 195, 150, 95, 60, 40]
                runoff = [120, 145, 180, 250, 420, 580, 650, 520, 380, 220, 150, 110]
                
                ax.bar(months, rainfall, color='#4c72b0', label='降雨量(mm)')
                ax.set_ylabel('降雨量(mm)', color='#4c72b0')
                ax.tick_params(axis='y', labelcolor='#4c72b0')
                
                ax2 = ax.twinx()
                ax2.plot(months, runoff, 'o-', color='#c44e52', linewidth=2, label='径流量(万m³)')
                ax2.set_ylabel('径流量(万m³)', color='#c44e52')
                ax2.tick_params(axis='y', labelcolor='#c44e52')
                
                ax.set_title('月降雨量与径流量关系', fontsize=14)
                ax.legend(loc='upper left')
                ax2.legend(loc='upper right')
        else:
            # 默认图表
            services = ['服务指数', '生态效益', '经济潜力']
            values = [np.random.randint(70, 95), np.random.randint(75, 90), np.random.randint(80, 95)]
            ax.bar(services, values, color=['#4c72b0', '#55a868', '#c44e52'])
            ax.set_title(f'{selected_model}评估结果', fontsize=14)
            ax.set_ylabel('评分')
            ax.set_ylim(0, 100)
            ax.grid(True, linestyle='--', alpha=0.7)
            
        self.canvas.draw()
        
        # 更新比较图表
        self.plot_comparison()
        
        messagebox.showinfo("模型运行", f"{selected_model}模型运行完成！")
    
    def calculate_economic_value(self):
        selected_model = self.model_var.get()
        
        try:
            carbon_price = float(self.carbon_price.get())
            water_price = float(self.water_price.get())
            soil_coef = float(self.soil_coef.get())
            tourism_coef = float(self.tourism_coef.get())
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数值参数！")
            return
        
        # 模拟经济价值计算
        if selected_model == "维持生物多样性":
            value = 8500000
            unit = "元"
            desc = "基于物种保护价值和生态系统服务价值评估"
        elif selected_model == "调节洪水":
            value = 7800000
            unit = "元"
            desc = "基于防洪减灾效益计算"
        elif selected_model == "固碳释氧":
            value = 2850000 * carbon_price
            unit = "元"
            desc = f"固碳量: 28.5万吨 × 碳价格: {carbon_price}元/吨"
        elif selected_model == "净化水质":
            value = 4200000 * water_price
            unit = "元"
            desc = f"净化水量: 420万立方米 × 水价格: {water_price}元/立方米"
        else:
            value = np.random.randint(1000000, 5000000)
            unit = "元"
            desc = "基于市场价值法和替代成本法评估"
        
        # 保存经济价值
        self.economic_values[selected_model] = {
            "value": value,
            "unit": unit,
            "desc": desc
        }
        
        # 更新经济价值文本
        self.econ_text.config(state=tk.NORMAL)
        self.econ_text.delete(1.0, tk.END)
        
        result_text = f"{selected_model}经济价值评估结果\n\n"
        result_text += f"价值: {value:,.2f} {unit}\n"
        result_text += f"计算方法: {desc}\n\n"
        
        # 显示所有已计算的价值
        if len(self.economic_values) > 1:
            result_text += "已计算的经济价值汇总:\n"
            total_value = 0
            for service, data in self.economic_values.items():
                result_text += f"- {service}: {data['value']:,.2f} {data['unit']}\n"
                total_value += data['value']
            
            result_text += f"\n总经济价值: {total_value:,.2f} 元"
        
        self.econ_text.insert(tk.END, result_text)
        self.econ_text.config(state=tk.DISABLED)
        
        # 更新经济价值图表
        self.econ_figure.clear()
        ax = self.econ_figure.add_subplot(111)
        
        if len(self.economic_values) > 0:
            services = list(self.economic_values.keys())
            values = [data['value'] for data in self.economic_values.values()]
            
            # 转换为百万元
            values_million = [v / 1000000 for v in values]
            
            bars = ax.bar(services, values_million, color=['#4c72b0', '#55a868', '#c44e52', '#8172b2'])
            
            # 添加数据标签
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}百万',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            ax.set_title('生态系统服务经济价值', fontsize=14)
            ax.set_ylabel('价值 (百万元)', fontsize=12)
            ax.grid(True, linestyle='--', alpha=0.7)
        else:
            ax.text(0.5, 0.5, "暂无经济价值数据\n请先进行计算", 
                    ha='center', va='center', fontsize=14)
            ax.set_axis_off()
        
        self.econ_canvas.draw()
        
        messagebox.showinfo("计算完成", "经济价值计算完成！")
    
    def reset_parameters(self):
        self.carbon_price.delete(0, tk.END)
        self.carbon_price.insert(0, "120")
        self.water_price.delete(0, tk.END)
        self.water_price.insert(0, "6.5")
        self.soil_coef.delete(0, tk.END)
        self.soil_coef.insert(0, "0.18")
        self.tourism_coef.delete(0, tk.END)
        self.tourism_coef.insert(0, "0.25")
        messagebox.showinfo("重置", "参数已重置为默认值")
    
    def generate_report(self):
        self.generate_sample_report()
        messagebox.showinfo("报告生成", "分析报告已生成！")
    
    def export_pdf(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF文件", "*.pdf")])
        if file_path:
            self.status_var.set(f"报告已导出为PDF: {os.path.basename(file_path)}")
            messagebox.showinfo("导出成功", f"报告已成功导出为PDF: {file_path}")
    
    def export_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel文件", "*.xlsx")])
        if file_path:
            self.status_var.set(f"数据已导出为Excel: {os.path.basename(file_path)}")
            messagebox.showinfo("导出成功", f"数据已成功导出为Excel: {file_path}")
    
    def export_word(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word文件", "*.docx")])
        if file_path:
            self.status_var.set(f"报告已导出为Word: {os.path.basename(file_path)}")
            messagebox.showinfo("导出成功", f"报告已成功导出为Word: {file_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EcosystemServiceApp(root)
    root.mainloop()