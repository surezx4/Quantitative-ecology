import sys
import os
import numpy as np
import geopandas as gpd
import rasterio
from rasterio import features
from shapely.geometry import Polygon, MultiPolygon, box, shape
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Arrow
from matplotlib import cm
import matplotlib.colors as mcolors
from matplotlib import font_manager as fm

# 设置中文字体支持
try:
    # 尝试使用系统中文字体
    chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'FangSong', 'KaiTi']
    for font_name in chinese_fonts:
        if any(f.name == font_name for f in fm.fontManager.ttflist):
            plt.rcParams['font.sans-serif'] = [font_name]
            plt.rcParams['axes.unicode_minus'] = False
            break
    else:
        # 如果没有找到中文字体，尝试使用默认字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
except:
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QFileDialog, QMessageBox, QSpinBox,
                             QProgressBar, QGroupBox, QTextEdit, QDockWidget, QSizePolicy,
                             QComboBox, QCheckBox, QDoubleSpinBox, QTabWidget, QDialog,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
                             QToolBar, QAction, QMenu, QMenuBar, QStatusBar, QToolButton,
                             QDialogButtonBox, QLineEdit, QListWidget, QListView, QGridLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QSettings
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QPainter

# Unicode符号定义
RED_LIGHT = "🔴"
BLUE_LIGHT = "🔵"
GREEN_LIGHT = "🟢"

# 应用设置
APP_NAME = "ProfessionalGISGridTool"
ORG_NAME = "GeoDataLab"

