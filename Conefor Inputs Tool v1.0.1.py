import sys
import os
import tempfile
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGroupBox, QLabel, QLineEdit, QPushButton, QCheckBox, 
                            QRadioButton, QComboBox, QAction, QMenu, QMenuBar, QStatusBar,
                            QTabWidget, QTextEdit, QSplitter, QFileDialog, QMessageBox,
                            QFormLayout, QListWidget, QListWidgetItem, QProgressBar)
from PyQt5.QtGui import QIcon, QFont, QDoubleValidator
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import fiona
from shapely.geometry import shape

class GISProcessor:
    """GIS数据处理类，用于准备Conefor输入数据"""
    def __init__(self):
        self.input_file = ""
        self.output_dir = ""
        self.node_field = ""
        self.area_field = ""
        self.threshold = 1000
        self.distance_type = "Euclidean"
        
    def extract_nodes(self, shapefile_path, output_path, node_field, area_field):
        """从Shapefile中提取节点信息"""
        try:
            # 使用Fiona打开Shapefile
            with fiona.open(shapefile_path, 'r') as src:
                # 创建输出文件
                with open(output_path, 'w') as f:
                    # 写入标题行
                    if area_field and area_field in src.schema['properties']:
                        f.write("id\tarea\n")
                    else:
                        f.write("id\n")
                    
                    # 遍历要素
                    for feature in src:
                        node_id = feature['properties'][node_field]
                        
                        if area_field and area_field in src.schema['properties']:
                            area = feature['properties'][area_field]
                            f.write(f"{node_id}\t{area}\n")
                        else:
                            f.write(f"{node_id}\n")
            
            return True, f"成功提取 {len(src)} 个节点"
            
        except Exception as e:
            return False, f"提取节点时出错: {str(e)}"
    
    def calculate_distances(self, shapefile_path, output_path, node_field, threshold):
        """计算节点之间的距离"""
        try:
            # 使用Fiona打开Shapefile
            with fiona.open(shapefile_path, 'r') as src:
                # 获取所有要素和几何体
                features = list(src)
                geometries = [shape(feature['geometry']) for feature in features]
                node_ids = [feature['properties'][node_field] for feature in features]
                
                # 创建输出文件
                with open(output_path, 'w') as f:
                    f.write("id1\tid2\tdistance\n")
                    
                    # 计算每对节点之间的距离
                    count = 0
                    for i in range(len(geometries)):
                        for j in range(i+1, len(geometries)):
                            distance = geometries[i].distance(geometries[j])
                            
                            if distance <= threshold:
                                f.write(f"{node_ids[i]}\t{node_ids[j]}\t{distance:.2f}\n")
                                count += 1
            
            return True, f"成功计算 {count} 对节点之间的距离"
            
        except Exception as e:
            return False, f"计算距离时出错: {str(e)}"

