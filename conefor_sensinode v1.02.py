import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGroupBox, QLabel, QLineEdit, QPushButton, QCheckBox, 
                            QRadioButton, QComboBox, QAction, QMenu, QMenuBar, QStatusBar,
                            QTabWidget, QTextEdit, QSplitter, QFileDialog, QMessageBox,
                            QFormLayout)
from PyQt5.QtGui import QIcon, QColor, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class SensinodeProgram:
    """后端处理类，模拟原程序的计算功能"""
    def __init__(self):
        self.nlFlag = False
        self.ncFlag = False
        self.hFlag = False
        self.iicFlag = False
        self.ccpFlag = False
        self.lcpFlag = False
        self.fFlag = False
        self.awfFlag = False
        self.pcFlag = False
        
        # 模拟时间数据
        self.nlTime = 0
        self.ncTime = 0
        self.hiicTime = 0
        self.hTime = 0
        self.iicTime = 0
        self.ccpTime = 0
        self.lcpTime = 0
        self.fTime = 0
        self.awfTime = 0
        self.pcTime = 0

class CalculationThread(QThread):
    """计算线程，避免界面卡顿"""
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, program):
        super().__init__()
        self.program = program
        
    def run(self):
        # 模拟计算过程
        import time
        self.update_signal.emit("🔍 开始计算...\n")
        time.sleep(1)
        
        if self.program.ccpFlag:
            self.update_signal.emit("📊 计算 CCP 指数...\n")
            time.sleep(1)
            self.program.ccpTime = 125000
        if self.program.lcpFlag:
            self.update_signal.emit("📊 计算 LCP 指数...\n")
            time.sleep(1)
            self.program.lcpTime = 95000
        if self.program.iicFlag:
            self.update_signal.emit("📊 计算 IIC 指数...\n")
            time.sleep(1)
            self.program.iicTime = 150000
            
        self.update_signal.emit("✅ 计算完成!\n")
        self.finished_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.program = SensinodeProgram()
        self.calc_thread = None
        self.init_ui()
        
    def init_ui(self):
        """初始化界面"""
        # 设置窗口基本属性
        self.setWindowTitle("🌈 Conefor Sensinode 2.2")
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建主分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建输入区域
        input_widget = self.create_input_area()
        splitter.addWidget(input_widget)
        
        # 创建输出区域
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("📝 执行日志将显示在这里...")
        splitter.addWidget(self.output_area)
        
        # 设置分割器比例
        splitter.setSizes([400, 300])
        
        main_layout.addWidget(splitter)
        
        # 创建状态栏
        self.statusBar().showMessage("就绪 ✅")
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("📂 文件")
        
        new_action = QAction("🆕 新建", self)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("📂 打开", self)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("💾 保存", self)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 执行菜单
        execute_menu = menubar.addMenu("▶️ 执行")
        
        start_action = QAction("▶️ 开始计算", self)
        start_action.triggered.connect(self.start_execution)
        execute_menu.addAction(start_action)
        
        pause_action = QAction("⏸️ 暂停", self)
        pause_action.triggered.connect(self.pause_execution)
        execute_menu.addAction(pause_action)
        
        stop_action = QAction("⏹️ 停止", self)
        stop_action.triggered.connect(self.stop_execution)
        execute_menu.addAction(stop_action)
        
        # 查看菜单
        view_menu = menubar.addMenu("👀 查看")
        
        results_action = QAction("📊 结果", self)
        results_action.triggered.connect(self.view_results)
        view_menu.addAction(results_action)
        
        adj_action = QAction("🔗 邻接关系", self)
        adj_action.triggered.connect(self.view_adjacencies)
        view_menu.addAction(adj_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("❓ 帮助")
        
        help_action = QAction("📚 帮助内容", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("ℹ️ 关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("工具")
        
        new_btn = QPushButton("🆕 新建")
        new_btn.clicked.connect(self.new_project)
        toolbar.addWidget(new_btn)
        
        open_btn = QPushButton("📂 打开")
        open_btn.clicked.connect(self.open_project)
        toolbar.addWidget(open_btn)
        
        save_btn = QPushButton("💾 保存")
        save_btn.clicked.connect(self.save_project)
        toolbar.addWidget(save_btn)
        
        toolbar.addSeparator()
        
        run_btn = QPushButton("▶️ 运行")
        run_btn.clicked.connect(self.start_execution)
        toolbar.addWidget(run_btn)
        
        stop_btn = QPushButton("⏹️ 停止")
        stop_btn.clicked.connect(self.stop_execution)
        toolbar.addWidget(stop_btn)
        
    def create_input_area(self):
        """创建输入区域"""
        tab_widget = QTabWidget()
        
        # 项目设置标签页
        project_tab = QWidget()
        project_layout = QFormLayout(project_tab)
        
        self.project_name_edit = QLineEdit()
        self.project_location_edit = QLineEdit()
        self.version_edit = QLineEdit("2.2")
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_project_location)
        
        location_layout = QHBoxLayout()
        location_layout.addWidget(self.project_location_edit)
        location_layout.addWidget(browse_btn)
        
        project_layout.addRow("项目名称 🏷️:", self.project_name_edit)
        project_layout.addRow("项目位置 📍:", location_layout)
        project_layout.addRow("版本号 🔢:", self.version_edit)
        
        tab_widget.addTab(project_tab, "📋 项目设置")
        
        # 节点和连接标签页
        nodes_tab = QWidget()
        nodes_layout = QVBoxLayout(nodes_tab)
        
        # 节点设置
        nodes_group = QGroupBox("🟢 节点设置")
        nodes_group_layout = QVBoxLayout(nodes_group)
        
        nodes_file_layout = QHBoxLayout()
        self.nodes_edit = QLineEdit()
        nodes_browse_btn = QPushButton("浏览...")
        nodes_browse_btn.clicked.connect(lambda: self.browse_file(self.nodes_edit))
        nodes_file_layout.addWidget(self.nodes_edit)
        nodes_file_layout.addWidget(nodes_browse_btn)
        
        self.add_nodes_checkbox = QCheckBox("添加额外节点 ➕")
        
        nodes_group_layout.addLayout(nodes_file_layout)
        nodes_group_layout.addWidget(self.add_nodes_checkbox)
        
        # 连接设置
        connections_group = QGroupBox("🔗 连接设置")
        connections_layout = QVBoxLayout(connections_group)
        
        connections_file_layout = QHBoxLayout()
        self.connections_edit = QLineEdit()
        connections_browse_btn = QPushButton("浏览...")
        connections_browse_btn.clicked.connect(lambda: self.browse_file(self.connections_edit))
        connections_file_layout.addWidget(self.connections_edit)
        connections_file_layout.addWidget(connections_browse_btn)
        
        self.connection_type_combo = QComboBox()
        self.connection_type_combo.addItems(["距离 (Distances)", "概率 (Probabilities)", "链接 (Links)"])
        
        structure_layout = QHBoxLayout()
        self.full_radio = QRadioButton("完全 (Full)")
        self.partial_radio = QRadioButton("部分 (Partial)")
        self.full_radio.setChecked(True)
        structure_layout.addWidget(self.full_radio)
        structure_layout.addWidget(self.partial_radio)
        
        # 修复这里：使用正确的变量名 connections_layout 而不是 connections_group_layout
        connections_layout.addLayout(connections_file_layout)
        connections_layout.addWidget(QLabel("连接类型 📦:"))
        connections_layout.addWidget(self.connection_type_combo)
        connections_layout.addWidget(QLabel("结构类型 🏗️:"))
        connections_layout.addLayout(structure_layout)
        
        # 阈值设置
        thresholds_group = QGroupBox("🎚️ 阈值设置")
        thresholds_layout = QFormLayout(thresholds_group)
        
        self.threshold_edit = QLineEdit("1000")
        self.k_distance_edit = QLineEdit("100")
        self.k_prob_edit = QLineEdit("0.5")
        self.landscape_area_edit = QLineEdit("10000")
        
        thresholds_layout.addRow("邻接距离阈值 📏:", self.threshold_edit)
        thresholds_layout.addRow("概率距离 K 📊:", self.k_distance_edit)
        thresholds_layout.addRow("概率值 K 🔄:", self.k_prob_edit)
        thresholds_layout.addRow("景观面积 🌄:", self.landscape_area_edit)
        
        nodes_layout.addWidget(nodes_group)
        nodes_layout.addWidget(connections_group)
        nodes_layout.addWidget(thresholds_group)
        
        tab_widget.addTab(nodes_tab, "🔗 节点和连接")
        
        # 指数计算标签页
        indices_tab = QWidget()
        indices_layout = QVBoxLayout(indices_tab)
        
        indices_group = QGroupBox("📈 连接指数计算")
        indices_group_layout = QVBoxLayout(indices_group)
        
        # 第一行复选框
        row1_layout = QHBoxLayout()
        self.ccp_checkbox = QCheckBox("CCP (Closest Component Probability)")
        self.lcp_checkbox = QCheckBox("LCP (Least Cost Path)")
        self.iic_checkbox = QCheckBox("IIC (Integral Index of Connectivity)")
        row1_layout.addWidget(self.ccp_checkbox)
        row1_layout.addWidget(self.lcp_checkbox)
        row1_layout.addWidget(self.iic_checkbox)
        
        # 第二行复选框
        row2_layout = QHBoxLayout()
        self.nc_checkbox = QCheckBox("NC (Number of Components)")
        self.nl_checkbox = QCheckBox("NL (Number of Links)")
        self.h_checkbox = QCheckBox("H (Harary Index)")
        row2_layout.addWidget(self.nc_checkbox)
        row2_layout.addWidget(self.nl_checkbox)
        row2_layout.addWidget(self.h_checkbox)
        
        # 第三行复选框
        row3_layout = QHBoxLayout()
        self.f_checkbox = QCheckBox("F (Flux)")
        self.awf_checkbox = QCheckBox("AWF (All-Weighted Flux)")
        self.pc_checkbox = QCheckBox("PC (Probability of Connectivity)")
        row3_layout.addWidget(self.f_checkbox)
        row3_layout.addWidget(self.awf_checkbox)
        row3_layout.addWidget(self.pc_checkbox)
        
        indices_group_layout.addLayout(row1_layout)
        indices_group_layout.addLayout(row2_layout)
        indices_group_layout.addLayout(row3_layout)
        
        # 计算按钮
        calc_btn_layout = QHBoxLayout()
        calc_btn = QPushButton("▶️ 开始计算")
        calc_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        calc_btn.clicked.connect(self.start_execution)
        calc_btn_layout.addWidget(calc_btn)
        
        indices_layout.addWidget(indices_group)
        indices_layout.addLayout(calc_btn_layout)
        
        tab_widget.addTab(indices_tab, "🧮 指数计算")
        
        return tab_widget
    
    def browse_project_location(self):
        """浏览项目位置"""
        directory = QFileDialog.getExistingDirectory(self, "选择项目位置")
        if directory:
            self.project_location_edit.setText(directory)
    
    def browse_file(self, line_edit):
        """浏览文件"""
        filename, _ = QFileDialog.getOpenFileName(self, "选择文件")
        if filename:
            line_edit.setText(filename)
    
    def new_project(self):
        """新建项目"""
        reply = QMessageBox.question(self, "新建项目", 
                                    "确定要创建新项目吗？当前项目可能未保存。",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.clear_project_data()
            self.statusBar().showMessage("已创建新项目 🆕")
    
    def open_project(self):
        """打开项目"""
        filename, _ = QFileDialog.getOpenFileName(self, "打开项目", "", "Conefor 项目文件 (*.cfr)")
        if filename:
            # 这里只是模拟打开项目
            self.project_name_edit.setText(os.path.basename(filename))
            self.project_location_edit.setText(os.path.dirname(filename))
            self.statusBar().showMessage(f"已打开项目: {os.path.basename(filename)} 📂")
    
    def save_project(self):
        """保存项目"""
        if not self.project_name_edit.text():
            QMessageBox.warning(self, "警告", "请先输入项目名称！")
            return
            
        if not self.project_location_edit.text():
            QMessageBox.warning(self, "警告", "请先选择项目位置！")
            return
            
        filename = os.path.join(self.project_location_edit.text(), 
                               self.project_name_edit.text() + ".cfr")
        # 这里只是模拟保存项目
        self.statusBar().showMessage(f"项目已保存至: {filename} 💾")
        QMessageBox.information(self, "成功", "项目保存成功！")
    
    def clear_project_data(self):
        """清除项目数据"""
        self.project_name_edit.clear()
        self.project_location_edit.clear()
        self.nodes_edit.clear()
        self.connections_edit.clear()
        self.add_nodes_checkbox.setChecked(False)
        self.full_radio.setChecked(True)
        self.connection_type_combo.setCurrentIndex(0)
        self.threshold_edit.setText("1000")
        self.k_distance_edit.setText("100")
        self.k_prob_edit.setText("0.5")
        self.landscape_area_edit.setText("10000")
        
        # 清除所有复选框
        for cb in [self.ccp_checkbox, self.lcp_checkbox, self.iic_checkbox,
                  self.nc_checkbox, self.nl_checkbox, self.h_checkbox,
                  self.f_checkbox, self.awf_checkbox, self.pc_checkbox]:
            cb.setChecked(False)
        
        self.output_area.clear()
    
    def start_execution(self):
        """开始执行计算"""
        # 检查必要的输入
        if not self.nodes_edit.text() or not os.path.exists(self.nodes_edit.text()):
            QMessageBox.warning(self, "输入错误", "请指定有效的节点文件！")
            return
            
        # 更新程序设置
        self.program.ccpFlag = self.ccp_checkbox.isChecked()
        self.program.lcpFlag = self.lcp_checkbox.isChecked()
        self.program.iicFlag = self.iic_checkbox.isChecked()
        self.program.ncFlag = self.nc_checkbox.isChecked()
        self.program.nlFlag = self.nl_checkbox.isChecked()
        self.program.hFlag = self.h_checkbox.isChecked()
        self.program.fFlag = self.f_checkbox.isChecked()
        self.program.awfFlag = self.awf_checkbox.isChecked()
        self.program.pcFlag = self.pc_checkbox.isChecked()
        
        # 启动计算线程
        self.calc_thread = CalculationThread(self.program)
        self.calc_thread.update_signal.connect(self.update_output)
        self.calc_thread.finished_signal.connect(self.calculation_finished)
        self.calc_thread.start()
        
        self.statusBar().showMessage("计算中... ⏳")
    
    def update_output(self, message):
        """更新输出区域"""
        self.output_area.append(message)
    
    def calculation_finished(self):
        """计算完成处理"""
        self.statusBar().showMessage("计算完成 ✅")
        self.update_output("⌛ 计算时间统计:\n")
        # 显示各指数计算时间
        if self.program.ccpFlag:
            self.update_output(f"  CCP 指数计算时间: {self.program.ccpTime} ms\n")
        if self.program.lcpFlag:
            self.update_output(f"  LCP 指数计算时间: {self.program.lcpTime} ms\n")
        if self.program.iicFlag:
            self.update_output(f"  IIC 指数计算时间: {self.program.iicTime} ms\n")
    
    def pause_execution(self):
        """暂停执行"""
        if self.calc_thread and self.calc_thread.isRunning():
            # 实际应用中需要实现线程暂停功能
            self.statusBar().showMessage("计算已暂停 ⏸️")
            self.update_output("计算已暂停 ⏸️\n")
    
    def stop_execution(self):
        """停止执行"""
        if self.calc_thread and self.calc_thread.isRunning():
            # 实际应用中需要实现线程停止功能
            self.calc_thread.terminate()
            self.statusBar().showMessage("计算已停止 ⏹️")
            self.update_output("计算已停止 ⏹️\n")
    
    def view_results(self):
        """查看结果"""
        QMessageBox.information(self, "查看结果", "结果查看功能将在这里实现 📊")
    
    def view_adjacencies(self):
        """查看邻接关系"""
        QMessageBox.information(self, "邻接关系", "邻接关系查看功能将在这里实现 🔗")
    
    def show_help(self):
        """显示帮助"""
        QMessageBox.information(self, "帮助", 
                              "Conefor Sensinode 2.2 帮助文档:\n\n"
                              "这是一个用于量化栖息地区域对维持或改善景观连接度重要性的软件。\n"
                              "更多信息请访问: http://www.conefor.org 📚")
    
    def show_about(self):
        """显示关于信息"""
        QMessageBox.about(self, "关于 Conefor Sensinode 2.2", 
                         "Conefor Sensinode 2.2\n\n"
                         "用于景观连接度分析的软件工具\n\n"
                         "作者:\n"
                         "Santiago Saura (santiago.saura@upm.es)\n"
                         "Josep Torné (josep.torne@gmail.com)\n\n"
                         "许可证: GNU GPL v3\n"
                         "http://www.conefor.org ℹ️")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体，确保Unicode符号正常显示
    font = QFont()
    font.setFamily("Segoe UI Emoji")  # 支持彩色emoji的字体
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())