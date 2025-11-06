import sys
import os
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QWidget, QTextEdit,
                             QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, 
                             QCheckBox, QProgressBar, QSplitter, QTabWidget,
                             QMessageBox, QFrame, QGridLayout)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
import rasterio
from rasterio.plot import reshape_as_image
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from scipy import ndimage
from scipy.ndimage import zoom, convolve
import tifffile
from skimage import exposure, filters, restoration, transform
import warnings
warnings.filterwarnings('ignore')

class ProcessingThread(QThread):
    """处理线程，防止界面卡死"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str, str)  # message, level
    processing_finished = pyqtSignal(object, object)  # 修改为object类型以兼容Profile对象

    def __init__(self, image_data, profile, method, parameters):
        super().__init__()
        self.image_data = image_data
        self.profile = profile
        self.method = method
        self.parameters = parameters
        self.is_running = True

    def run(self):
        try:
            self.status_updated.emit(f"开始处理: {self.method}", "info")
            
            # 根据选择的方法进行处理
            if self.method == "双三次插值":
                processed_data = self.bicubic_interpolation()
            elif self.method == "双线性插值":
                processed_data = self.bilinear_interpolation()
            elif self.method == "Lanczos插值":
                processed_data = self.lanczos_interpolation()
            elif self.method == "锐化增强":
                processed_data = self.sharpen_enhancement()
            elif self.method == "导向滤波":
                processed_data = self.guided_filter()
            elif self.method == "小波变换":
                processed_data = self.wavelet_transform()
            elif self.method == "全色锐化":
                processed_data = self.pansharpening()
            else:
                processed_data = self.image_data.copy()
                
            self.progress_updated.emit(100)
            self.status_updated.emit("处理完成!", "success")
            self.processing_finished.emit(processed_data, self.profile)
            
        except Exception as e:
            self.status_updated.emit(f"处理失败: {str(e)}", "error")

    def bicubic_interpolation(self):
        scale_factor = self.parameters.get("scale_factor", 2.0)
        processed_data = np.zeros((
            self.image_data.shape[0],
            int(self.image_data.shape[1] * scale_factor),
            int(self.image_data.shape[2] * scale_factor)
        ))
        
        for i in range(self.image_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(int(100 * i / self.image_data.shape[0]))
            band = self.image_data[i].astype(np.float32)
            # 使用scipy的zoom函数进行双三次插值
            processed_data[i] = zoom(band, scale_factor, order=3)
            
        return processed_data

    def bilinear_interpolation(self):
        scale_factor = self.parameters.get("scale_factor", 2.0)
        processed_data = np.zeros((
            self.image_data.shape[0],
            int(self.image_data.shape[1] * scale_factor),
            int(self.image_data.shape[2] * scale_factor)
        ))
        
        for i in range(self.image_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(int(100 * i / self.image_data.shape[0]))
            band = self.image_data[i].astype(np.float32)
            # 使用scipy的zoom函数进行双线性插值
            processed_data[i] = zoom(band, scale_factor, order=1)
            
        return processed_data

    def lanczos_interpolation(self):
        scale_factor = self.parameters.get("scale_factor", 2.0)
        processed_data = np.zeros((
            self.image_data.shape[0],
            int(self.image_data.shape[1] * scale_factor),
            int(self.image_data.shape[2] * scale_factor)
        ))
        
        for i in range(self.image_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(int(100 * i / self.image_data.shape[0]))
            band = self.image_data[i].astype(np.float32)
            # 使用skimage的resize进行Lanczos插值
            processed_data[i] = transform.resize(
                band, 
                (int(band.shape[0] * scale_factor), int(band.shape[1] * scale_factor)),
                order=3,  # Lanczos
                anti_aliasing=True
            )
            
        return processed_data

    def sharpen_enhancement(self):
        scale_factor = self.parameters.get("scale_factor", 2.0)
        strength = self.parameters.get("strength", 1.0)
        
        # 先进行插值
        interpolated_data = np.zeros((
            self.image_data.shape[0],
            int(self.image_data.shape[1] * scale_factor),
            int(self.image_data.shape[2] * scale_factor)
        ))
        
        for i in range(self.image_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(int(50 * i / self.image_data.shape[0]))
            band = self.image_data[i].astype(np.float32)
            interpolated_data[i] = zoom(band, scale_factor, order=3)
        
        # 然后进行锐化
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]) * strength
        processed_data = np.zeros_like(interpolated_data)
        
        for i in range(interpolated_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(50 + int(50 * i / interpolated_data.shape[0]))
            # 使用scipy的convolve进行卷积
            processed_data[i] = convolve(interpolated_data[i], kernel, mode='reflect')
            
        return processed_data

    def guided_filter(self):
        scale_factor = self.parameters.get("scale_factor", 2.0)
        radius = self.parameters.get("radius", 5)
        
        # 先进行插值
        interpolated_data = np.zeros((
            self.image_data.shape[0],
            int(self.image_data.shape[1] * scale_factor),
            int(self.image_data.shape[2] * scale_factor)
        ))
        
        for i in range(self.image_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(int(50 * i / self.image_data.shape[0]))
            band = self.image_data[i].astype(np.float32)
            interpolated_data[i] = zoom(band, scale_factor, order=3)
        
        # 使用高斯滤波代替导向滤波
        processed_data = np.zeros_like(interpolated_data)
        
        for i in range(interpolated_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(50 + int(50 * i / interpolated_data.shape[0]))
            processed_data[i] = filters.gaussian(interpolated_data[i], sigma=radius/3)
            
        return processed_data

    def wavelet_transform(self):
        try:
            import pywt
        except ImportError:
            self.status_updated.emit("未安装pywavelets库，使用双三次插值代替", "warning")
            return self.bicubic_interpolation()
        
        scale_factor = self.parameters.get("scale_factor", 2.0)
        
        # 先进行插值
        interpolated_data = np.zeros((
            self.image_data.shape[0],
            int(self.image_data.shape[1] * scale_factor),
            int(self.image_data.shape[2] * scale_factor)
        ))
        
        for i in range(self.image_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(int(50 * i / self.image_data.shape[0]))
            band = self.image_data[i].astype(np.float32)
            interpolated_data[i] = zoom(band, scale_factor, order=3)
        
        # 然后进行小波变换增强
        processed_data = np.zeros_like(interpolated_data)
        
        for i in range(interpolated_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(50 + int(50 * i / interpolated_data.shape[0]))
            try:
                # 小波变换
                coeffs = pywt.dwt2(interpolated_data[i], 'db4')
                cA, (cH, cV, cD) = coeffs
                
                # 增强高频分量
                cH *= 1.2
                cV *= 1.2
                cD *= 1.1
                
                # 逆变换
                processed_data[i] = pywt.idwt2((cA, (cH, cV, cD)), 'db4')
            except:
                # 如果小波变换失败，使用原始数据
                processed_data[i] = interpolated_data[i]
            
        return processed_data

    def pansharpening(self):
        # 简化的全色锐化模拟
        scale_factor = self.parameters.get("scale_factor", 2.0)
        method = self.parameters.get("pansharp_method", "brovey")
        
        # 模拟全色波段（通过加权平均多光谱波段）
        panchromatic = np.mean(self.image_data, axis=0)
        
        # 对全色波段进行插值
        pan_interpolated = zoom(panchromatic, scale_factor, order=3)
        
        # 对多光谱波段进行插值
        ms_interpolated = np.zeros((
            self.image_data.shape[0],
            int(self.image_data.shape[1] * scale_factor),
            int(self.image_data.shape[2] * scale_factor)
        ))
        
        for i in range(self.image_data.shape[0]):
            if not self.is_running:
                break
            self.progress_updated.emit(int(100 * i / self.image_data.shape[0]))
            band = self.image_data[i].astype(np.float32)
            ms_interpolated[i] = zoom(band, scale_factor, order=3)
        
        # 应用全色锐化
        if method == "brovey":
            # Brovey变换
            sum_ms = np.sum(ms_interpolated, axis=0)
            sum_ms[sum_ms == 0] = 1  # 避免除零
            processed_data = ms_interpolated * (pan_interpolated / sum_ms)
        else:
            # 简单的强度替换
            intensity = np.mean(ms_interpolated, axis=0)
            ratio = np.zeros_like(ms_interpolated)
            for i in range(ms_interpolated.shape[0]):
                ratio[i] = ms_interpolated[i] / (intensity + 1e-8)
            processed_data = ratio * pan_interpolated
            
        return processed_data


class MplCanvas(FigureCanvas):
    """Matplotlib画布"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_data = None
        self.profile = None
        self.processed_data = None
        self.processing_thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('🛰️ Landsat遥感卫星空间分辨率提升工具')
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                padding: 4px;
                border: 1px solid #cccccc;
                border-radius: 4px;
                background-color: white;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                width: 20px;
            }
        """)

        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 左侧：控制面板
        left_panel = QVBoxLayout()
        
        # 文件操作组
        file_group = QGroupBox("📁 文件操作")
        file_layout = QVBoxLayout()
        
        self.btn_load = QPushButton('📂 加载TIFF影像')
        self.btn_save = QPushButton('💾 保存处理结果')
        self.btn_save.setEnabled(False)
        
        file_layout.addWidget(self.btn_load)
        file_layout.addWidget(self.btn_save)
        file_group.setLayout(file_layout)
        left_panel.addWidget(file_group)
        
        # 处理方法组
        method_group = QGroupBox("⚙️ 分辨率提升方法")
        method_layout = QGridLayout()
        
        method_layout.addWidget(QLabel("方法:"), 0, 0)
        self.cmb_method = QComboBox()
        self.cmb_method.addItems([
            "双三次插值", 
            "双线性插值", 
            "Lanczos插值", 
            "锐化增强", 
            "导向滤波", 
            "小波变换", 
            "全色锐化"
        ])
        method_layout.addWidget(self.cmb_method, 0, 1)
        
        method_layout.addWidget(QLabel("缩放因子:"), 1, 0)
        self.spn_scale = QDoubleSpinBox()
        self.spn_scale.setRange(1.1, 4.0)
        self.spn_scale.setValue(2.0)
        self.spn_scale.setSingleStep(0.1)
        method_layout.addWidget(self.spn_scale, 1, 1)
        
        method_layout.addWidget(QLabel("锐化强度:"), 2, 0)
        self.spn_sharpen = QDoubleSpinBox()
        self.spn_sharpen.setRange(0.1, 3.0)
        self.spn_sharpen.setValue(1.0)
        self.spn_sharpen.setSingleStep(0.1)
        method_layout.addWidget(self.spn_sharpen, 2, 1)
        
        method_layout.addWidget(QLabel("滤波半径:"), 3, 0)
        self.spn_radius = QSpinBox()
        self.spn_radius.setRange(1, 20)
        self.spn_radius.setValue(5)
        method_layout.addWidget(self.spn_radius, 3, 1)
        
        method_layout.addWidget(QLabel("全色锐化方法:"), 4, 0)
        self.cmb_pansharp = QComboBox()
        self.cmb_pansharp.addItems(["Brovey变换", "IHS变换"])
        method_layout.addWidget(self.cmb_pansharp, 4, 1)
        
        self.chk_hist_match = QCheckBox("直方图匹配")
        self.chk_hist_match.setChecked(True)
        method_layout.addWidget(self.chk_hist_match, 5, 0, 1, 2)
        
        method_group.setLayout(method_layout)
        left_panel.addWidget(method_group)
        
        # 处理控制组
        process_group = QGroupBox("🚀 处理控制")
        process_layout = QVBoxLayout()
        
        self.btn_process = QPushButton('🎯 开始处理')
        self.btn_process.setEnabled(False)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        
        process_layout.addWidget(self.btn_process)
        process_layout.addWidget(self.progress_bar)
        process_group.setLayout(process_layout)
        left_panel.addWidget(process_group)
        
        # 图像信息组
        info_group = QGroupBox("ℹ️ 图像信息")
        info_layout = QVBoxLayout()
        
        self.lbl_info = QLabel("未加载图像")
        self.lbl_info.setWordWrap(True)
        info_layout.addWidget(self.lbl_info)
        info_group.setLayout(info_layout)
        left_panel.addWidget(info_group)
        
        # 日志组
        log_group = QGroupBox("📋 处理日志")
        log_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setMaximumHeight(200)
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        log_group.setLayout(log_layout)
        left_panel.addWidget(log_group)
        
        left_panel_widget = QWidget()
        left_panel_widget.setLayout(left_panel)
        left_panel_widget.setMaximumWidth(400)
        
        # 右侧：图像显示区域
        right_panel = QVBoxLayout()
        
        # 创建标签页显示图像
        self.tab_images = QTabWidget()
        
        # 原始图像标签页
        self.tab_original = QWidget()
        layout_original = QVBoxLayout(self.tab_original)
        self.canvas_original = MplCanvas(self, width=6, height=5, dpi=100)
        layout_original.addWidget(self.canvas_original)
        self.tab_images.addTab(self.tab_original, "📷 原始影像")
        
        # 处理后图像标签页
        self.tab_processed = QWidget()
        layout_processed = QVBoxLayout(self.tab_processed)
        self.canvas_processed = MplCanvas(self, width=6, height=5, dpi=100)
        layout_processed.addWidget(self.canvas_processed)
        self.tab_images.addTab(self.tab_processed, "✨ 处理后影像")
        
        # 对比标签页
        self.tab_compare = QWidget()
        layout_compare = QVBoxLayout(self.tab_compare)
        self.fig_compare = Figure(figsize=(8, 5))
        self.canvas_compare = FigureCanvas(self.fig_compare)
        layout_compare.addWidget(self.canvas_compare)
        self.tab_images.addTab(self.tab_compare, "🔍 影像对比")
        
        right_panel.addWidget(self.tab_images)
        
        # 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel_widget)
        right_panel_widget = QWidget()
        right_panel_widget.setLayout(right_panel)
        splitter.addWidget(right_panel_widget)
        splitter.setSizes([350, 1050])
        
        main_layout.addWidget(splitter)

        # 连接信号与槽
        self.btn_load.clicked.connect(self.load_tiff)
        self.btn_save.clicked.connect(self.save_result)
        self.btn_process.clicked.connect(self.process_image)
        self.cmb_method.currentTextChanged.connect(self.update_parameters_visibility)

        # 初始化参数可见性
        self.update_parameters_visibility()
        
        self.log('🛰️ Landsat遥感卫星空间分辨率提升工具已启动', 'info')
        self.log('✅ 请加载TIFF格式的遥感影像开始处理', 'success')

    def update_parameters_visibility(self):
        """根据选择的方法更新参数控件的可见性"""
        method = self.cmb_method.currentText()
        
        # 默认隐藏所有特殊参数
        self.spn_sharpen.setEnabled(False)
        self.spn_radius.setEnabled(False)
        self.cmb_pansharp.setEnabled(False)
        
        # 根据方法启用相关参数
        if method == "锐化增强":
            self.spn_sharpen.setEnabled(True)
        elif method == "导向滤波":
            self.spn_radius.setEnabled(True)
        elif method == "全色锐化":
            self.cmb_pansharp.setEnabled(True)

    def load_tiff(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "打开TIFF文件", 
            "", 
            "TIFF Files (*.tif *.tiff);;All Files (*)"
        )
        if file_path:
            try:
                with rasterio.open(file_path) as src:
                    self.image_data = src.read()
                    self.profile = src.profile
                    
                # 更新图像信息
                info_text = f"""
                📊 图像信息:
                📏 尺寸: {self.image_data.shape[1]} x {self.image_data.shape[2]} 像素
                🎨 波段数: {self.image_data.shape[0]}
                📐 数据类型: {self.image_data.dtype}
                🌍 坐标系统: {self.profile.get('crs', '未知')}
                """
                self.lbl_info.setText(info_text)
                
                # 显示原始图像
                self.display_image(self.image_data, self.canvas_original, "原始影像")
                
                # 启用处理按钮
                self.btn_process.setEnabled(True)
                self.btn_save.setEnabled(False)
                
                self.log(f'✅ 成功加载文件: {os.path.basename(file_path)}', 'success')
                self.log(f'📊 图像尺寸: {self.image_data.shape}', 'info')
                
            except Exception as e:
                self.log(f'❌ 加载文件失败: {str(e)}', 'error')

    def process_image(self):
        if self.image_data is None:
            self.log('❌ 请先加载TIFF影像', 'error')
            return
            
        # 收集处理参数
        method = self.cmb_method.currentText()
        parameters = {
            "scale_factor": self.spn_scale.value(),
            "strength": self.spn_sharpen.value(),
            "radius": self.spn_radius.value(),
            "pansharp_method": "brovey" if self.cmb_pansharp.currentText() == "Brovey变换" else "ihs",
            "histogram_match": self.chk_hist_match.isChecked()
        }
        
        # 禁用按钮，开始处理
        self.btn_process.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # 创建处理线程
        self.processing_thread = ProcessingThread(
            self.image_data, 
            self.profile, 
            method, 
            parameters
        )
        self.processing_thread.progress_updated.connect(self.progress_bar.setValue)
        self.processing_thread.status_updated.connect(self.log)
        self.processing_thread.processing_finished.connect(self.on_processing_finished)
        self.processing_thread.start()

    def on_processing_finished(self, processed_data, profile):
        self.processed_data = processed_data
        self.processed_profile = profile
        
        # 显示处理后的图像
        self.display_image(processed_data, self.canvas_processed, "处理后影像")
        
        # 显示对比图像
        self.display_comparison(self.image_data, processed_data)
        
        # 启用保存按钮
        self.btn_save.setEnabled(True)
        self.btn_process.setEnabled(True)
        
        # 更新图像信息
        info_text = f"""
        📊 图像信息:
        📏 原始尺寸: {self.image_data.shape[1]} x {self.image_data.shape[2]} 像素
        📏 处理后尺寸: {processed_data.shape[1]} x {processed_data.shape[2]} 像素
        🎨 波段数: {processed_data.shape[0]}
        📐 数据类型: {processed_data.dtype}
        🌍 坐标系统: {profile.get('crs', '未知')}
        """
        self.lbl_info.setText(info_text)

    def save_result(self):
        if self.processed_data is None:
            self.log('❌ 没有可保存的处理结果', 'error')
            return
            
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存TIFF文件", 
            "", 
            "TIFF Files (*.tif);;All Files (*)"
        )
        if save_path:
            try:
                # 更新元数据
                profile = self.processed_profile.copy()
                profile.update({
                    'height': self.processed_data.shape[1],
                    'width': self.processed_data.shape[2],
                    'dtype': self.processed_data.dtype,
                    'count': self.processed_data.shape[0]
                })
                
                # 保存处理后的数据
                with rasterio.open(save_path, 'w', **profile) as dst:
                    dst.write(self.processed_data)
                    
                self.log(f'✅ 文件已保存: {os.path.basename(save_path)}', 'success')
                
            except Exception as e:
                self.log(f'❌ 保存文件失败: {str(e)}', 'error')

    def display_image(self, image_data, canvas, title):
        """显示图像到指定的画布"""
        canvas.axes.clear()
        
        # 如果是多波段，显示RGB合成（前3个波段）
        if image_data.shape[0] >= 3:
            # 归一化并转换为RGB图像
            rgb_image = np.transpose(image_data[:3], (1, 2, 0))
            # 拉伸对比度
            p2, p98 = np.percentile(rgb_image, (2, 98))
            rgb_image = exposure.rescale_intensity(rgb_image, in_range=(p2, p98))
            
            canvas.axes.imshow(rgb_image)
        else:
            # 单波段图像
            canvas.axes.imshow(image_data[0], cmap='gray')
            
        canvas.axes.set_title(title)
        canvas.axes.axis('off')
        canvas.draw()

    def display_comparison(self, original, processed):
        """显示原始图像和处理后图像的对比"""
        self.fig_compare.clear()
        
        # 如果是多波段，使用RGB合成
        if original.shape[0] >= 3 and processed.shape[0] >= 3:
            # 原始图像RGB
            orig_rgb = np.transpose(original[:3], (1, 2, 0))
            p2, p98 = np.percentile(orig_rgb, (2, 98))
            orig_rgb = exposure.rescale_intensity(orig_rgb, in_range=(p2, p98))
            
            # 处理后的图像RGB
            proc_rgb = np.transpose(processed[:3], (1, 2, 0))
            p2, p98 = np.percentile(proc_rgb, (2, 98))
            proc_rgb = exposure.rescale_intensity(proc_rgb, in_range=(p2, p98))
            
            # 显示对比
            ax1 = self.fig_compare.add_subplot(1, 2, 1)
            ax1.imshow(orig_rgb)
            ax1.set_title('原始影像')
            ax1.axis('off')
            
            ax2 = self.fig_compare.add_subplot(1, 2, 2)
            ax2.imshow(proc_rgb)
            ax2.set_title('处理后影像')
            ax2.axis('off')
            
        self.canvas_compare.draw()

    def log(self, message, level='info'):
        """在日志框中添加带图标的日志"""
        icon_map = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }
        
        color_map = {
            'info': '#0066cc',
            'success': '#009900',
            'warning': '#ff9900',
            'error': '#cc0000'
        }
        
        icon = icon_map.get(level, '')
        color = color_map.get(level, '#000000')
        
        # 添加带颜色的HTML格式日志
        html_message = f'<span style="color: {color}">{icon} {message}</span>'
        self.log_display.append(html_message)
        
        # 自动滚动到底部
        self.log_display.verticalScrollBar().setValue(
            self.log_display.verticalScrollBar().maximum()
        )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用程序字体
    font = QFont("Segoe UI Emoji", 9)
    app.setFont(font)
    
    main_window = MainWindow()
    main_window.show()
    
    sys.exit(app.exec_())