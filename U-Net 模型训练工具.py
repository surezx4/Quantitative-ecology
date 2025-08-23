import sys
import datetime
import os
import numpy as np
import cv2
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, concatenate, Conv2DTranspose, BatchNormalization, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import plot_model
from tensorflow.keras import backend as K
from tensorflow.keras.callbacks import ModelCheckpoint, TensorBoard
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split

# 假设这些自定义函数在 losses.py 中定义
def weighted_binary_crossentropy(y_true, y_pred):
    # 实现您的自定义损失函数
    return K.binary_crossentropy(y_true, y_pred)

def accuracy(y_true, y_pred):
    # 实现准确率计算
    return K.mean(K.equal(y_true, K.round(y_pred)))

def precision(y_true, y_pred):
    # 实现精确率计算
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    return true_positives / (predicted_positives + K.epsilon())

def recall(y_true, y_pred):
    # 实现召回率计算
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    return true_positives / (possible_positives + K.epsilon())

# 导入 PyQt5 相关库
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QGroupBox, QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog,
                             QSpinBox, QCheckBox, QComboBox, QProgressBar, QMessageBox, QTabWidget,
                             QListWidget, QSplitter, QSizePolicy, QScrollArea)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 训练线程类
class TrainThread(QThread):
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()
    
    def __init__(self, model, callbacks, X_train, Y_train, X_val, Y_val, epochs, batch_size):
        super().__init__()
        self.model = model
        self.callbacks = callbacks
        self.X_train = X_train
        self.Y_train = Y_train
        self.X_val = X_val
        self.Y_val = Y_val
        self.epochs = epochs
        self.batch_size = batch_size
        
    def run(self):
        try:
            self.update_signal.emit("开始训练模型...")
            
            # 自定义回调函数用于更新进度
            class ProgressCallback(Callback):
                def __init__(self, outer):
                    self.outer = outer
                    self.epoch = 0
                
                def on_epoch_begin(self, epoch, logs=None):
                    self.epoch = epoch
                    self.outer.update_signal.emit(f"开始第 {epoch+1}/{self.outer.epochs} 轮训练")
                
                def on_epoch_end(self, epoch, logs=None):
                    progress = int((epoch + 1) / self.outer.epochs * 100)
                    self.outer.progress_signal.emit(progress)
                    self.outer.update_signal.emit(
                        f"第 {epoch+1}/{self.outer.epochs} 轮完成 - "
                        f"损失: {logs['loss']:.4f}, 准确率: {logs['accuracy']:.4f}, "
                        f"验证损失: {logs['val_loss']:.4f}, 验证准确率: {logs['val_accuracy']:.4f}"
                    )
            
            # 添加进度回调
            self.callbacks.append(ProgressCallback(self))
            
            history = self.model.fit(
                self.X_train, self.Y_train,
                batch_size=self.batch_size,
                epochs=self.epochs,
                validation_data=(self.X_val, self.Y_val),
                callbacks=self.callbacks,
                verbose=0  # 设置为0，因为我们使用自定义回调
            )
            
            self.update_signal.emit(f"训练完成！最终损失: {history.history['loss'][-1]:.4f}")
            self.finished_signal.emit()
            
        except Exception as e:
            self.update_signal.emit(f"训练过程中出错: {str(e)}")
            self.finished_signal.emit()