class ProcessingThread(QThread):
    """处理线程，避免界面卡顿"""
    update_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, processor, task_type, **kwargs):
        super().__init__()
        self.processor = processor
        self.task_type = task_type
        self.kwargs = kwargs
        
    def run(self):
        try:
            if self.task_type == "extract_nodes":
                self.update_signal.emit("🔍 开始提取节点信息...")
                success, message = self.processor.extract_nodes(**self.kwargs)
            elif self.task_type == "calculate_distances":
                self.update_signal.emit("📏 开始计算节点距离...")
                success, message = self.processor.calculate_distances(**self.kwargs)
            else:
                success, message = False, "未知任务类型"
                
            self.finished_signal.emit(success, message)
            
        except Exception as e:
            self.finished_signal.emit(False, f"处理过程中出错: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.processor = GISProcessor()
        self.processing_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 设置窗口基本属性
        self.setWindowTitle("🌍 Conefor Inputs Tool")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建主分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧输入区域
        input_widget = self.create_input_area()
        splitter.addWidget(input_widget)
        
        # 创建右侧输出区域
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("📝 处理日志将显示在这里...")
        splitter.addWidget(self.output_area)
        
        # 设置分割器比例
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 ✅")
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("📂 文件")
        
        new_action = QAction("🆕 新建项目", self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("📂 打开项目", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("💾 保存项目", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("🛠️ 工具")
        
        extract_nodes_action = QAction("🔍 提取节点", self)
        extract_nodes_action.triggered.connect(self.extract_nodes)
        tools_menu.addAction(extract_nodes_action)
        
        calculate_distances_action = QAction("📏 计算距离", self)
        calculate_distances_action.triggered.connect(self.calculate_distances)
        tools_menu.addAction(calculate_distances_action)
        
        batch_process_action = QAction("🔁 批量处理", self)
        batch_process_action.triggered.connect(self.batch_process)
        tools_menu.addAction(batch_process_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("❓ 帮助")
        
        help_action = QAction("📚 帮助内容", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("ℹ️ 关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_input_area(self):
        """创建输入区域"""
        tab_widget = QTabWidget()
        
        # 数据输入标签页
        input_tab = QWidget()
        input_layout = QVBoxLayout(input_tab)
        
        # 文件选择组
        file_group = QGroupBox("📁 文件选择")
        file_layout = QFormLayout(file_group)
        
        self.input_file_edit = QLineEdit()
        input_browse_btn = QPushButton("浏览...")
        input_browse_btn.clicked.connect(self.browse_input_file)
        
        input_file_layout = QHBoxLayout()
        input_file_layout.addWidget(self.input_file_edit)
        input_file_layout.addWidget(input_browse_btn)
        
        self.output_dir_edit = QLineEdit()
        output_browse_btn = QPushButton("浏览...")
        output_browse_btn.clicked.connect(self.browse_output_dir)
        
        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(self.output_dir_edit)
        output_dir_layout.addWidget(output_browse_btn)
        
        file_layout.addRow("输入文件:", input_file_layout)
        file_layout.addRow("输出目录:", output_dir_layout)
        
        # 节点设置组
        node_group = QGroupBox("🟢 节点设置")
        node_layout = QFormLayout(node_group)
        
        self.node_field_combo = QComboBox()
        self.area_field_combo = QComboBox()
        
        node_layout.addRow("节点ID字段:", self.node_field_combo)
        node_layout.addRow("面积字段:", self.area_field_combo)
        
        # 连接设置组
        connection_group = QGroupBox("🔗 连接设置")
        connection_layout = QFormLayout(connection_group)
        
        self.distance_type_combo = QComboBox()
        self.distance_type_combo.addItems(["欧氏距离 (Euclidean)", "成本距离 (Cost)", "最小路径 (Least Cost Path)"])
        
        self.threshold_edit = QLineEdit("1000")
        # 使用PyQt5内置的QDoubleValidator
        validator = QDoubleValidator(0, 1000000, 2)
        self.threshold_edit.setValidator(validator)
        
        connection_layout.addRow("距离类型:", self.distance_type_combo)
        connection_layout.addRow("距离阈值:", self.threshold_edit)
        
        input_layout.addWidget(file_group)
        input_layout.addWidget(node_group)
        input_layout.addWidget(connection_group)
        input_layout.addStretch()
        
        tab_widget.addTab(input_tab, "📥 数据输入")
        
        # 批量处理标签页
        batch_tab = QWidget()
        batch_layout = QVBoxLayout(batch_tab)
        
        batch_group = QGroupBox("🔁 批量处理")
        batch_group_layout = QVBoxLayout(batch_group)
        
        self.file_list = QListWidget()
        add_files_btn = QPushButton("添加文件")
        add_files_btn.clicked.connect(self.add_batch_files)
        remove_file_btn = QPushButton("移除选中")
        remove_file_btn.clicked.connect(self.remove_batch_file)
        
        batch_btn_layout = QHBoxLayout()
        batch_btn_layout.addWidget(add_files_btn)
        batch_btn_layout.addWidget(remove_file_btn)
        
        batch_group_layout.addWidget(self.file_list)
        batch_group_layout.addLayout(batch_btn_layout)
        
        batch_process_btn = QPushButton("开始批量处理")
        batch_process_btn.clicked.connect(self.batch_process)
        batch_process_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        batch_layout.addWidget(batch_group)
        batch_layout.addWidget(batch_process_btn)
        
        tab_widget.addTab(batch_tab, "🔁 批量处理")
        
        return tab_widget
    
    def browse_input_file(self):
        """浏览输入文件"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "选择输入文件", "", 
            "GIS文件 (*.shp *.geojson *.gpkg);;所有文件 (*.*)"
        )
        if filename:
            self.input_file_edit.setText(filename)
            self.load_field_names(filename)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = QFileDialog.getExistingDirectory(self, "选择输出目录")
        if directory:
            self.output_dir_edit.setText(directory)
    
    def load_field_names(self, filename):
        """加载Shapefile的字段名"""
        if not (filename.lower().endswith('.shp') or 
                filename.lower().endswith('.geojson') or 
                filename.lower().endswith('.gpkg')):
            return
            
        try:
            # 使用Fiona打开文件获取字段信息
            with fiona.open(filename, 'r') as src:
                # 清空现有字段
                self.node_field_combo.clear()
                self.area_field_combo.clear()
                self.area_field_combo.addItem("(无)")  # 添加一个空选项
                
                # 添加字段名
                for field_name in src.schema['properties'].keys():
                    self.node_field_combo.addItem(field_name)
                    self.area_field_combo.addItem(field_name)
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法读取字段信息: {str(e)}")
    
    def add_batch_files(self):
        """添加批量处理文件"""
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "选择批量处理文件", "", 
            "GIS文件 (*.shp *.geojson *.gpkg);;所有文件 (*.*)"
        )
        for filename in filenames:
            QListWidgetItem(filename, self.file_list)
    
    def remove_batch_file(self):
        """移除选中的批量处理文件"""
        current_row = self.file_list.currentRow()
        if current_row >= 0:
            self.file_list.takeItem(current_row)
    
    def new_project(self):
        """新建项目"""
        reply = QMessageBox.question(self, "新建项目", 
                                    "确定要创建新项目吗？当前项目可能未保存。",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clear_project_data()
            self.status_bar.showMessage("已创建新项目 🆕")
    
    def open_project(self):
        """打开项目"""
        filename, _ = QFileDialog.getOpenFileName(self, "打开项目", "", "Conefor Inputs 项目文件 (*.cft)")
        if filename:
            # 这里只是模拟打开项目
            self.status_bar.showMessage(f"已打开项目: {os.path.basename(filename)} 📂")
    
    def save_project(self):
        """保存项目"""
        if not self.input_file_edit.text():
            QMessageBox.warning(self, "警告", "请先选择输入文件！")
            return
            
        filename, _ = QFileDialog.getSaveFileName(self, "保存项目", "", "Conefor Inputs 项目文件 (*.cft)")
        if filename:
            # 这里只是模拟保存项目
            self.status_bar.showMessage(f"项目已保存至: {filename} 💾")
            QMessageBox.information(self, "成功", "项目保存成功！")
    
    def clear_project_data(self):
        """清除项目数据"""
        self.input_file_edit.clear()
        self.output_dir_edit.clear()
        self.node_field_combo.clear()
        self.area_field_combo.clear()
        self.threshold_edit.setText("1000")
        self.distance_type_combo.setCurrentIndex(0)
        self.file_list.clear()
        self.output_area.clear()
    
    def extract_nodes(self):
        """提取节点信息"""
        if not self.validate_inputs():
            return
            
        input_file = self.input_file_edit.text()
        output_dir = self.output_dir_edit.text()
        node_field = self.node_field_combo.currentText()
        area_field = self.area_field_combo.currentText() if self.area_field_combo.currentText() != "(无)" else ""
        
        output_path = os.path.join(output_dir, "nodes.txt")
        
        # 启动处理线程
        self.processing_thread = ProcessingThread(
            self.processor, "extract_nodes",
            shapefile_path=input_file,
            output_path=output_path,
            node_field=node_field,
            area_field=area_field
        )
        self.connect_thread_signals()
        self.processing_thread.start()
        
        self.status_bar.showMessage("正在提取节点... ⏳")
        self.progress_bar.setVisible(True)
    
    def calculate_distances(self):
        """计算节点距离"""
        if not self.validate_inputs():
            return
            
        input_file = self.input_file_edit.text()
        output_dir = self.output_dir_edit.text()
        node_field = self.node_field_combo.currentText()
        threshold = float(self.threshold_edit.text())
        
        output_path = os.path.join(output_dir, "distances.txt")
        
        # 启动处理线程
        self.processing_thread = ProcessingThread(
            self.processor, "calculate_distances",
            shapefile_path=input_file,
            output_path=output_path,
            node_field=node_field,
            threshold=threshold
        )
        self.connect_thread_signals()
        self.processing_thread.start()
        
        self.status_bar.showMessage("正在计算距离... ⏳")
        self.progress_bar.setVisible(True)
    
    def batch_process(self):
        """批量处理"""
        if self.file_list.count() == 0:
            QMessageBox.warning(self, "警告", "请先添加要处理的文件！")
            return
            
        if not self.output_dir_edit.text():
            QMessageBox.warning(self, "警告", "请先选择输出目录！")
            return
            
        # 这里可以实现批量处理逻辑
        QMessageBox.information(self, "批量处理", "批量处理功能将在这里实现 🔁")
    
    def validate_inputs(self):
        """验证输入"""
        if not self.input_file_edit.text() or not os.path.exists(self.input_file_edit.text()):
            QMessageBox.warning(self, "输入错误", "请指定有效的输入文件！")
            return False
            
        if not self.output_dir_edit.text() or not os.path.isdir(self.output_dir_edit.text()):
            QMessageBox.warning(self, "输入错误", "请指定有效的输出目录！")
            return False
            
        if self.node_field_combo.currentText() == "":
            QMessageBox.warning(self, "输入错误", "请选择节点ID字段！")
            return False
            
        try:
            threshold = float(self.threshold_edit.text())
            if threshold <= 0:
                QMessageBox.warning(self, "输入错误", "距离阈值必须大于0！")
                return False
        except ValueError:
            QMessageBox.warning(self, "输入错误", "距离阈值必须是有效数字！")
            return False
            
        return True
    
    def connect_thread_signals(self):
        """连接线程信号"""
        self.processing_thread.update_signal.connect(self.update_output)
        self.processing_thread.progress_signal.connect(self.update_progress)
        self.processing_thread.finished_signal.connect(self.processing_finished)
    
    def update_output(self, message):
        """更新输出区域"""
        self.output_area.append(message)
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
    
    def processing_finished(self, success, message):
        """处理完成"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_bar.showMessage("处理完成 ✅")
            self.update_output(f"✅ {message}\n")
            QMessageBox.information(self, "成功", message)
        else:
            self.status_bar.showMessage("处理失败 ❌")
            self.update_output(f"❌ {message}\n")
            QMessageBox.critical(self, "错误", message)
    
    def show_help(self):
        """显示帮助"""
        QMessageBox.information(self, "帮助", 
                              "Conefor Inputs Tool 帮助文档:\n\n"
                              "这是一个用于准备Conefor Sensinode输入数据的工具。\n"
                              "功能包括:\n"
                              "• 从GIS数据中提取节点信息\n"
                              "• 计算节点之间的距离\n"
                              "• 批量处理多个文件\n\n"
                              "输出文件可以直接用于Conefor Sensinode计算 📚")
    
    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(self, "关于 Conefor Inputs Tool", 
                         "Conefor Inputs Tool\n\n"
                         "用于准备Conefor Sensinode输入数据的GIS处理工具\n\n"
                         "版本: 1.0\n"
                         "开发人员: Your Name\n\n"
                         "许可证: MIT License\n"
                         "© 2023 Your Organization ℹ️")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体，确保Unicode符号正常显示
    font = QFont()
    font.setFamily("Segoe UI Emoji")  # 支持彩色emoji的字体
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())