class DataInfoDialog(QDialog):
    """数据显示信息对话框"""
    def __init__(self, data_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据信息")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 创建表格显示数据信息
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["属性", "值"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        # 填充数据
        self.table.setRowCount(len(data_info))
        for i, (key, value) in enumerate(data_info.items()):
            self.table.setItem(i, 0, QTableWidgetItem(str(key)))
            self.table.setItem(i, 1, QTableWidgetItem(str(value)))
        
        layout.addWidget(self.table)
        
        # 添加关闭按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

class FieldSelectionDialog(QDialog):
    """字段选择对话框"""
    def __init__(self, fields, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择出图字段")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("请选择用于专题图渲染的字段:"))
        
        self.field_list = QListWidget()
        for field in fields:
            self.field_list.addItem(field)
        layout.addWidget(self.field_list)
        
        # 添加按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def selected_field(self):
        """获取选中的字段"""
        if self.field_list.currentItem():
            return self.field_list.currentItem().text()
        return None

class PreviewCanvas(FigureCanvas):
    """预览画布类"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()
        
        # 设置样式
        self.ax.set_facecolor('#f0f0f0')
        self.fig.patch.set_facecolor('#d0d0d0')
        
    def clear(self):
        """清除画布"""
        self.ax.clear()
        self.draw()
    
    def add_north_arrow(self, x, y, size, color='black'):
        """添加指北针"""
        arrow = Arrow(x, y, 0, size, width=size*0.3, color=color)
        self.ax.add_patch(arrow)
        self.ax.text(x, y - size*0.5, 'N', ha='center', va='top', fontweight='bold')
    
    def add_scale_bar(self, x, y, length, units='m', color='black'):
        """添加比例尺"""
        # 绘制比例尺主线
        self.ax.plot([x, x + length], [y, y], color=color, linewidth=3)
        
        # 绘制刻度
        for i in range(0, 6):
            pos = x + i * length / 5
            self.ax.plot([pos, pos], [y, y - length/20], color=color, linewidth=1)
        
        # 添加标签
        label = f"{length} {units}"
        self.ax.text(x + length/2, y - length/10, label, ha='center', va='top')
    
    def add_grid(self, bounds, crs):
        """添加经纬度网格"""
        if crs and crs.is_geographic:
            # 如果是地理坐标系，添加经纬网格
            minx, miny, maxx, maxy = bounds
            
            # 计算合适的网格间隔
            x_interval = max(0.1, round((maxx - minx) / 5, 1))
            y_interval = max(0.1, round((maxy - miny) / 5, 1))
            
            # 生成网格线
            x_ticks = np.arange(np.floor(minx), np.ceil(maxx) + x_interval, x_interval)
            y_ticks = np.arange(np.floor(miny), np.ceil(maxy) + y_interval, y_interval)
            
            # 绘制网格线
            for x in x_ticks:
                self.ax.axvline(x=x, color='gray', linestyle='--', alpha=0.5)
            for y in y_ticks:
                self.ax.axhline(y=y, color='gray', linestyle='--', alpha=0.5)
            
            # 设置刻度
            self.ax.set_xticks(x_ticks)
            self.ax.set_yticks(y_ticks)
            
            # 添加标签
            self.ax.set_xlabel('经度')
            self.ax.set_ylabel('纬度')
        
        self.ax.grid(True, alpha=0.3)

class GridWorker(QThread):
    """后台工作线程，用于网格划分操作"""
    progress_updated = pyqtSignal(int)
    message_emitted = pyqtSignal(str)
    finished = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, data, data_type, grid_size, grid_units, stat_method="mean", band_index=1, keep_original_attributes=True):
        super().__init__()
        self.data = data
        self.data_type = data_type  # "vector" 或 "raster"
        self.grid_size = grid_size
        self.grid_units = grid_units
        self.stat_method = stat_method
        self.band_index = band_index
        self.keep_original_attributes = keep_original_attributes

    def run(self):
        try:
            if self.data_type == "vector":
                self.process_vector()
            elif self.data_type == "raster":
                self.process_raster()
            else:
                self.error_occurred.emit(f"未知的数据类型: {self.data_type}")
                
        except Exception as e:
            self.error_occurred.emit(str(e))

    def process_vector(self):
        """处理矢量数据"""
        self.message_emitted.emit("开始矢量数据网格划分...")
        gdf = self.data
        
        # 获取数据边界
        total_bounds = gdf.total_bounds
        minx, miny, maxx, maxy = total_bounds
        
        self.message_emitted.emit(f"数据边界: X({minx:.2f}~{maxx:.2f}), Y({miny:.2f}~{maxy:.2f})")
        
        # 计算网格行列数
        cols = int(np.ceil((maxx - minx) / self.grid_size))
        rows = int(np.ceil((maxy - miny) / self.grid_size))
        
        self.message_emitted.emit(f"将生成 {rows} 行 x {cols} 列的网格，共 {rows * cols} 个单元")
        
        # 创建网格
        grid_polygons = []
        attributes = []
        
        total_cells = rows * cols
        processed = 0
        
        for i in range(rows):
            for j in range(cols):
                # 计算当前网格的边界
                x1 = minx + j * self.grid_size
                x2 = minx + (j + 1) * self.grid_size
                y1 = miny + i * self.grid_size
                y2 = miny + (i + 1) * self.grid_size
                
                # 创建网格多边形
                grid_cell = box(x1, y1, x2, y2)
                
                # 查找与当前网格相交的原始要素
                intersecting_features = gdf[gdf.intersects(grid_cell)]
                
                if not intersecting_features.empty:
                    # 计算每个字段的统计值
                    attr_dict = {}
                    
                    if self.keep_original_attributes:
                        # 保留原始属性
                        for col in gdf.columns:
                            if col != 'geometry':
                                try:
                                    # 对于每个字段，使用第一个相交要素的值
                                    attr_dict[col] = intersecting_features[col].iloc[0]
                                except:
                                    attr_dict[col] = None
                    else:
                        # 计算统计值
                        for col in gdf.columns:
                            if col != 'geometry' and col != 'id':
                                try:
                                    # 尝试计算数值字段的统计值
                                    if intersecting_features[col].dtype in [np.int64, np.float64]:
                                        if self.stat_method == "mean":
                                            attr_dict[col] = intersecting_features[col].mean()
                                        elif self.stat_method == "sum":
                                            attr_dict[col] = intersecting_features[col].sum()
                                        elif self.stat_method == "max":
                                            attr_dict[col] = intersecting_features[col].max()
                                        elif self.stat_method == "min":
                                            attr_dict[col] = intersecting_features[col].min()
                                        elif self.stat_method == "count":
                                            attr_dict[col] = intersecting_features[col].count()
                                        elif self.stat_method == "std":
                                            attr_dict[col] = intersecting_features[col].std()
                                        elif self.stat_method == "median":
                                            attr_dict[col] = intersecting_features[col].median()
                                    else:
                                        # 对于非数值字段，使用第一个相交要素的值
                                        attr_dict[col] = intersecting_features[col].iloc[0]
                                except:
                                    attr_dict[col] = None
                    
                    grid_polygons.append(grid_cell)
                    attributes.append(attr_dict)
                
                processed += 1
                progress = int(processed / total_cells * 100)
                self.progress_updated.emit(progress)
        
        # 创建网格GeoDataFrame
        grid_gdf = gpd.GeoDataFrame(attributes, geometry=grid_polygons, crs=gdf.crs)
        
        self.message_emitted.emit(f"矢量数据网格划分完成，共生成 {len(grid_gdf)} 个有效网格")
        self.finished.emit(grid_gdf)

    def process_raster(self):
        """处理栅格数据"""
        self.message_emitted.emit("开始栅格数据网格划分...")
        raster_data, raster_meta = self.data
        
        # 获取数据边界
        transform = raster_meta['transform']
        width = raster_meta['width']
        height = raster_meta['height']
        
        minx = transform[2]
        maxy = transform[5]
        maxx = minx + width * transform[0]
        miny = maxy + height * transform[4]
        
        self.message_emitted.emit(f"数据边界: X({minx:.2f}~{maxx:.2f}), Y({miny:.2f}~{maxy:.2f})")
        
        # 计算网格行列数
        cols = int(np.ceil((maxx - minx) / self.grid_size))
        rows = int(np.ceil((maxy - miny) / self.grid_size))
        
        self.message_emitted.emit(f"将生成 {rows} 行 x {cols} 列的网格，共 {rows * cols} 个单元")
        
        # 创建网格
        grid_polygons = []
        attributes = []
        
        total_cells = rows * cols
        processed = 0
        
        for i in range(rows):
            for j in range(cols):
                # 计算当前网格的边界
                x1 = minx + j * self.grid_size
                x2 = minx + (j + 1) * self.grid_size
                y1 = miny + i * self.grid_size
                y2 = miny + (i + 1) * self.grid_size
                
                # 创建网格多边形
                grid_cell = box(x1, y1, x2, y2)
                
                # 计算网格内的像素值统计
                # 首先找到网格覆盖的像素范围
                col_start = int((x1 - minx) / transform[0])
                col_end = int((x2 - minx) / transform[0])
                row_start = int((y1 - maxy) / transform[4])  # transform[4]是负值
                row_end = int((y2 - maxy) / transform[4])
                
                # 确保不超出图像范围
                col_start = max(0, min(col_start, width))
                col_end = max(0, min(col_end, width))
                row_start = max(0, min(row_start, height))
                row_end = max(0, min(row_end, height))
                
                if col_end > col_start and row_end > row_start:
                    # 提取网格内的像素值
                    cell_values = raster_data[row_start:row_end, col_start:col_end]
                    
                    # 计算统计值（忽略NaN值）
                    if cell_values.size > 0:
                        valid_values = cell_values[~np.isnan(cell_values)]
                        
                        if valid_values.size > 0:
                            if self.stat_method == "mean":
                                stat_value = np.mean(valid_values)
                            elif self.stat_method == "sum":
                                stat_value = np.sum(valid_values)
                            elif self.stat_method == "max":
                                stat_value = np.max(valid_values)
                            elif self.stat_method == "min":
                                stat_value = np.min(valid_values)
                            elif self.stat_method == "count":
                                stat_value = valid_values.size
                            elif self.stat_method == "std":
                                stat_value = np.std(valid_values)
                            elif self.stat_method == "median":
                                stat_value = np.median(valid_values)
                            
                            attr_dict = {"value": stat_value}
                            grid_polygons.append(grid_cell)
                            attributes.append(attr_dict)
                
                processed += 1
                progress = int(processed / total_cells * 100)
                self.progress_updated.emit(progress)
        
        # 创建网格GeoDataFrame
        grid_gdf = gpd.GeoDataFrame(attributes, geometry=grid_polygons)
        # 设置CRS（如果栅格数据有CRS信息）
        if raster_meta.get('crs'):
            grid_gdf.crs = raster_meta['crs']
        
        self.message_emitted.emit(f"栅格数据网格划分完成，共生成 {len(grid_gdf)} 个有效网格")
        self.finished.emit(grid_gdf)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("专业GIS数据网格划分工具")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化变量
        self.input_data = None
        self.data_type = None  # "vector" 或 "raster"
        self.output_gdf = None
        self.selected_field = None  # 用户选择的出图字段
        self.settings = QSettings(ORG_NAME, APP_NAME)
        
        # 设置应用样式
        self.setup_style()
        
        self.setup_ui()
        
        # 加载设置
        self.load_settings()
        
    def setup_style(self):
        """设置应用样式"""
        # 使用Fusion样式
        QApplication.setStyle("Fusion")
        
        # 创建调色板
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        
        QApplication.setPalette(palette)
        
    def setup_ui(self):
        # 创建菜单栏
        self.setup_menubar()
        
        # 创建工具栏
        self.setup_toolbar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧面板
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        # 创建标题
        title_label = QLabel("专业GIS数据网格划分工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("background-color: #2a82da; color: white; padding: 10px;")
        left_layout.addWidget(title_label)
        
        # 创建封面符号
        cover_label = QLabel(f"{RED_LIGHT} {BLUE_LIGHT} {GREEN_LIGHT}")
        cover_label.setAlignment(Qt.AlignCenter)
        cover_font = QFont()
        cover_font.setPointSize(30)
        cover_label.setFont(cover_font)
        cover_label.setStyleSheet("background-color: #353535; padding: 10px;")
        left_layout.addWidget(cover_label)
        
        # 创建输入组
        input_group = QGroupBox("数据输入")
        input_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        input_layout = QVBoxLayout(input_group)
        
        # 文件类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("数据类型:"))
        
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItem("SHP矢量数据", "vector")
        self.data_type_combo.addItem("TIFF栅格数据", "raster")
        type_layout.addWidget(self.data_type_combo)
        
        type_layout.addStretch()
        input_layout.addLayout(type_layout)
        
        self.import_btn = QPushButton("导入数据文件")
        self.import_btn.clicked.connect(self.import_data)
        self.import_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogOpenButton')))
        input_layout.addWidget(self.import_btn)
        
        self.info_btn = QPushButton("显示数据信息")
        self.info_btn.clicked.connect(self.show_data_info)
        self.info_btn.setEnabled(False)
        self.info_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_MessageBoxInformation')))
        input_layout.addWidget(self.info_btn)
        
        self.file_info = QLabel("未导入任何文件")
        self.file_info.setWordWrap(True)
        self.file_info.setStyleSheet("background-color: #252525; padding: 5px; border: 1px solid #555;")
        input_layout.addWidget(self.file_info)
        
        left_layout.addWidget(input_group)
        
        # 创建网格设置组
        grid_group = QGroupBox("网格设置")
        grid_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        grid_layout = QVBoxLayout(grid_group)
        
        # 网格大小设置
        size_layout = QGridLayout()
        size_layout.addWidget(QLabel("网格大小:"), 0, 0)
        
        self.grid_size = QDoubleSpinBox()
        self.grid_size.setRange(0.1, 10000)
        self.grid_size.setValue(100)
        self.grid_size.setDecimals(2)
        size_layout.addWidget(self.grid_size, 0, 1)
        
        self.grid_units = QComboBox()
        self.grid_units.addItems(["米", "千米", "度"])
        size_layout.addWidget(self.grid_units, 0, 2)
        
        size_layout.addWidget(QLabel("统计方法:"), 1, 0)
        
        self.stat_method = QComboBox()
        self.stat_method.addItem("平均值", "mean")
        self.stat_method.addItem("总和", "sum")
        self.stat_method.addItem("最大值", "max")
        self.stat_method.addItem("最小值", "min")
        self.stat_method.addItem("计数", "count")
        self.stat_method.addItem("标准差", "std")
        self.stat_method.addItem("中位数", "median")
        size_layout.addWidget(self.stat_method, 1, 1, 1, 2)
        
        # 波段选择（仅对栅格数据有效）
        size_layout.addWidget(QLabel("波段:"), 2, 0)
        
        self.band_combo = QComboBox()
        self.band_combo.addItem("波段 1", 1)
        size_layout.addWidget(self.band_combo, 2, 1, 1, 2)
        
        # 属性保留选项
        self.keep_attrs_check = QCheckBox("保留原始属性")
        self.keep_attrs_check.setChecked(True)
        size_layout.addWidget(self.keep_attrs_check, 3, 0, 1, 3)
        
        grid_layout.addLayout(size_layout)
        
        self.process_btn = QPushButton("执行网格划分")
        self.process_btn.clicked.connect(self.process_data)
        self.process_btn.setEnabled(False)
        self.process_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_MediaPlay')))
        grid_layout.addWidget(self.process_btn)
        
        left_layout.addWidget(grid_group)
        
        # 创建输出组
        output_group = QGroupBox("数据输出")
        output_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        output_layout = QVBoxLayout(output_group)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("输出格式:"))
        
        self.output_format = QComboBox()
        self.output_format.addItem("ESRI Shapefile", "shp")
        self.output_format.addItem("GeoJSON", "geojson")
        self.output_format.addItem("KML", "kml")
        format_layout.addWidget(self.output_format)
        
        format_layout.addStretch()
        output_layout.addLayout(format_layout)
        
        self.export_btn = QPushButton("导出数据")
        self.export_btn.clicked.connect(self.export_data)
        self.export_btn.setEnabled(False)
        self.export_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')))
        output_layout.addWidget(self.export_btn)
        
        left_layout.addWidget(output_group)
        
        # 添加到主布局
        main_layout.addWidget(left_panel)
        
        # 创建右侧预览区域
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 创建预览选项卡
        self.preview_tabs = QTabWidget()
        
        # 原始数据预览
        self.original_preview = PreviewCanvas(self, width=6, height=5)
        self.preview_tabs.addTab(self.original_preview, "原始数据预览")
        
        # 网格数据预览
        self.grid_preview = PreviewCanvas(self, width=6, height=5)
        self.preview_tabs.addTab(self.grid_preview, "网格数据预览")
        
        right_layout.addWidget(self.preview_tabs)
        
        # 添加出图按钮
        self.plot_btn = QPushButton("生成专题图")
        self.plot_btn.clicked.connect(self.generate_plot)
        self.plot_btn.setEnabled(False)
        self.plot_btn.setIcon(self.style().standardIcon(getattr(self.style(), 'SP_FileDialogDetailedView')))
        right_layout.addWidget(self.plot_btn)
        
        main_layout.addWidget(right_panel, 1)  # 1表示拉伸因子
        
        # 创建进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
        
        # 创建日志窗口
        log_dock = QDockWidget("处理日志", self)
        log_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_dock.setWidget(self.log_text)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)
        
        # 添加状态栏
        self.statusBar().showMessage("就绪")
        
    def setup_menubar(self):
        """设置菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        import_action = QAction("导入数据", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        export_action = QAction("导出数据", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tool_menu = menubar.addMenu("工具")
        
        process_action = QAction("执行网格划分", self)
        process_action.setShortcut("Ctrl+G")
        process_action.triggered.connect(self.process_data)
        tool_menu.addAction(process_action)
        
        plot_action = QAction("生成专题图", self)
        plot_action.setShortcut("Ctrl+P")
        plot_action.triggered.connect(self.generate_plot)
        tool_menu.addAction(plot_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图")
        
        log_action = QAction("显示/隐藏日志", self)
        log_action.setShortcut("Ctrl+L")
        log_action.triggered.connect(self.toggle_log)
        view_menu.addAction(log_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # 导入按钮
        import_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_DialogOpenButton')), "导入数据", self)
        import_action.triggered.connect(self.import_data)
        toolbar.addAction(import_action)
        
        # 处理按钮
        process_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_MediaPlay')), "执行网格划分", self)
        process_action.triggered.connect(self.process_data)
        toolbar.addAction(process_action)
        
        toolbar.addSeparator()
        
        # 导出按钮
        export_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_DialogSaveButton')), "导出数据", self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)
        
        # 出图按钮
        plot_action = QAction(self.style().standardIcon(getattr(self.style(), 'SP_FileDialogDetailedView')), "生成专题图", self)
        plot_action.triggered.connect(self.generate_plot)
        toolbar.addAction(plot_action)
        
    def load_settings(self):
        """加载应用设置"""
        # 加载网格大小和单位
        grid_size = self.settings.value("grid_size", 100.0, type=float)
        grid_units_index = self.settings.value("grid_units_index", 0, type=int)
        
        self.grid_size.setValue(grid_size)
        self.grid_units.setCurrentIndex(grid_units_index)
        
        # 加载统计方法
        stat_method_index = self.settings.value("stat_method_index", 0, type=int)
        self.stat_method.setCurrentIndex(stat_method_index)
        
        # 加载输出格式
        output_format_index = self.settings.value("output_format_index", 0, type=int)
        self.output_format.setCurrentIndex(output_format_index)
        
        # 加载属性保留选项
        keep_attrs = self.settings.value("keep_attrs", True, type=bool)
        self.keep_attrs_check.setChecked(keep_attrs)
        
    def save_settings(self):
        """保存应用设置"""
        # 保存网格设置
        self.settings.setValue("grid_size", self.grid_size.value())
        self.settings.setValue("grid_units_index", self.grid_units.currentIndex())
        
        # 保存统计方法
        self.settings.setValue("stat_method_index", self.stat_method.currentIndex())
        
        # 保存输出格式
        self.settings.setValue("output_format_index", self.output_format.currentIndex())
        
        # 保存属性保留选项
        self.settings.setValue("keep_attrs", self.keep_attrs_check.isChecked())
        
    def closeEvent(self, event):
        """应用关闭事件"""
        self.save_settings()
        event.accept()
        
    def import_data(self):
        data_type = self.data_type_combo.currentData()
        
        if data_type == "vector":
            file_filter = "Shapefile (*.shp)"
        else:  # raster
            file_filter = "GeoTIFF (*.tif *.tiff);;所有文件 (*)"
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"选择{data_type.upper()}文件", "", file_filter
        )
        
        if file_path:
            try:
                self.log_message(f"正在导入文件: {file_path}")
                
                if data_type == "vector":
                    self.input_data = gpd.read_file(file_path)
                    self.data_type = "vector"
                    
                    # 显示文件信息
                    num_features = len(self.input_data)
                    bounds = self.input_data.total_bounds
                    crs = self.input_data.crs
                    
                    info_text = f"已导入矢量数据: {os.path.basename(file_path)}\n"
                    info_text += f"要素数量: {num_features}\n"
                    info_text += f"坐标系统: {crs}\n"
                    info_text += f"数据范围: X({bounds[0]:.2f}~{bounds[2]:.2f}), Y({bounds[1]:.2f}~{bounds[3]:.2f})"
                    
                    # 预览原始数据
                    self.preview_original_data()
                    
                else:  # raster
                    with rasterio.open(file_path) as src:
                        # 读取所有波段的信息
                        num_bands = src.count
                        raster_data = src.read(1)  # 默认读取第一个波段
                        raster_meta = src.meta.copy()
                    
                    self.input_data = (raster_data, raster_meta)
                    self.data_type = "raster"
                    
                    # 更新波段选择
                    self.band_combo.clear()
                    for i in range(1, num_bands + 1):
                        self.band_combo.addItem(f"波段 {i}", i)
                    
                    # 显示文件信息
                    transform = raster_meta['transform']
                    width = raster_meta['width']
                    height = raster_meta['height']
                    crs = raster_meta.get('crs', '未知')
                    
                    minx = transform[2]
                    maxy = transform[5]
                    maxx = minx + width * transform[0]
                    miny = maxy + height * transform[4]
                    
                    info_text = f"已导入栅格数据: {os.path.basename(file_path)}\n"
                    info_text += f"尺寸: {width} x {height} 像素\n"
                    info_text += f"波段数: {num_bands}\n"
                    info_text += f"坐标系统: {crs}\n"
                    info_text += f"数据范围: X({minx:.2f}~{maxx:.2f}), Y({miny:.2f}~{maxy:.2f})"
                    
                    # 预览原始数据
                    self.preview_original_data()
                
                self.file_info.setText(info_text)
                self.process_btn.setEnabled(True)
                self.info_btn.setEnabled(True)
                self.log_message("文件导入成功")
                
            except Exception as e:
                self.log_message(f"导入失败: {str(e)}", error=True)
                QMessageBox.critical(self, "错误", f"导入文件失败:\n{str(e)}")
    
    def preview_original_data(self):
        """预览原始数据"""
        self.original_preview.clear()
        
        if self.data_type == "vector":
            gdf = self.input_data
            bounds = gdf.total_bounds
            
            # 绘制数据
            gdf.plot(ax=self.original_preview.ax, edgecolor='blue', facecolor='none', linewidth=0.5)
            
            # 添加网格和装饰
            self.original_preview.add_grid(bounds, gdf.crs)
            
        else:  # raster
            raster_data, raster_meta = self.input_data
            transform = raster_meta['transform']
            
            # 计算边界
            minx = transform[2]
            maxy = transform[5]
            maxx = minx + raster_meta['width'] * transform[0]
            miny = maxy + raster_meta['height'] * transform[4]
            bounds = (minx, miny, maxx, maxy)
            
            # 绘制数据
            im = self.original_preview.ax.imshow(
                raster_data, 
                extent=[minx, maxx, miny, maxy],
                cmap='viridis'
            )
            
            # 添加颜色条
            self.original_preview.fig.colorbar(im, ax=self.original_preview.ax)
            
            # 添加网格和装饰
            self.original_preview.add_grid(bounds, raster_meta.get('crs'))
        
        # 添加指北针和比例尺
        self.original_preview.add_north_arrow(
            bounds[0] + (bounds[2] - bounds[0]) * 0.1,
            bounds[1] + (bounds[3] - bounds[1]) * 0.9,
            (bounds[2] - bounds[0]) * 0.05
        )
        
        scale_length = (bounds[2] - bounds[0]) * 0.2
        self.original_preview.add_scale_bar(
            bounds[0] + (bounds[2] - bounds[0]) * 0.1,
            bounds[1] + (bounds[3] - bounds[1]) * 0.1,
            scale_length,
            'm' if self.grid_units.currentText() == "米" else 
            'km' if self.grid_units.currentText() == "千米" else '度'
        )
        
        # 设置标题
        self.original_preview.ax.set_title("原始数据预览")
        
        # 刷新画布
        self.original_preview.draw()
    
    def preview_grid_data(self):
        """预览网格数据"""
        if self.output_gdf is None:
            return
            
        self.grid_preview.clear()
        
        bounds = self.output_gdf.total_bounds
        
        # 绘制网格数据
        # 选择一个数值字段进行可视化
        value_column = self.selected_field
        if not value_column:
            # 如果没有选择字段，尝试自动选择一个
            for col in self.output_gdf.columns:
                if col != 'geometry' and self.output_gdf[col].dtype in [np.int64, np.float64]:
                    value_column = col
                    break
        
        if value_column and value_column in self.output_gdf.columns:
            # 使用颜色映射
            try:
                cmap = plt.colormaps['viridis']
            except:
                cmap = cm.get_cmap('viridis')
                
            norm = mcolors.Normalize(
                vmin=self.output_gdf[value_column].min(),
                vmax=self.output_gdf[value_column].max()
            )
            
            for idx, row in self.output_gdf.iterrows():
                color = cmap(norm(row[value_column]))
                self.grid_preview.ax.fill(
                    *row.geometry.exterior.xy, 
                    facecolor=color, 
                    edgecolor='black', 
                    linewidth=0.5,
                    alpha=0.7
                )
            
            # 添加颜色条
            sm = cm.ScalarMappable(norm=norm, cmap=cmap)
            sm.set_array([])
            self.grid_preview.fig.colorbar(sm, ax=self.grid_preview.ax, label=value_column)
        else:
            # 如果没有数值字段，使用单一颜色
            for idx, row in self.output_gdf.iterrows():
                self.grid_preview.ax.fill(
                    *row.geometry.exterior.xy, 
                    facecolor='lightblue', 
                    edgecolor='black', 
                    linewidth=0.5,
                    alpha=0.7
                )
        
        # 添加网格和装饰
        self.grid_preview.add_grid(bounds, self.output_gdf.crs)
        
        # 添加指北针和比例尺
        self.grid_preview.add_north_arrow(
            bounds[0] + (bounds[2] - bounds[0]) * 0.1,
            bounds[1] + (bounds[3] - bounds[1]) * 0.9,
            (bounds[2] - bounds[0]) * 0.05
        )
        
        scale_length = (bounds[2] - bounds[0]) * 0.2
        self.grid_preview.add_scale_bar(
            bounds[0] + (bounds[2] - bounds[0]) * 0.1,
            bounds[1] + (bounds[3] - bounds[1]) * 0.1,
            scale_length,
            'm' if self.grid_units.currentText() == "米" else 
            'km' if self.grid_units.currentText() == "千米" else '度'
        )
        
        # 设置标题
        self.grid_preview.ax.set_title("网格数据预览")
        
        # 刷新画布
        self.grid_preview.draw()
    
    def show_data_info(self):
        """显示数据信息对话框"""
        if self.input_data is None:
            return
            
        data_info = {}
        
        if self.data_type == "vector":
            gdf = self.input_data
            data_info["数据类型"] = "矢量数据 (SHP)"
            data_info["要素数量"] = len(gdf)
            data_info["坐标系统"] = str(gdf.crs)
            
            bounds = gdf.total_bounds
            data_info["X范围"] = f"{bounds[0]:.6f} ~ {bounds[2]:.6f}"
            data_info["Y范围"] = f"{bounds[1]:.6f} ~ {bounds[3]:.6f}"
            data_info["宽度"] = f"{bounds[2] - bounds[0]:.2f}"
            data_info["高度"] = f"{bounds[3] - bounds[1]:.2f}"
            
            # 字段信息
            for col in gdf.columns:
                if col != 'geometry':
                    dtype = gdf[col].dtype
                    data_info[f"字段 '{col}'"] = f"{dtype}, {gdf[col].notna().sum()} 个有效值"
            
        else:  # raster
            raster_data, raster_meta = self.input_data
            data_info["数据类型"] = "栅格数据 (TIFF)"
            data_info["尺寸"] = f"{raster_meta['width']} x {raster_meta['height']} 像素"
            data_info["波段数"] = raster_meta.get('count', 1)
            data_info["坐标系统"] = str(raster_meta.get('crs', '未知'))
            
            transform = raster_meta['transform']
            minx = transform[2]
            maxy = transform[5]
            maxx = minx + raster_meta['width'] * transform[0]
            miny = maxy + raster_meta['height'] * transform[4]
            
            data_info["X范围"] = f"{minx:.6f} ~ {maxx:.6f}"
            data_info["Y范围"] = f"{miny:.6f} ~ {maxy:.6f}"
            data_info["宽度"] = f"{maxx - minx:.2f}"
            data_info["高度"] = f"{maxy - miny:.2f}"
            
            # 数据统计
            data_info["最小值"] = f"{np.nanmin(raster_data):.4f}"
            data_info["最大值"] = f"{np.nanmax(raster_data):.4f}"
            data_info["平均值"] = f"{np.nanmean(raster_data):.4f}"
            data_info["标准差"] = f"{np.nanstd(raster_data):.4f}"
        
        # 显示对话框
        dialog = DataInfoDialog(data_info, self)
        dialog.exec_()
    
    def process_data(self):
        if self.input_data is None:
            self.log_message("错误: 没有导入任何数据", error=True)
            return
        
        # 获取网格大小并转换为米（如果是度或千米）
        grid_size = self.grid_size.value()
        units = self.grid_units.currentText()
        
        if units == "千米":
            grid_size *= 1000  # 转换为米
        elif units == "度":
            # 对于地理坐标系，度转换为米的近似值（在赤道附近）
            grid_size *= 111320  # 1度约等于111.32公里
        
        stat_method = self.stat_method.currentData()
        band_index = self.band_combo.currentData() if self.data_type == "raster" else 1
        keep_original_attributes = self.keep_attrs_check.isChecked()
        
        self.log_message(f"开始处理数据，网格大小: {self.grid_size.value()} {units}, 统计方法: {stat_method}")
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 禁用按钮防止重复操作
        self.import_btn.setEnabled(False)
        self.process_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        self.plot_btn.setEnabled(False)
        
        # 创建工作线程
        self.worker = GridWorker(
            self.input_data, self.data_type, grid_size, units, 
            stat_method, band_index, keep_original_attributes
        )
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.message_emitted.connect(self.log_message)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.error_occurred.connect(self.on_processing_error)
        self.worker.start()
    
    def on_processing_finished(self, result_gdf):
        self.output_gdf = result_gdf
        self.progress_bar.setValue(100)
        
        # 启用按钮
        self.import_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        self.plot_btn.setEnabled(True)
        
        # 重置选择的字段
        self.selected_field = None
        
        # 预览网格数据
        self.preview_grid_data()
        
        self.log_message("数据处理完成")
        QMessageBox.information(self, "完成", "网格划分处理已完成")
    
    def on_processing_error(self, error_msg):
        self.log_message(f"处理错误: {error_msg}", error=True)
        
        # 启用按钮
        self.import_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "错误", f"处理过程中发生错误:\n{error_msg}")
    
    def export_data(self):
        if self.output_gdf is None:
            self.log_message("错误: 没有可导出的数据", error=True)
            return
        
        output_format = self.output_format.currentData()
        
        if output_format == "shp":
            file_filter = "ESRI Shapefile (*.shp)"
        elif output_format == "geojson":
            file_filter = "GeoJSON (*.geojson)"
        elif output_format == "kml":
            file_filter = "KML (*.kml)"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", file_filter
        )
        
        if file_path:
            try:
                self.log_message(f"正在导出文件: {file_path}")
                
                if output_format == "shp":
                    self.output_gdf.to_file(file_path)
                elif output_format == "geojson":
                    self.output_gdf.to_file(file_path, driver='GeoJSON')
                elif output_format == "kml":
                    self.output_gdf.to_file(file_path, driver='KML')
                
                self.log_message("文件导出成功")
                QMessageBox.information(self, "成功", "文件导出成功")
                
            except Exception as e:
                self.log_message(f"导出失败: {str(e)}", error=True)
                QMessageBox.critical(self, "错误", f"导出文件失败:\n{str(e)}")
    
    def generate_plot(self):
        """生成专题图"""
        if self.output_gdf is None:
            self.log_message("错误: 没有可绘制的数据", error=True)
            return
        
        # 获取可用的数值字段
        numeric_fields = []
        for col in self.output_gdf.columns:
            if col != 'geometry' and self.output_gdf[col].dtype in [np.int64, np.float64]:
                numeric_fields.append(col)
        
        if not numeric_fields:
            QMessageBox.warning(self, "警告", "没有可用的数值字段用于生成专题图")
            return
        
        # 让用户选择字段
        dialog = FieldSelectionDialog(numeric_fields, self)
        if dialog.exec_() == QDialog.Accepted:
            self.selected_field = dialog.selected_field()
        else:
            return
            
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存专题图", "", "PNG图像 (*.png);;PDF文档 (*.pdf);;SVG图像 (*.svg)"
        )
        
        if not file_path:
            return
            
        try:
            # 创建专题图
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # 使用选择的字段进行可视化
            if self.selected_field and self.selected_field in self.output_gdf.columns:
                # 使用颜色映射
                try:
                    cmap = plt.colormaps['viridis']
                except:
                    cmap = cm.get_cmap('viridis')
                    
                norm = mcolors.Normalize(
                    vmin=self.output_gdf[self.selected_field].min(),
                    vmax=self.output_gdf[self.selected_field].max()
                )
                
                for idx, row in self.output_gdf.iterrows():
                    color = cmap(norm(row[self.selected_field]))
                    ax.fill(
                        *row.geometry.exterior.xy, 
                        facecolor=color, 
                        edgecolor='black', 
                        linewidth=0.5,
                        alpha=0.7
                    )
                
                # 添加颜色条
                sm = cm.ScalarMappable(norm=norm, cmap=cmap)
                sm.set_array([])
                cbar = fig.colorbar(sm, ax=ax)
                cbar.set_label(self.selected_field)
            else:
                # 如果没有选择字段，使用单一颜色
                for idx, row in self.output_gdf.iterrows():
                    ax.fill(
                        *row.geometry.exterior.xy, 
                        facecolor='lightblue', 
                        edgecolor='black', 
                        linewidth=0.5,
                        alpha=0.7
                    )
            
            # 获取边界并添加网格
            bounds = self.output_gdf.total_bounds
            self.add_grid(bounds, self.output_gdf.crs, ax)
            
            # 添加指北针和比例尺
            self.add_north_arrow(
                bounds[0] + (bounds[2] - bounds[0]) * 0.1,
                bounds[1] + (bounds[3] - bounds[1]) * 0.9,
                (bounds[2] - bounds[0]) * 0.05,
                ax
            )
            
            scale_length = (bounds[2] - bounds[0]) * 0.2
            self.add_scale_bar(
                bounds[0] + (bounds[2] - bounds[0]) * 0.1,
                bounds[1] + (bounds[3] - bounds[1]) * 0.1,
                scale_length,
                'm' if self.grid_units.currentText() == "米" else 
                'km' if self.grid_units.currentText() == "千米" else '度',
                ax
            )
            
            # 设置标题和标签
            ax.set_title("网格数据专题图")
            if self.output_gdf.crs and self.output_gdf.crs.is_geographic:
                ax.set_xlabel("经度")
                ax.set_ylabel("纬度")
            else:
                ax.set_xlabel("X坐标")
                ax.set_ylabel("Y坐标")
            
            # 保存图像
            fig.tight_layout()
            fig.savefig(file_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            
            self.log_message(f"专题图已保存: {file_path}")
            QMessageBox.information(self, "成功", "专题图生成成功")
            
            # 更新预览
            self.preview_grid_data()
            
        except Exception as e:
            self.log_message(f"生成专题图失败: {str(e)}", error=True)
            QMessageBox.critical(self, "错误", f"生成专题图失败:\n{str(e)}")
    
    def add_north_arrow(self, x, y, size, ax, color='black'):
        """添加指北针到指定坐标轴"""
        arrow = Arrow(x, y, 0, size, width=size*0.3, color=color)
        ax.add_patch(arrow)
        ax.text(x, y - size*0.5, 'N', ha='center', va='top', fontweight='bold')
    
    def add_scale_bar(self, x, y, length, units, ax, color='black'):
        """添加比例尺到指定坐标轴"""
        # 绘制比例尺主线
        ax.plot([x, x + length], [y, y], color=color, linewidth=3)
        
        # 绘制刻度
        for i in range(0, 6):
            pos = x + i * length / 5
            ax.plot([pos, pos], [y, y - length/20], color=color, linewidth=1)
        
        # 添加标签
        label = f"{length} {units}"
        ax.text(x + length/2, y - length/10, label, ha='center', va='top')
    
    def add_grid(self, bounds, crs, ax):
        """添加经纬度网格到指定坐标轴"""
        if crs and crs.is_geographic:
            # 如果是地理坐标系，添加经纬网格
            minx, miny, maxx, maxy = bounds
            
            # 计算合适的网格间隔
            x_interval = max(0.1, round((maxx - minx) / 5, 1))
            y_interval = max(0.1, round((maxy - miny) / 5, 1))
            
            # 生成网格线
            x_ticks = np.arange(np.floor(minx), np.ceil(maxx) + x_interval, x_interval)
            y_ticks = np.arange(np.floor(miny), np.ceil(maxy) + y_interval, y_interval)
            
            # 绘制网格线
            for x in x_ticks:
                ax.axvline(x=x, color='gray', linestyle='--', alpha=0.5)
            for y in y_ticks:
                ax.axhline(y=y, color='gray', linestyle='--', alpha=0.5)
            
            # 设置刻度
            ax.set_xticks(x_ticks)
            ax.set_yticks(y_ticks)
        
        ax.grid(True, alpha=0.3)
    
    def toggle_log(self):
        """切换日志窗口的显示/隐藏"""
        log_dock = self.findChild(QDockWidget, "处理日志")
        if log_dock:
            log_dock.setVisible(not log_dock.isVisible())
    
    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
        <h2>专业GIS数据网格划分工具</h2>
        <p>版本: 1.0.0</p>
        <p>版权所有 © 2023 GeoDataLab. 保留所有权利。</p>
        <p>此工具用于对GIS数据进行网格划分处理，支持SHP和TIFF格式数据。</p>
        <p>功能包括:</p>
        <ul>
            <li>支持SHP矢量数据和TIFF栅格数据</li>
            <li>自定义网格大小和单位（米、千米、度）</li>
            <li>多种统计方法（平均值、总和、最大值、最小值、计数、标准差、中位数）</li>
            <li>数据预览和网格预览</li>
            <li>多种输出格式（SHP、GeoJSON、KML）</li>
            <li>专题图生成功能</li>
        </ul>
        <p>技术支持: support@geodatalab.com</p>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def log_message(self, message, error=False):
        """添加消息到日志"""
        if error:
            formatted_msg = f'<font color="red">{message}</font>'
            self.statusBar().showMessage(f"错误: {message}")
        else:
            formatted_msg = f'<font color="blue">{message}</font>'
            self.statusBar().showMessage(message)
        
        self.log_text.append(formatted_msg)
        
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    QApplication.setApplicationName(APP_NAME)
    QApplication.setOrganizationName(ORG_NAME)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())