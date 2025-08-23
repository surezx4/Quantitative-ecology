# -*- 编码: utf-8 -*-
'""'
创建于2025年8月15日星期五14:56:59

@作者: 管理员
'""'

导入 tkinter 为 tk
从 tkinter 导入 ttk, filedialog, messagebox
导入 numpy 为 np
导入 pandas 为 pd
导入 matplotlib.pyplot 为 plt
从 matplotlib.backends.backend_tkagg 导入 FigureCanvasTkAgg
从 scipy.integrate 导入 solve_ivp
导入 os
导入 seaborn 为 sns
从 sklearn.preprocessing 导入 StandardScaler
导入 statsmodels.api 为 sm
从 matplotlib.figure 导入 Figure
导入 matplotlib.dates 为 mdates

# 设置中文显示
plt.rcParams["font.family"] = ["思源黑体", " WenQuanYi Micro Hei", "黑体 TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

类 生态系统模型：
    """生态系统动力学模型类，包含模型参数和微分方程定义"""
    
    定义 __init__(self):
        # 模型参数初始化
        self.params = {
            # 生态因子对气象因子的敏感性参数
            'fvc_temp_sens'：0.02，    # FVC对温度的敏感性
            'fvc_precip_sens'：0.001，# FVC对降水的敏感性
            'ndvi_temp_sens'：0.015，  # NDVI对温度的敏感性
            'ndvi_precip_sens'：0.002，# NDVI对降水的敏感性
            'npp_temp_sens': 0.03,    # NPP对温度的敏感性
            'npp_precip_sens': 0.0015,# NPP对降水的敏感性
            
            # 生态因子之间的相互作用参数
            'fvc_ndvi_interact': 0.1, # FVC与NDVI的相互作用
            'ndvi_npp_interact'：0.15，# NDVI与NPP的相互作用
            'npp_fvc_interact': 0.08, # NPP与FVC的相互作用
            
            # 其他环境因子的影响参数
            'evap_coeff'：0.05，       # 蒸发量影响系数
            ' Sunshine_coeff ': 0.03,   # 日照时长影响系数
            'water_level_coeff': 0.04,# 水位波动影响系数
            'dem_coeff'：0.02         # 地形影响系数
        }
        
        # 数据存储
        self.data = 无
        self.年龄 = 无
        self.dem_data = 无
        
        # 模型结果
        self.仿真结果 = 无
    
    def load_data(self, file_path):
        """加载时间序列数据（包含生态因子和气象因子）"""
        try:
            if file_path.endswith('.csv'):
                self.data = pd.read_csv(file_path, parse_dates=['年份'])
            elif file_path.endswith('.xlsx'):
                self.data = pd.read_excel(file_path, parse_dates=['年份'])
            else:

                
            # 提取年份信息

            return True
        except Exception as e:

            return False
    
    def load_dem_data(self, file_path):
        """加载DEM地形数据"""
        try:
            if file_path.endswith('.csv'):
                self.dem_data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                self.dem_data = pd.read_excel(file_path)
            else:
                raise ValueError("不支持的文件格式，仅支持CSV和Excel文件")
            return True
        except Exception as e:
            messagebox.showerror("DEM数据加载错误", f"加载DEM数据时发生错误: {str(e)}")
            return False
    
    def save_data(self, file_path):
        """保存当前数据"""
        if self.data is None:
            messagebox.showwarning("无数据", "没有可保存的数据，请先加载数据")
            return False
            
        try:
            if file_path.endswith('.csv'):
                self.data.to_csv(file_path, index=False)
            elif file_path.endswith('.xlsx'):
                self.data.to_excel(file_path, index=False)
            else:
                file_path += '.csv'
                self.data.to_csv(file_path, index=False)
            return True
        except Exception as e:
            messagebox.showerror("保存错误", f"保存数据时发生错误: {str(e)}")
            return False
    
    def system_equations(self, t, state, params, env_factors):
        """定义系统动力学模型的微分方程组"""
        fvc, ndvi, npp = state
        
        # 从环境因子中提取当前时间步的气象数据
        # 这里使用线性插值获取任意时间t的环境因子值
        temp = np.interp(t, range(len(env_factors['temp'])), env_factors['temp'])
        precip = np.interp(t, range(len(env_factors['precip'])), env_factors['precip'])
        evap = np.interp(t, range(len(env_factors['evap'])), env_factors['evap'])
        sunshine = np.interp(t, range(len(env_factors['sunshine'])), env_factors['sunshine'])
        water_level = np.interp(t, range(len(env_factors['water_level'])), env_factors['water_level'])
        
        # 地形因子（静态数据，取平均值）
        dem = np.mean(env_factors['dem']) if len(env_factors['dem']) > 0 else 0
        
        # 微分方程
        dfvc_dt = (
            params['fvc_temp_sens'] * (temp - np.mean(env_factors['temp'])) * fvc +
            params['fvc_precip_sens'] * (precip - np.mean(env_factors['precip'])) * fvc +
            params['fvc_ndvi_interact'] * ndvi * (1 - fvc) -
            params['evap_coeff'] * evap * fvc / 100 +
            params['water_level_coeff'] * (np.mean(env_factors['water_level']) - water_level) * fvc
        )
        
        dndvi_dt = (
            params['ndvi_temp_sens'] * (temp - np.mean(env_factors['temp'])) * ndvi +
            params['ndvi_precip_sens'] * (precip - np.mean(env_factors['precip'])) * ndvi +
            params['ndvi_npp_interact'] * npp * (1 - ndvi) +
            params['sunshine_coeff'] * sunshine * ndvi / 1000 -
            params['dem_coeff'] * dem * ndvi / 100
        )
        
        dnpp_dt = (
            params['npp_temp_sens'] * (temp - np.mean(env_factors['temp'])) * npp +
            params['npp_precip_sens'] * (precip - np.mean(env_factors['precip'])) * npp +
            params['npp_fvc_interact'] * fvc * (1 - npp / np.max(env_factors['npp'])) -
            params['evap_coeff'] * evap * npp / 100 +
            params['sunshine_coeff'] * sunshine * npp / 1000
        )
        
        return [dfvc_dt, dndvi_dt, dnpp_dt]
    
    def run_simulation(self):
        """运行系统动力学模型模拟"""
        if self.data is None:
            messagebox.showwarning("无数据", "请先加载数据")
            return False
            
        try:
            # 提取环境因子
            env_factors = {
                'temp': self.data['年均气温'].values,
                'precip': self.data['降水量'].values,
                'evap': self.data['蒸发量'].values,
                'sunshine': self.data['日照时长'].values,
                'water_level': self.data['水位波动'].values,
                'dem': self.dem_data['DEM'].values if self.dem_data is not None else [],
                'npp': self.data['NPP净初级生产力'].values
            }
            
            # 初始状态
            initial_state = [
                self.data['FVC覆盖度指数'].iloc[0],
                self.data['NDVI指数'].iloc[0],
                self.data['NPP净初级生产力'].iloc[0]
            ]
            
            # 时间范围
            t_span = (0, len(self.data) - 1)
            t_eval = np.arange(t_span[0], t_span[1] + 1)
            
            # 求解微分方程
            solution = solve_ivp(
                fun=lambda t, y: self.system_equations(t, y, self.params, env_factors),
                t_span=t_span,
                y0=initial_state,
                t_eval=t_eval,
                method='RK45'
            )
            
            # 存储模拟结果
            self.simulation_results = pd.DataFrame({
                '年份': self.data['年份'],
                'FVC模拟值': solution.y[0],
                'NDVI模拟值': solution.y[1],
                'NPP模拟值': solution.y[2],
                'FVC实际值': self.data['FVC覆盖度指数'],
                'NDVI实际值': self.data['NDVI指数'],
                'NPP实际值': self.data['NPP净初级生产力']
            })
            
            return True
        except Exception as e:
            messagebox.showerror("模拟错误", f"运行模拟时发生错误: {str(e)}")
            return False
    
    def get_statistical_summary(self):
        """生成数据的统计摘要"""
        if self.data is None:
            return None
            
        summary = self.data.describe().round(4)
        return summary
    
    def get_correlation_analysis(self):
        """计算变量间的相关性"""
        if self.data is None:
            return None
            
        # 选择数值型变量进行相关性分析
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        corr = self.data[numeric_cols].corr().round(4)
        return corr
    
    def get_regression_analysis(self, dependent_var, independent_vars):
        """进行回归分析"""
        if self.data is None:
            return None
            
        try:
            X = self.data[independent_vars]
            y = self.data[dependent_var]
            
            # 添加常数项
            X = sm.add_constant(X)
            
            # 拟合线性回归模型
            model = sm.OLS(y, X).fit()
            return model.summary()
        except Exception as e:
            messagebox.showerror("回归分析错误", f"进行回归分析时发生错误: {str(e)}")
            return None


class EcosystemModelGUI:
    """生态系统动力学模型的GUI界面类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("生态系统动力学模型分析工具")
        self.root.geometry("1200x800")
        
        # 创建模型实例
        self.model = EcologicalSystemModel()
        
        # 创建主界面
        self.create_main_widgets()
        
        # 创建标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 数据导入导出标签页
        self.frame_data = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_data, text="数据管理")
        
        # 模型模拟标签页
        self.frame_simulation = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_simulation, text="模型模拟")
        
        # 统计分析标签页
        self.frame_analysis = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_analysis, text="统计分析")
        
        # 参数设置标签页
        self.frame_params = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_params, text="参数设置")
        
        # 初始化各个标签页
        self.init_data_frame()
        self.init_simulation_frame()
        self.init_analysis_frame()
        self.init_params_frame()
    
    def create_main_widgets(self):
        """创建主界面控件"""
        # 创建菜单栏
        menubar = tk.Menu(self.root)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="导入数据", command=self.import_data)
        file_menu.add_command(label="导入DEM数据", command=self.import_dem_data)
        file_menu.add_command(label="导出数据", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 分析菜单
        analysis_menu = tk.Menu(menubar, tearoff=0)
        analysis_menu.add_command(label="运行模拟", command=self.run_simulation)
        analysis_menu.add_command(label="统计摘要", command=self.show_statistical_summary)
        analysis_menu.add_command(label="相关性分析", command=self.show_correlation_analysis)
        menubar.add_cascade(label="分析", menu=analysis_menu)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=self.show_about)
        help_menu.add_command(label="使用帮助", command=self.show_help)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def init_data_frame(self):
        """初始化数据管理标签页"""
        # 创建按钮框架
        btn_frame = ttk.Frame(self.frame_data)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="导入时间序列数据", command=self.import_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导入DEM地形数据", command=self.import_dem_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出数据", command=self.export_data).pack(side=tk.LEFT, padx=5)
        
        # 创建数据表格
        table_frame = ttk.Frame(self.frame_data)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建滚动条
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        
        # 创建树状视图显示数据
        self.data_tree = ttk.Treeview(
            table_frame,
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        
        scrollbar_y.config(command=self.data_tree.yview)
        scrollbar_x.config(command=self.data_tree.xview)
        
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.data_tree.pack(fill=tk.BOTH, expand=True)
        
        # 数据信息标签
        self.data_info = ttk.Label(self.frame_data, text="请导入数据")
        self.data_info.pack(pady=5)
    
    def init_simulation_frame(self):
        """初始化模型模拟标签页"""
        # 控制按钮框架
        control_frame = ttk.Frame(self.frame_simulation)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="运行模拟", command=self.run_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="保存模拟结果", command=self.save_simulation_results).pack(side=tk.LEFT, padx=5)
        
        # 选择显示的变量
        self.var_show_fvc = tk.BooleanVar(value=True)
        self.var_show_ndvi = tk.BooleanVar(value=True)
        self.var_show_npp = tk.BooleanVar(value=True)
        
        check_frame = ttk.Frame(control_frame)
        check_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Checkbutton(check_frame, text="显示FVC", variable=self.var_show_fvc, command=self.update_simulation_plots).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(check_frame, text="显示NDVI", variable=self.var_show_ndvi, command=self.update_simulation_plots).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(check_frame, text="显示NPP", variable=self.var_show_npp, command=self.update_simulation_plots).pack(side=tk.LEFT, padx=2)
        
        # 图表框架
        self.plot_frame = ttk.Frame(self.frame_simulation)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建图表
        self.fig_simulation = Figure(figsize=(10, 6), dpi=100)
        self.canvas_simulation = FigureCanvasTkAgg(self.fig_simulation, master=self.plot_frame)
        self.canvas_simulation.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 状态标签
        self.simulation_status = ttk.Label(self.frame_simulation, text="请加载数据并运行模拟")
        self.simulation_status.pack(pady=5)
    
    def init_analysis_frame(self):
        """初始化统计分析标签页"""
        # 分析控制框架
        control_frame = ttk.Frame(self.frame_analysis)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="统计摘要", command=self.show_statistical_summary).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="相关性分析", command=self.show_correlation_analysis).pack(side=tk.LEFT, padx=5)
        
        # 回归分析控件
        ttk.Label(control_frame, text="回归分析:").pack(side=tk.LEFT, padx=10)
        
        self.dependent_var = tk.StringVar(value="FVC覆盖度指数")
        ttk.Combobox(
            control_frame, 
            textvariable=self.dependent_var, 
            values=["FVC覆盖度指数", "NDVI指数", "NPP净初级生产力"],
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="运行回归分析", command=self.run_regression_analysis).pack(side=tk.LEFT, padx=5)
        
        # 分析结果框架
        self.analysis_result_frame = ttk.Frame(self.frame_analysis)
        self.analysis_result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建结果显示区域
        self.analysis_notebook = ttk.Notebook(self.analysis_result_frame)
        self.analysis_notebook.pack(fill=tk.BOTH, expand=True)
        
        # 统计摘要标签页
        self.frame_summary = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.frame_summary, text="统计摘要")
        
        # 相关性分析标签页
        self.frame_correlation = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.frame_correlation, text="相关性分析")
        
        # 回归分析标签页
        self.frame_regression = ttk.Frame(self.analysis_notebook)
        self.analysis_notebook.add(self.frame_regression, text="回归分析")
        
        # 初始化各个分析结果显示区域
        # 统计摘要表格
        self.summary_tree = ttk.Treeview(self.frame_summary)
        self.summary_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 相关性热图
        self.fig_correlation = Figure(figsize=(8, 6), dpi=100)
        self.canvas_correlation = FigureCanvasTkAgg(self.fig_correlation, master=self.frame_correlation)
        self.canvas_correlation.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 回归分析结果
        self.regression_text = tk.Text(self.frame_regression, wrap=tk.WORD)
        self.regression_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 状态标签
        self.analysis_status = ttk.Label(self.frame_analysis, text="请加载数据并选择分析类型")
        self.analysis_status.pack(pady=5)
    
    def init_params_frame(self):
        """初始化参数设置标签页"""
        # 创建参数设置框架
        params_frame = ttk.LabelFrame(self.frame_params, text="模型参数设置")
        params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 使用网格布局排列参数
        self.param_entries = {}
        row = 0
        
        # 为每个参数创建输入框
        for param_name, value in self.model.params.items():
            # 转换参数名到易读格式
            display_name = self.format_param_name(param_name)
            
            ttk.Label(params_frame, text=display_name).grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
            entry = ttk.Scale(
                params_frame, 
                from_=max(0, value * 0.1), 
                to=value * 5, 
                value=value,
                orient=tk.HORIZONTAL,
                length=300,
                command=lambda v, p=param_name: self.update_param_label(v, p)
            )
            entry.grid(row=row, column=1, padx=10, pady=5)
            
            # 参数值标签
            label = ttk.Label(params_frame, text=f"{value:.4f}")
            label.grid(row=row, column=2, padx=10, pady=5)
            self.param_entries[param_name] = (entry, label)
            
            row += 1
        
        # 按钮框架
        btn_frame = ttk.Frame(self.frame_params)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="重置参数", command=self.reset_params).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="应用参数", command=self.apply_params).pack(side=tk.LEFT, padx=5)
        
        # 参数说明（已修正缩进错误）
        说明文本 = """
        参数说明：
        - 敏感性参数：表示生态因子对环境因子变化的敏感程度
        - 相互作用参数：表示不同生态因子之间的相互影响强度
        - 影响系数：表示环境因子对生态系统的影响程度
        
        调整参数后请点击"应用参数"使设置生效。
        """
        ttk.Label(self.frame_params, text=说明文本, justify=tk.LEFT).pack(fill=tk.X, padx=10, pady=10)
    
    def format_param_name(self, param_name):
        """将参数名转换为易读格式（已修正重复键错误）"""
        param_map = {
            'fvc_temp_sens': 'FVC对温度的敏感性',
            'fvc_precip_sens': 'FVC对降水的敏感性',
            'ndvi_temp_sens': 'NDVI对温度的敏感性',
            'ndvi_precip_sens': 'NDVI对降水的敏感性',
            'npp_temp_sens': 'NPP对温度的敏感性',
            'npp_precip_sens': 'NPP对降水的敏感性',
            'fvc_ndvi_interact': 'FVC与NDVI的相互作用',
            'ndvi_npp_interact': 'NDVI与NPP的相互作用',
            'npp_fvc_interact': 'NPP与FVC的相互作用',
            'evap_coeff': '蒸发量影响系数',
            'sunshine_coeff': '日照时长影响系数',
            'water_level_coeff': '水位波动影响系数',
            'dem_coeff': '地形影响系数'
        }
        return param_map.get(param_name, param_name)
    
    def update_param_label(self, value, param_name):
        """更新参数值标签"""
        self.param_entries[param_name][1].config(text=f"{float(value):.4f}")
    
    def reset_params(self):
        """重置参数为默认值"""
        for param_name, (entry, label) in self.param_entries.items():
            default_value = self.model.params[param_name]
            entry.set(default_value)
            label.config(text=f"{default_value:.4f}")
    
    def apply_params(self):
        """应用当前参数设置"""
        for param_name, (entry, label) in self.param_entries.items():
            self.model.params[param_name] = float(entry.get())
        messagebox.showinfo("参数更新", "模型参数已更新")
    
    def import_data(self):
        """导入时间序列数据"""
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if self.model.load_data(file_path):
                self.update_data_table()
                self.data_info.config(text=f"已导入数据: {os.path.basename(file_path)}, 共 {len(self.model.data)} 条记录")
                messagebox.showinfo("导入成功", f"数据导入成功，共 {len(self.model.data)} 条记录")
    
    def import_dem_data(self):
        """导入DEM地形数据"""
        file_path = filedialog.askopenfilename(
            title="选择DEM数据文件",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if self.model.load_dem_data(file_path):
                self.data_info.config(text=f"已导入DEM数据: {os.path.basename(file_path)}, 共 {len(self.model.dem_data)} 条记录")
                messagebox.showinfo("导入成功", f"DEM数据导入成功，共 {len(self.model.dem_data)} 条记录")
    
    def export_data(self):
        """导出数据"""
        if self.model.data is None:
            messagebox.showwarning("无数据", "没有可导出的数据，请先导入数据")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存数据文件",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file_path:
            if self.model.save_data(file_path):
                messagebox.showinfo("导出成功", f"数据已成功保存到 {file_path}")
    
    def update_data_table(self):
        """更新数据表格显示"""
        # 清空现有数据
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # 设置列
        columns = list(self.model.data.columns)
        self.data_tree["columns"] = columns
        
        for col in columns:
            self.data_tree.heading(col, text=col)
            self.data_tree.column(col, width=100)
        
        # 添加数据行
        for _, row in self.model.data.iterrows():
            values = [str(row[col]) for col in columns]
            self.data_tree.insert("", tk.END, values=values)
    
    def run_simulation(self):
        """运行模拟并更新图表"""
        if self.model.run_simulation():
            self.simulation_status.config(text=f"模拟完成，时间范围: {self.model.years[0]} - {self.model.years[-1]}")
            self.update_simulation_plots()
    
    def update_simulation_plots(self):
        """更新模拟结果图表"""
        if self.model.simulation_results is None:
            return
        
        self.fig_simulation.clear()
        
        # 创建三个子图，分别显示FVC、NDVI和NPP的模拟值与实际值
        ax1 = self.fig_simulation.add_subplot(311)
        ax2 = self.fig_simulation.add_subplot(312)
        ax3 = self.fig_simulation.add_subplot(313)
        
        years = self.model.simulation_results['年份']
        
        # 绘制FVC
        if self.var_show_fvc.get():
            ax1.plot(years, self.model.simulation_results['FVC实际值'], 'bo-', label='实际值')
            ax1.plot(years, self.model.simulation_results['FVC模拟值'], 'r--', label='模拟值')
            ax1.set_title('FVC覆盖度指数')
            ax1.legend()
        
        # 绘制NDVI
        if self.var_show_ndvi.get():
            ax2.plot(years, self.model.simulation_results['NDVI实际值'], 'go-', label='实际值')
            ax2.plot(years, self.model.simulation_results['NDVI模拟值'], 'r--', label='模拟值')
            ax2.set_title('NDVI指数')
            ax2.legend()
        
        # 绘制NPP
        if self.var_show_npp.get():
            ax3.plot(years, self.model.simulation_results['NPP实际值'], 'mo-', label='实际值')
            ax3.plot(years, self.model.simulation_results['NPP模拟值'], 'r--', label='模拟值')
            ax3.set_title('NPP净初级生产力')
            ax3.legend()
        
        self.fig_simulation.tight_layout()
        self.canvas_simulation.draw()
    
    def save_simulation_results(self):
        """保存模拟结果"""
        if self.model.simulation_results is None:
            messagebox.showwarning("无结果", "没有可保存的模拟结果，请先运行模拟")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存模拟结果",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.model.simulation_results.to_csv(file_path, index=False)
                elif file_path.endswith('.xlsx'):
                    self.model.simulation_results.to_excel(file_path, index=False)
                messagebox.showinfo("保存成功", f"模拟结果已成功保存到 {file_path}")
            except Exception as e:
                messagebox.showerror("保存错误", f"保存模拟结果时发生错误: {str(e)}")
    
    def show_statistical_summary(self):
        """显示统计摘要"""
        summary = self.model.get_statistical_summary()
        if summary is None:
            messagebox.showwarning("无数据", "请先导入数据")
            return
        
        # 清空现有内容
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        # 设置列
        columns = ['统计量'] + list(summary.columns)
        self.summary_tree["columns"] = columns
        
        for col in columns:
            self.summary_tree.heading(col, text=col)
            self.summary_tree.column(col, width=100)
        
        # 添加数据行
        for idx, row in summary.iterrows():
            values = [idx] + list(row.values)
            self.summary_tree.insert("", tk.END, values=values)
        
        self.analysis_notebook.select(self.frame_summary)
        self.analysis_status.config(text="显示统计摘要")
    
    def show_correlation_analysis(self):
        """显示相关性分析热图"""
        corr = self.model.get_correlation_analysis()
        if corr is None:
            messagebox.showwarning("无数据", "请先导入数据")
            return
        
        self.fig_correlation.clear()
        ax = self.fig_correlation.add_subplot(111)
        
        # 绘制相关性热图
        sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax)
        ax.set_title("变量间相关性热图")
        
        self.fig_correlation.tight_layout()
        self.canvas_correlation.draw()
        
        self.analysis_notebook.select(self.frame_correlation)
        self.analysis_status.config(text="显示相关性分析结果")
    
    def run_regression_analysis(self):
        """运行回归分析并显示结果"""
        dependent = self.dependent_var.get()
        independents = ["年均气温", "降水量", "蒸发量", "日照时长", "水位波动"]
        
        result = self.model.get_regression_analysis(dependent, independents)
        if result is None:
            return
        
        # 清空现有内容
        self.regression_text.delete(1.0, tk.END)
        self.regression_text.insert(tk.END, str(result))
        
        self.analysis_notebook.select(self.frame_regression)
        self.analysis_status.config(text=f"显示以{self.dependent_var.get()}为因变量的回归分析结果")
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
        生态系统动力学模型分析工具 v1.0
        
        该工具用于分析生态系统因子（FVC、NDVI、NPP）与气象因子、地形因子之间的关系，
        通过系统动力学模型模拟生态系统动态变化。
        
        支持数据导入导出、模型模拟、统计分析等功能。
        """
        messagebox.showinfo("关于", about_text)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
        使用帮助:
        
        1. 数据管理:
           - 导入时间序列数据（包含年份、FVC、NDVI、NPP、气象数据等）
           - 导入DEM地形数据
           - 查看和导出数据
        
        2. 模型模拟:
           - 加载数据后点击"运行模拟"
           - 可选择显示不同的生态因子
           - 模拟结果可导出保存
        
        3. 统计分析:
           - 统计摘要：显示各变量的基本统计信息
           - 相关性分析：显示变量间的相关性热图
           - 回归分析：分析生态因子与气象因子的回归关系
        
        4. 参数设置:
           - 可调整模型参数
           - 调整后需点击"应用参数"使设置生效
        """
        messagebox.showinfo("使用帮助", help_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = EcosystemModelGUI(root)

    root.mainloop()
