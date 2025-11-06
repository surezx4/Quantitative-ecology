import sys
import os
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QPushButton, QFileDialog, QComboBox, 
                             QSlider, QGroupBox, QSplitter, QMessageBox, QProgressBar,
                             QTabWidget, QCheckBox, QDoubleSpinBox, QSpinBox)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QPalette, QColor
import pyqtgraph.opengl as gl
import rasterio
import geopandas as gpd
from pykml import parser as kml_parser
from pyqtgraph import ColorMap
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

class TerrainViewer3D(gl.GLViewWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('3D地形查看器')
        self.setCameraPosition(distance=50, elevation=10, azimuth=0)
        
        # 添加坐标系
        self.axis = gl.GLAxisItem()
        self.axis.setSize(10, 10, 10)
        self.addItem(self.axis)
        
        # 地形网格
        self.terrain_mesh = None
        self.flight_path = None
        self.flight_position = None
        
    def load_terrain(self, dem_data, texture_data=None):
        """加载地形数据"""
        # 清理现有地形
        if self.terrain_mesh is not None:
            self.removeItem(self.terrain_mesh)
            
        # 创建地形网格
        rows, cols = dem_data.shape
        x = np.linspace(-cols/2, cols/2, cols)
        y = np.linspace(-rows/2, rows/2, rows)
        x, y = np.meshgrid(x, y)
        z = dem_data / np.max(dem_data) * 10  # 标准化高度
        
        # 创建颜色映射
        colors = self.create_terrain_colors(z)
        
        # 创建网格项
        self.terrain_mesh = gl.GLMeshItem(
            vertexes=np.dstack([x, y, z]),
            faces=None,
            vertexColors=colors,
            smooth=False,
            drawEdges=False
        )
        self.addItem(self.terrain_mesh)
        
        # 调整相机位置
        self.setCameraPosition(distance=max(rows, cols)*1.5)
        
    def create_terrain_colors(self, z):
        """创建地形颜色"""
        # 创建自定义颜色映射 (从绿色到棕色)
        colors = np.zeros((z.shape[0], z.shape[1], 4))
        
        # 根据高度设置颜色
        min_z, max_z = np.min(z), np.max(z)
        normalized_z = (z - min_z) / (max_z - min_z)
        
        # 低海拔: 绿色
        # 中海拔: 黄色/棕色
        # 高海拔: 灰色/白色
        for i in range(z.shape[0]):
            for j in range(z.shape[1]):
                height_ratio = normalized_z[i, j]
                if height_ratio < 0.3:
                    # 低海拔 - 绿色
                    colors[i, j] = [0.1, 0.6, 0.1, 1.0]
                elif height_ratio < 0.6:
                    # 中海拔 - 黄色/棕色
                    colors[i, j] = [0.7, 0.5, 0.2, 1.0]
                else:
                    # 高海拔 - 灰色/白色
                    colors[i, j] = [0.8, 0.8, 0.8, 1.0]
                    
        return colors.reshape(-1, 4)
    
    def load_flight_path(self, path_data):
        """加载飞行路径"""
        # 清理现有路径
        if self.flight_path is not None:
            self.removeItem(self.flight_path)
            
        # 创建路径点
        points = np.array(path_data)
        if len(points) == 0:
            return
            
        # 创建路径线
        self.flight_path = gl.GLLinePlotItem(
            pos=points, 
            color=(1, 0, 0, 1), 
            width=3, 
            antialias=True
        )
        self.addItem(self.flight_path)
        
        # 创建飞行位置指示器
        if self.flight_position is not None:
            self.removeItem(self.flight_position)
            
        self.flight_position = gl.GLScatterPlotItem(
            pos=[points[0]], 
            color=(1, 0, 0, 1), 
            size=10
        )
        self.addItem(self.flight_position)
        
    def update_flight_position(self, position):
        """更新飞行位置"""
        if self.flight_position is not None:
            self.flight_position.setData(pos=[position])
            
    def set_camera_to_flight(self, position, look_ahead):
        """设置相机到飞行位置"""
        # 设置相机位置和朝向
        self.setCameraPosition(
            pos=position,
            distance=0,  # 距离设为0，使用pos参数
            elevation=0,  # 仰角设为0，使用up参数
            azimuth=0    # 方位角设为0，使用lookAt参数
        )
        # 看向前方一点的位置
        self.pan(look_ahead[0]-position[0], look_ahead[1]-position[1], look_ahead[2]-position[2], relative=False)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D遥感图飞行演示软件 🛰️")
        self.setGeometry(100, 100, 1400, 900)
        
        # 应用样式
        self.apply_style()
        
        # 初始化数据
        self.dem_data = None
        self.texture_data = None
        self.flight_path_data = None
        self.current_flight_index = 0
        self.flight_timer = QTimer()
        self.flight_timer.timeout.connect(self.update_flight)
        self.is_manual_flight = False
        self.manual_flight_speed = 1.0
        
        # 创建UI
        self.create_ui()
        
        # 创建3D视图
        self.terrain_viewer = TerrainViewer3D()
        self.center_widget.layout().addWidget(self.terrain_viewer)
        
    def apply_style(self):
        """应用GIS专业风格"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #88ccff;
            }
            QPushButton {
                background-color: #4a4a4a;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QComboBox {
                background-color: #3a3a3a;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px;
                min-width: 120px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #555555;
                height: 5px;
                background: #3a3a3a;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #88ccff;
                border: 1px solid #555555;
                width: 12px;
                margin: -5px 0;
                border-radius: 6px;
            }
            QLabel {
                color: #ffffff;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 3px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #88ccff;
                width: 10px;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #3a3a3a;
            }
            QTabBar::tab {
                background-color: #4a4a4a;
                color: #ffffff;
                padding: 8px 20px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #88ccff;
                color: #000000;
            }
        """)
        
    def create_ui(self):
        """创建用户界面"""
        # 中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)
        
        # 中央显示区域
        self.center_widget = QWidget()
        self.center_widget.setLayout(QVBoxLayout())
        main_layout.addWidget(self.center_widget, 1)  # 设置伸缩因子为1
        
    def create_control_panel(self):
        """创建控制面板"""
        control_panel = QWidget()
        control_panel.setFixedWidth(300)
        layout = QVBoxLayout(control_panel)
        
        # 标题
        title = QLabel("🌍 3D遥感飞行演示")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 数据导入组
        data_group = QGroupBox("📁 数据导入")
        data_layout = QVBoxLayout(data_group)
        
        # DEM数据导入
        dem_btn = QPushButton("🗻 导入DEM数据")
        dem_btn.clicked.connect(self.load_dem_data)
        data_layout.addWidget(dem_btn)
        
        # 遥感图像导入
        image_btn = QPushButton("🛰️ 导入遥感图像")
        image_btn.clicked.connect(self.load_texture_data)
        data_layout.addWidget(image_btn)
        
        # 飞行路径导入
        path_btn = QPushButton("✈️ 导入飞行路径")
        path_btn.clicked.connect(self.load_flight_path)
        data_layout.addWidget(path_btn)
        
        layout.addWidget(data_group)
        
        # 飞行控制组
        flight_group = QGroupBox("🎮 飞行控制")
        flight_layout = QVBoxLayout(flight_group)
        
        # 飞行模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("飞行模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["自动飞行", "手动飞行"])
        self.mode_combo.currentTextChanged.connect(self.change_flight_mode)
        mode_layout.addWidget(self.mode_combo)
        flight_layout.addLayout(mode_layout)
        
        # 飞行速度控制
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("飞行速度:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 10)
        self.speed_slider.setValue(5)
        self.speed_slider.valueChanged.connect(self.update_flight_speed)
        speed_layout.addWidget(self.speed_slider)
        flight_layout.addLayout(speed_layout)
        
        # 飞行控制按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶️ 开始飞行")
        self.start_btn.clicked.connect(self.start_flight)
        btn_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.clicked.connect(self.pause_flight)
        btn_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self.stop_flight)
        btn_layout.addWidget(self.stop_btn)
        
        flight_layout.addLayout(btn_layout)
        
        # 手动飞行控制
        manual_group = QGroupBox("🎯 手动飞行控制")
        manual_layout = QVBoxLayout(manual_group)
        
        # 方向控制
        direction_layout = QHBoxLayout()
        up_btn = QPushButton("⬆️")
        up_btn.clicked.connect(lambda: self.manual_move(0, 1, 0))
        direction_layout.addWidget(up_btn)
        
        middle_layout = QVBoxLayout()
        left_btn = QPushButton("⬅️")
        left_btn.clicked.connect(lambda: self.manual_move(-1, 0, 0))
        right_btn = QPushButton("➡️")
        right_btn.clicked.connect(lambda: self.manual_move(1, 0, 0))
        middle_layout.addWidget(left_btn)
        middle_layout.addWidget(right_btn)
        direction_layout.addLayout(middle_layout)
        
        down_btn = QPushButton("⬇️")
        down_btn.clicked.connect(lambda: self.manual_move(0, -1, 0))
        direction_layout.addWidget(down_btn)
        
        manual_layout.addLayout(direction_layout)
        
        # 高度控制
        altitude_layout = QHBoxLayout()
        altitude_layout.addWidget(QLabel("高度:"))
        self.altitude_up_btn = QPushButton("↑")
        self.altitude_up_btn.clicked.connect(lambda: self.manual_move(0, 0, 1))
        altitude_layout.addWidget(self.altitude_up_btn)
        
        self.altitude_down_btn = QPushButton("↓")
        self.altitude_down_btn.clicked.connect(lambda: self.manual_move(0, 0, -1))
        altitude_layout.addWidget(self.altitude_down_btn)
        
        manual_layout.addLayout(altitude_layout)
        
        flight_layout.addWidget(manual_group)
        
        layout.addWidget(flight_group)
        
        # 视图控制组
        view_group = QGroupBox("👁️ 视图控制")
        view_layout = QVBoxLayout(view_group)
        
        # 视角选择
        view_layout.addWidget(QLabel("预设视角:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["俯视图", "前视图", "左视图", "右视图", "透视图"])
        self.view_combo.currentTextChanged.connect(self.change_view)
        view_layout.addWidget(self.view_combo)
        
        # 缩放控制
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("缩放:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 200)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(self.update_zoom)
        zoom_layout.addWidget(self.zoom_slider)
        view_layout.addLayout(zoom_layout)
        
        layout.addWidget(view_group)
        
        # 状态信息组
        status_group = QGroupBox("📊 状态信息")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("就绪")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        return control_panel
        
    def load_dem_data(self):
        """加载DEM数据 - 使用rasterio替代GDAL"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择DEM文件", "", "TIFF文件 (*.tif *.tiff)"
        )
        
        if file_path:
            try:
                # 使用rasterio读取DEM数据
                with rasterio.open(file_path) as dataset:
                    # 读取第一个波段
                    self.dem_data = dataset.read(1)
                    
                    # 处理NoData值
                    if dataset.nodata is not None:
                        self.dem_data[self.dem_data == dataset.nodata] = 0
                    
                # 更新3D地形
                self.terrain_viewer.load_terrain(self.dem_data)
                
                self.status_label.setText(f"DEM数据已加载: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载DEM数据时出错: {str(e)}")
                
    def load_texture_data(self):
        """加载遥感图像数据 - 使用rasterio替代GDAL"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择遥感图像文件", "", "TIFF文件 (*.tif *.tiff)"
        )
        
        if file_path:
            try:
                # 使用rasterio读取遥感图像
                with rasterio.open(file_path) as dataset:
                    # 读取所有波段
                    self.texture_data = dataset.read()
                    
                    # 如果是多波段图像，使用前三个波段作为RGB
                    if self.texture_data.shape[0] >= 3:
                        # 这里可以添加纹理映射逻辑
                        pass
                        
                self.status_label.setText(f"遥感图像已加载: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载遥感图像时出错: {str(e)}")
                
    def load_flight_path(self):
        """加载飞行路径 - 使用geopandas和pykml替代OGR"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择飞行路径文件", "", "SHP文件 (*.shp);;KML文件 (*.kml)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.shp'):
                    # 使用geopandas读取SHP文件
                    gdf = gpd.read_file(file_path)
                    
                    path_data = []
                    for geometry in gdf.geometry:
                        if geometry.geom_type == 'LineString':
                            # 提取线段的坐标点
                            coords = list(geometry.coords)
                            for point in coords:
                                # 转换为3D坐标 (添加高度)
                                path_data.append([point[0], point[1], 5])  # 固定高度为5
                        elif geometry.geom_type == 'Point':
                            # 如果是点，直接添加
                            path_data.append([geometry.x, geometry.y, 5])
                            
                    self.flight_path_data = np.array(path_data)
                    
                elif file_path.endswith('.kml'):
                    # 使用pykml解析KML文件
                    with open(file_path, 'r', encoding='utf-8') as f:
                        doc = kml_parser.parse(f).getroot()
                    
                    # 查找KML中的路径数据
                    path_data = []
                    for placemark in doc.Document.Folder.Placemark:
                        if hasattr(placemark, 'LineString'):
                            coords_str = placemark.LineString.coordinates.text
                            # 解析坐标字符串
                            coords = []
                            for coord_str in coords_str.strip().split():
                                parts = coord_str.split(',')
                                if len(parts) >= 2:
                                    x, y = float(parts[0]), float(parts[1])
                                    z = float(parts[2]) if len(parts) > 2 else 5
                                    coords.append([x, y, z])
                            path_data.extend(coords)
                    
                    if not path_data:
                        # 如果没有找到路径，创建示例路径
                        path_data = [
                            [-10, -10, 5], [-5, -5, 8], [0, 0, 10], [5, 5, 8], [10, 10, 5]
                        ]
                    
                    self.flight_path_data = np.array(path_data)
                
                # 更新飞行路径
                self.terrain_viewer.load_flight_path(self.flight_path_data)
                self.current_flight_index = 0
                
                self.status_label.setText(f"飞行路径已加载: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"加载飞行路径时出错: {str(e)}")
                # 创建示例路径作为备选
                self.flight_path_data = np.array([
                    [-10, -10, 5], [-5, -5, 8], [0, 0, 10], [5, 5, 8], [10, 10, 5]
                ])
                self.terrain_viewer.load_flight_path(self.flight_path_data)
                self.current_flight_index = 0
                self.status_label.setText("使用示例飞行路径")
                
    def change_flight_mode(self, mode):
        """改变飞行模式"""
        self.is_manual_flight = (mode == "手动飞行")
        self.status_label.setText(f"飞行模式: {mode}")
        
    def update_flight_speed(self, speed):
        """更新飞行速度"""
        self.manual_flight_speed = speed / 5.0  # 标准化速度
        
    def start_flight(self):
        """开始飞行"""
        if self.flight_path_data is None:
            QMessageBox.warning(self, "警告", "请先导入飞行路径")
            return
            
        if not self.is_manual_flight:
            # 自动飞行
            self.flight_timer.start(100)  # 每100毫秒更新一次
            self.status_label.setText("自动飞行中...")
        else:
            self.status_label.setText("手动飞行模式已激活")
            
    def pause_flight(self):
        """暂停飞行"""
        if self.flight_timer.isActive():
            self.flight_timer.stop()
            self.status_label.setText("飞行已暂停")
        else:
            self.flight_timer.start(100)
            self.status_label.setText("继续飞行...")
            
    def stop_flight(self):
        """停止飞行"""
        self.flight_timer.stop()
        self.current_flight_index = 0
        self.status_label.setText("飞行已停止")
        
    def update_flight(self):
        """更新飞行位置（自动模式）"""
        if self.flight_path_data is None or len(self.flight_path_data) == 0:
            return
            
        # 更新飞行位置
        self.current_flight_index = (self.current_flight_index + 1) % len(self.flight_path_data)
        position = self.flight_path_data[self.current_flight_index]
        
        # 计算前方点（用于相机朝向）
        look_ahead_index = (self.current_flight_index + 1) % len(self.flight_path_data)
        look_ahead = self.flight_path_data[look_ahead_index]
        
        # 更新3D视图
        self.terrain_viewer.update_flight_position(position)
        self.terrain_viewer.set_camera_to_flight(position, look_ahead)
        
        # 更新进度条
        progress = int((self.current_flight_index / len(self.flight_path_data)) * 100)
        self.progress_bar.setValue(progress)
        
    def manual_move(self, dx, dy, dz):
        """手动移动（手动模式）"""
        if not self.is_manual_flight:
            return
            
        # 获取当前相机位置
        camera_params = self.terrain_viewer.cameraParams()
        current_pos = np.array([camera_params['pos'].x(), 
                               camera_params['pos'].y(), 
                               camera_params['pos'].z()])
        
        # 计算新位置
        new_pos = current_pos + np.array([dx, dy, dz]) * self.manual_flight_speed
        
        # 更新相机位置
        self.terrain_viewer.setCameraPosition(pos=new_pos)
        
    def change_view(self, view_name):
        """改变视图"""
        if view_name == "俯视图":
            self.terrain_viewer.setCameraPosition(distance=50, elevation=90, azimuth=0)
        elif view_name == "前视图":
            self.terrain_viewer.setCameraPosition(distance=50, elevation=0, azimuth=0)
        elif view_name == "左视图":
            self.terrain_viewer.setCameraPosition(distance=50, elevation=0, azimuth=90)
        elif view_name == "右视图":
            self.terrain_viewer.setCameraPosition(distance=50, elevation=0, azimuth=-90)
        elif view_name == "透视图":
            self.terrain_viewer.setCameraPosition(distance=50, elevation=30, azimuth=45)
            
    def update_zoom(self, value):
        """更新缩放"""
        # 获取当前相机参数
        camera_params = self.terrain_viewer.cameraParams()
        
        # 更新距离（实现缩放效果）
        distance = value
        self.terrain_viewer.setCameraPosition(
            distance=distance,
            elevation=camera_params['elevation'],
            azimuth=camera_params['azimuth']
        )


def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()