# 数据加载线程类
class DataLoadThread(QThread):
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object, object, object, object)
    
    def __init__(self, image_dir, mask_dir, im_sz, n_classes, val_split=0.2):
        super().__init__()
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.im_sz = im_sz
        self.n_classes = n_classes
        self.val_split = val_split
        
    def run(self):
        try:
            self.update_signal.emit("开始加载数据...")
            
            # 获取图像和掩码文件列表
            image_files = [f for f in os.listdir(self.image_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
            mask_files = [f for f in os.listdir(self.mask_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
            
            if not image_files or not mask_files:
                self.update_signal.emit("未找到图像或掩码文件！")
                self.finished_signal.emit(None, None, None, None)
                return
                
            # 确保图像和掩码文件匹配
            common_files = set(image_files) & set(mask_files)
            if not common_files:
                self.update_signal.emit("图像和掩码文件不匹配！")
                self.finished_signal.emit(None, None, None, None)
                return
                
            image_files = sorted(list(common_files))
            total_files = len(image_files)
            
            # 加载图像和掩码
            images = []
            masks = []
            
            for i, filename in enumerate(image_files):
                # 加载图像
                img_path = os.path.join(self.image_dir, filename)
                img = cv2.imread(img_path, cv2.IMREAD_COLOR)
                if img is None:
                    self.update_signal.emit(f"无法加载图像: {filename}")
                    continue
                    
                # 调整图像大小
                img = cv2.resize(img, (self.im_sz, self.im_sz))
                img = img / 255.0  # 归一化
                images.append(img)
                
                # 加载掩码
                mask_path = os.path.join(self.mask_dir, filename)
                mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                if mask is None:
                    self.update_signal.emit(f"无法加载掩码: {filename}")
                    continue
                    
                # 调整掩码大小
                mask = cv2.resize(mask, (self.im_sz, self.im_sz))
                
                # 将掩码转换为one-hot编码
                mask_one_hot = np.zeros((self.im_sz, self.im_sz, self.n_classes))
                for c in range(self.n_classes):
                    mask_one_hot[:, :, c] = (mask == c).astype(np.float32)
                    
                masks.append(mask_one_hot)
                
                # 更新进度
                progress = int((i + 1) / total_files * 100)
                self.progress_signal.emit(progress)
                self.update_signal.emit(f"已加载 {i+1}/{total_files} 个文件")
            
            if not images or not masks:
                self.update_signal.emit("未能加载任何有效数据！")
                self.finished_signal.emit(None, None, None, None)
                return
                
            # 转换为numpy数组
            images = np.array(images)
            masks = np.array(masks)
            
            # 划分训练集和验证集
            X_train, X_val, Y_train, Y_val = train_test_split(
                images, masks, test_size=self.val_split, random_state=42
            )
            
            self.update_signal.emit(f"数据加载完成！训练集: {X_train.shape[0]} 样本, 验证集: {X_val.shape[0]} 样本")
            self.finished_signal.emit(X_train, X_val, Y_train, Y_val)
            
        except Exception as e:
            self.update_signal.emit(f"加载数据时出错: {str(e)}")
            self.finished_signal.emit(None, None, None, None)

# 模型可视化画布
class ModelCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)
        
    def plot_model_structure(self, model):
        self.ax.clear()
        try:
            plot_model(model, to_file='model_plot.png', show_shapes=True, show_layer_names=True)
            img = plt.imread('model_plot.png')
            self.ax.imshow(img)
            self.ax.axis('off')
            self.draw()
        except Exception as e:
            self.ax.text(0.5, 0.5, f"无法显示模型结构: {str(e)}", 
                        ha='center', va='center', transform=self.ax.transAxes)
            self.draw()

# 图像显示标签
class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setText("暂无图像")
        self.setStyleSheet("border: 1px solid gray;")
        
    def set_image(self, image_path):
        if image_path and os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 缩放图像以适应标签大小
                pixmap = pixmap.scaled(self.width(), self.height(), 
                                      Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setPixmap(pixmap)
                return
        self.setText("无法加载图像")

# 主窗口类
class UNetGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = None
        self.X_train, self.X_val, self.Y_train, self.Y_val = None, None, None, None
        self.image_dir = ""
        self.mask_dir = ""
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('U-Net 图像分割工具')
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件和主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧参数面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(300)
        
        # 数据导入组
        data_group = QGroupBox("数据导入")
        data_layout = QVBoxLayout()
        
        # 图像目录选择
        data_layout.addWidget(QLabel("图像目录:"))
        self.image_dir_btn = QPushButton("选择图像目录")
        self.image_dir_btn.clicked.connect(self.select_image_dir)
        data_layout.addWidget(self.image_dir_btn)
        self.image_dir_label = QLabel("未选择")
        data_layout.addWidget(self.image_dir_label)
        
        # 掩码目录选择
        data_layout.addWidget(QLabel("掩码目录:"))
        self.mask_dir_btn = QPushButton("选择掩码目录")
        self.mask_dir_btn.clicked.connect(self.select_mask_dir)
        data_layout.addWidget(self.mask_dir_btn)
        self.mask_dir_label = QLabel("未选择")
        data_layout.addWidget(self.mask_dir_label)
        
        # 验证集比例
        data_layout.addWidget(QLabel("验证集比例:"))
        self.val_split = QLineEdit("0.2")
        data_layout.addWidget(self.val_split)
        
        # 加载数据按钮
        self.load_data_btn = QPushButton("加载数据")
        self.load_data_btn.clicked.connect(self.load_data)
        self.load_data_btn.setEnabled(False)
        data_layout.addWidget(self.load_data_btn)
        
        # 数据预览按钮
        self.preview_btn = QPushButton("预览数据")
        self.preview_btn.clicked.connect(self.preview_data)
        self.preview_btn.setEnabled(False)
        data_layout.addWidget(self.preview_btn)
        
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)
        
        # 模型参数组
        params_group = QGroupBox("模型参数")
        params_layout = QVBoxLayout()
        
        # 类别数
        params_layout.addWidget(QLabel("类别数:"))
        self.n_classes = QSpinBox()
        self.n_classes.setRange(1, 100)
        self.n_classes.setValue(5)
        params_layout.addWidget(self.n_classes)
        
        # 图像尺寸
        params_layout.addWidget(QLabel("图像尺寸:"))
        self.im_sz = QSpinBox()
        self.im_sz.setRange(32, 512)
        self.im_sz.setValue(160)
        params_layout.addWidget(self.im_sz)
        
        # 通道数
        params_layout.addWidget(QLabel("通道数:"))
        self.n_channels = QSpinBox()
        self.n_channels.setRange(1, 100)
        self.n_channels.setValue(3)
        params_layout.addWidget(self.n_channels)
        
        # 初始过滤器数
        params_layout.addWidget(QLabel("初始过滤器数:"))
        self.n_filters_start = QSpinBox()
        self.n_filters_start.setRange(8, 256)
        self.n_filters_start.setValue(32)
        params_layout.addWidget(self.n_filters_start)
        
        # 增长因子
        params_layout.addWidget(QLabel("增长因子:"))
        self.growth_factor = QSpinBox()
        self.growth_factor.setRange(1, 4)
        self.growth_factor.setValue(2)
        params_layout.addWidget(self.growth_factor)
        
        # 使用转置卷积
        self.upconv = QCheckBox("使用转置卷积")
        self.upconv.setChecked(True)
        params_layout.addWidget(self.upconv)
        
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)
        
        # 训练参数组
        train_group = QGroupBox("训练参数")
        train_layout = QVBoxLayout()
        
        # 训练 epochs
        train_layout.addWidget(QLabel("训练轮次:"))
        self.epochs = QSpinBox()
        self.epochs.setRange(1, 1000)
        self.epochs.setValue(10)
        train_layout.addWidget(self.epochs)
        
        # 批大小
        train_layout.addWidget(QLabel("批大小:"))
        self.batch_size = QSpinBox()
        self.batch_size.setRange(1, 256)
        self.batch_size.setValue(32)
        train_layout.addWidget(self.batch_size)
        
        # 学习率
        train_layout.addWidget(QLabel("学习率:"))
        self.learning_rate = QLineEdit("0.001")
        train_layout.addWidget(self.learning_rate)
        
        train_group.setLayout(train_layout)
        left_layout.addWidget(train_group)
        
        # 按钮组
        button_group = QGroupBox("操作")
        button_layout = QVBoxLayout()
        
        # 创建模型按钮
        self.create_btn = QPushButton("创建模型")
        self.create_btn.clicked.connect(self.create_model)
        button_layout.addWidget(self.create_btn)
        
        # 训练模型按钮
        self.train_btn = QPushButton("训练模型")
        self.train_btn.clicked.connect(self.train_model)
        self.train_btn.setEnabled(False)
        button_layout.addWidget(self.train_btn)
        
        # 加载模型按钮
        self.load_btn = QPushButton("加载模型")
        self.load_btn.clicked.connect(self.load_model)
        button_layout.addWidget(self.load_btn)
        
        # 保存模型按钮
        self.save_btn = QPushButton("保存模型")
        self.save_btn.clicked.connect(self.save_model)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        # 预测按钮
        self.predict_btn = QPushButton("预测图像")
        self.predict_btn.clicked.connect(self.predict_image)
        self.predict_btn.setEnabled(False)
        button_layout.addWidget(self.predict_btn)
        
        button_group.setLayout(button_layout)
        left_layout.addWidget(button_group)
        
        # 进度条
        self.progress = QProgressBar()
        left_layout.addWidget(self.progress)
        
        # 添加到主布局
        main_layout.addWidget(left_panel)
        
        # 创建右侧标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 日志标签页
        self.log_tab = QWidget()
        log_layout = QVBoxLayout(self.log_tab)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(QLabel("训练日志:"))
        log_layout.addWidget(self.log_text)
        self.tabs.addTab(self.log_tab, "日志")
        
        # 模型结构标签页
        self.model_tab = QWidget()
        model_layout = QVBoxLayout(self.model_tab)
        self.model_canvas = ModelCanvas(self.model_tab, width=8, height=6, dpi=100)
        model_layout.addWidget(QLabel("模型结构:"))
        model_layout.addWidget(self.model_canvas)
        self.tabs.addTab(self.model_tab, "模型结构")
        
        # 数据预览标签页
        self.preview_tab = QWidget()
        preview_layout = QVBoxLayout(self.preview_tab)
        
        # 创建分割器用于显示图像和掩码
        splitter = QSplitter(Qt.Horizontal)
        
        # 图像显示区域
        self.image_scroll = QScrollArea()
        self.image_label = ImageLabel()
        self.image_scroll.setWidget(self.image_label)
        self.image_scroll.setWidgetResizable(True)
        splitter.addWidget(self.image_scroll)
        
        # 掩码显示区域
        self.mask_scroll = QScrollArea()
        self.mask_label = ImageLabel()
        self.mask_scroll.setWidget(self.mask_label)
        self.mask_scroll.setWidgetResizable(True)
        splitter.addWidget(self.mask_scroll)
        
        # 文件列表
        self.file_list = QListWidget()
        self.file_list.currentTextChanged.connect(self.show_selected_file)
        
        # 添加到布局
        preview_layout.addWidget(QLabel("数据预览 (选择文件查看):"))
        preview_layout.addWidget(self.file_list)
        preview_layout.addWidget(splitter)
        
        self.tabs.addTab(self.preview_tab, "数据预览")
        
        # 训练历史标签页
        self.history_tab = QWidget()
        history_layout = QVBoxLayout(self.history_tab)
        self.history_canvas = FigureCanvas(Figure(figsize=(8, 6)))
        history_layout.addWidget(QLabel("训练历史:"))
        history_layout.addWidget(self.history_canvas)
        self.tabs.addTab(self.history_tab, "训练历史")
        
    def select_image_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择图像目录")
        if dir_path:
            self.image_dir = dir_path
            self.image_dir_label.setText(os.path.basename(dir_path))
            self.check_directories()
            
    def select_mask_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择掩码目录")
        if dir_path:
            self.mask_dir = dir_path
            self.mask_dir_label.setText(os.path.basename(dir_path))
            self.check_directories()
            
    def check_directories(self):
        if self.image_dir and self.mask_dir:
            self.load_data_btn.setEnabled(True)
            
    def load_data(self):
        try:
            val_split = float(self.val_split.text())
            if val_split <= 0 or val_split >= 1:
                QMessageBox.warning(self, "错误", "验证集比例必须在0和1之间")
                return
                
            im_sz = self.im_sz.value()
            n_classes = self.n_classes.value()
            
            # 禁用按钮防止重复操作
            self.load_data_btn.setEnabled(False)
            self.preview_btn.setEnabled(False)
            
            # 创建并启动数据加载线程
            self.data_thread = DataLoadThread(
                self.image_dir, self.mask_dir, im_sz, n_classes, val_split
            )
            self.data_thread.update_signal.connect(self.update_log)
            self.data_thread.progress_signal.connect(self.progress.setValue)
            self.data_thread.finished_signal.connect(self.data_loading_finished)
            self.data_thread.start()
            
        except ValueError:
            QMessageBox.warning(self, "错误", "验证集比例必须是数字")
            self.load_data_btn.setEnabled(True)
            
    def data_loading_finished(self, X_train, X_val, Y_train, Y_val):
        if X_train is not None:
            self.X_train, self.X_val, self.Y_train, self.Y_val = X_train, X_val, Y_train, Y_val
            self.preview_btn.setEnabled(True)
            
            # 更新文件列表
            self.file_list.clear()
            image_files = [f for f in os.listdir(self.image_dir) if f.endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
            self.file_list.addItems(image_files)
            
            self.log_text.append("数据加载完成，可以预览数据")
        else:
            self.log_text.append("数据加载失败")
            
        self.load_data_btn.setEnabled(True)
        
    def preview_data(self):
        if self.file_list.count() > 0:
            self.tabs.setCurrentIndex(2)  # 切换到数据预览标签页
            self.file_list.setCurrentRow(0)
        else:
            self.log_text.append("没有可预览的数据")
            
    def show_selected_file(self, filename):
        if filename:
            # 显示图像
            img_path = os.path.join(self.image_dir, filename)
            self.image_label.set_image(img_path)
            
            # 显示掩码
            mask_path = os.path.join(self.mask_dir, filename)
            self.mask_label.set_image(mask_path)
            
    def create_model(self):
        try:
            # 获取参数
            n_classes = self.n_classes.value()
            im_sz = self.im_sz.value()
            n_channels = self.n_channels.value()
            n_filters_start = self.n_filters_start.value()
            growth_factor = self.growth_factor.value()
            upconv = self.upconv.isChecked()
            
            # 创建模型
            self.model = self.unet_model(
                n_classes=n_classes,
                im_sz=im_sz,
                n_channels=n_channels,
                n_filters_start=n_filters_start,
                growth_factor=growth_factor,
                upconv=upconv
            )
            
            # 显示模型结构
            self.model_canvas.plot_model_structure(self.model)
            
            # 启用按钮
            self.train_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.predict_btn.setEnabled(True)
            
            self.log_text.append("模型创建成功！")
            self.log_text.append(f"参数: 类别数={n_classes}, 图像尺寸={im_sz}, 通道数={n_channels}")
            self.log_text.append(f"初始过滤器={n_filters_start}, 增长因子={growth_factor}, 转置卷积={upconv}")
            
        except Exception as e:
            self.log_text.append(f"创建模型时出错: {str(e)}")
    
    def train_model(self):
        if self.model is None:
            self.log_text.append("请先创建或加载模型！")
            return
            
        if self.X_train is None:
            self.log_text.append("请先加载训练数据！")
            return
            
        try:
            # 获取训练参数
            epochs = self.epochs.value()
            batch_size = self.batch_size.value()
            learning_rate = float(self.learning_rate.text())
            
            # 更新优化器学习率
            self.model.optimizer.lr = learning_rate
            
            # 创建回调函数
            callbacks = self.get_callbacks()
            
            # 禁用按钮以防止重复训练
            self.train_btn.setEnabled(False)
            self.create_btn.setEnabled(False)
            self.load_data_btn.setEnabled(False)
            
            # 创建并启动训练线程
            self.train_thread = TrainThread(
                self.model, callbacks, self.X_train, self.Y_train, self.X_val, self.Y_val, epochs, batch_size
            )
            self.train_thread.update_signal.connect(self.update_log)
            self.train_thread.progress_signal.connect(self.progress.setValue)
            self.train_thread.finished_signal.connect(self.training_finished)
            self.train_thread.start()
            
        except Exception as e:
            self.log_text.append(f"准备训练数据时出错: {str(e)}")
            self.train_btn.setEnabled(True)
    
    def load_model(self):
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择模型文件", "", "H5 files (*.h5);;All files (*)"
            )
            
            if file_path:
                self.model = self.model_load(file_path)
                self.model_canvas.plot_model_structure(self.model)
                self.train_btn.setEnabled(True)
                self.save_btn.setEnabled(True)
                self.predict_btn.setEnabled(True)
                self.log_text.append(f"模型已从 {file_path} 加载")
                
        except Exception as e:
            self.log_text.append(f"加载模型时出错: {str(e)}")
    
    def save_model(self):
        if self.model is None:
            self.log_text.append("没有模型可保存！")
            return
            
        try:
            timestr = datetime.datetime.now().strftime("(%m-%d-%Y , %H:%M:%S)")
            default_name = f"UNet_{timestr}.h5"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存模型", default_name, "H5 files (*.h5);;All files (*)"
            )
            
            if file_path:
                self.model.save(file_path)
                self.log_text.append(f"模型已保存到 {file_path}")
                
        except Exception as e:
            self.log_text.append(f"保存模型时出错: {str(e)}")
    
    def predict_image(self):
        if self.model is None:
            self.log_text.append("请先创建或加载模型！")
            return
            
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择预测图像", "", "Image files (*.png *.jpg *.jpeg *.tif *.tiff);;All files (*)"
            )
            
            if file_path:
                # 加载和预处理图像
                img = cv2.imread(file_path, cv2.IMREAD_COLOR)
                if img is None:
                    self.log_text.append("无法加载图像！")
                    return
                    
                original_size = img.shape[:2]
                img = cv2.resize(img, (self.im_sz.value(), self.im_sz.value()))
                img = img / 255.0
                img = np.expand_dims(img, axis=0)
                
                # 预测
                prediction = self.model.predict(img)
                
                # 处理预测结果
                pred_mask = np.argmax(prediction[0], axis=-1)
                
                # 将预测结果保存为图像
                output_path = file_path.replace('.', '_prediction.')
                cv2.imwrite(output_path, pred_mask)
                
                self.log_text.append(f"预测完成！结果已保存到: {output_path}")
                
        except Exception as e:
            self.log_text.append(f"预测过程中出错: {str(e)}")
    
    def update_log(self, message):
        self.log_text.append(message)
    
    def training_finished(self):
        self.train_btn.setEnabled(True)
        self.create_btn.setEnabled(True)
        self.load_data_btn.setEnabled(True)
        self.log_text.append("训练完成！")
        
        # 这里可以添加绘制训练历史的代码
    
    # 以下是原始的函数实现
    def unet_model(self, n_classes=5, im_sz=160, n_channels=8, n_filters_start=32, growth_factor=2, upconv=True):
        droprate=0.25
        n_filters = n_filters_start
        inputs = Input((im_sz, im_sz, n_channels))
        conv1 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(inputs)
        conv1 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv1)
        pool1 = MaxPooling2D(pool_size=(2, 2))(conv1)

        n_filters *= growth_factor
        pool1 = BatchNormalization()(pool1)
        conv2 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(pool1)
        conv2 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv2)
        pool2 = MaxPooling2D(pool_size=(2, 2))(conv2)
        pool2 = Dropout(droprate)(pool2)

        n_filters *= growth_factor
        pool2 = BatchNormalization()(pool2)
        conv3 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(pool2)
        conv3 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv3)
        pool3 = MaxPooling2D(pool_size=(2, 2))(conv3)
        pool3 = Dropout(droprate)(pool3)

        n_filters *= growth_factor
        pool3 = BatchNormalization()(pool3)
        conv4_0 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(pool3)
        conv4_0 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv4_0)
        pool4_1 = MaxPooling2D(pool_size=(2, 2))(conv4_0)
        pool4_1 = Dropout(droprate)(pool4_1)

        n_filters *= growth_factor
        pool4_1 = BatchNormalization()(pool4_1)
        conv4_1 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(pool4_1)
        conv4_1 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv4_1)
        pool4_2 = MaxPooling2D(pool_size=(2, 2))(conv4_1)
        pool4_2 = Dropout(droprate)(pool4_2)

        n_filters *= growth_factor
        conv5 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(pool4_2)
        conv5 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv5)

        n_filters //= growth_factor
        if upconv:
            up6_1 = concatenate([Conv2DTranspose(n_filters, (2, 2), strides=(2, 2), padding='same')(conv5), conv4_1])
        else:
            up6_1 = concatenate([UpSampling2D(size=(2, 2))(conv5), conv4_1])
        up6_1 = BatchNormalization()(up6_1)
        conv6_1 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(up6_1)
        conv6_1 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv6_1)
        conv6_1 = Dropout(droprate)(conv6_1)

        n_filters //= growth_factor
        if upconv:
            up6_2 = concatenate([Conv2DTranspose(n_filters, (2, 2), strides=(2, 2), padding='same')(conv6_1), conv4_0])
        else:
            up6_2 = concatenate([UpSampling2D(size=(2, 2))(conv6_1), conv4_0])
        up6_2 = BatchNormalization()(up6_2)
        conv6_2 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(up6_2)
        conv6_2 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv6_2)
        conv6_2 = Dropout(droprate)(conv6_2)

        n_filters //= growth_factor
        if upconv:
            up7 = concatenate([Conv2DTranspose(n_filters, (2, 2), strides=(2, 2), padding='same')(conv6_2), conv3])
        else:
            up7 = concatenate([UpSampling2D(size=(2, 2))(conv6_2), conv3])
        up7 = BatchNormalization()(up7)
        conv7 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(up7)
        conv7 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv7)
        conv7 = Dropout(droprate)(conv7)

        n_filters //= growth_factor
        if upconv:
            up8 = concatenate([Conv2DTranspose(n_filters, (2, 2), strides=(2, 2), padding='same')(conv7), conv2])
        else:
            up8 = concatenate([UpSampling2D(size=(2, 2))(conv7), conv2])
        up8 = BatchNormalization()(up8)
        conv8 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(up8)
        conv8 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv8)
        conv8 = Dropout(droprate)(conv8)

        n_filters //= growth_factor
        if upconv:
            up9 = concatenate([Conv2DTranspose(n_filters, (2, 2), strides=(2, 2), padding='same')(conv8), conv1])
        else:
            up9 = concatenate([UpSampling2D(size=(2, 2))(conv8), conv1])
        conv9 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(up9)
        conv9 = Conv2D(n_filters, (3, 3), activation='relu', padding='same')(conv9)

        conv10 = Conv2D(n_classes, (1, 1), activation='sigmoid')(conv9)

        model = Model(inputs=inputs, outputs=conv10)
        
        model.compile(optimizer=Adam(), loss=weighted_binary_crossentropy, metrics=[accuracy, precision, recall])
        
        return model

    def get_callbacks(self):
        timestr = datetime.datetime.now().strftime("(%m-%d-%Y , %H:%M:%S)")
        model_dir = os.path.join('./models','UNet_{}'.format(timestr))
        checkpoint = ModelCheckpoint(model_dir, monitor='val_loss', verbose=2, 
                                     save_best_only=True, mode='min', save_weights_only=False)

        log_dir = os.path.join('./logs','UNet_{}'.format(timestr))
        tensorboard = TensorBoard(log_dir=log_dir, histogram_freq=0, write_graph=True, 
                                 write_grads=False, write_images=False, embeddings_freq=0, 
                                 embeddings_layer_names=None, embeddings_metadata=None, 
                                 embeddings_data=None, update_freq='epoch')

        callbacks_list = [checkpoint, tensorboard] 
        
        return callbacks_list

    def model_load(self, model_path):
        model = load_model(model_path, custom_objects={
            'weighted_binary_crossentropy': weighted_binary_crossentropy,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall
        }, compile=False)

        model.compile(optimizer=Adam(), loss=weighted_binary_crossentropy, 
                     metrics=[accuracy, precision, recall])
        return model

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = UNetGUI()
    gui.show()
    sys.exit(app.exec_())