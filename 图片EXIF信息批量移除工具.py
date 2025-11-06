import sys
import os
import glob
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                            QProgressBar, QTextEdit, QFileDialog, QMessageBox,
                            QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QTextCursor
from PIL import Image

# 定义unicode多彩符号用于美化界面
SYMBOL_FOLDER = "📂"
SYMBOL_IMAGE = "🖼️"
SYMBOL_CHECK = "✅"
SYMBOL_ERROR = "❌"
SYMBOL_WARNING = "⚠️"
SYMBOL_INFO = "ℹ️"
SYMBOL_PROCESS = "🔄"
SYMBOL_DELETE = "🗑️"
SYMBOL_START = "▶️"
SYMBOL_STOP = "⏹️"
SYMBOL_COMPLETE = "🏁"
SYMBOL_SETTINGS = "⚙️"
SYMBOL_HELP = "❓"

class ExifRemoverThread(QThread):
    """处理EXIF信息移除的线程类，避免UI卡顿"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str, str)  # 消息内容，消息类型
    process_complete = pyqtSignal(int, int)  # 总文件数，成功处理数
    
    def __init__(self, folder_path, file_formats):
        super().__init__()
        self.folder_path = folder_path
        self.file_formats = file_formats
        self.running = True
        
    def run(self):
        # 准备图片格式列表
        image_extensions = [f'*.{fmt.lower()}' for fmt in self.file_formats if fmt]
        image_files = []
        
        # 遍历文件夹及其子文件夹寻找图片文件
        self.status_updated.emit(f"{SYMBOL_PROCESS} 正在搜索图片文件...", "info")
        for ext in image_extensions:
            image_files.extend(glob.glob(os.path.join(self.folder_path, '**', ext), recursive=True))
        
        total_files = len(image_files)
        success_count = 0
        
        if total_files == 0:
            self.status_updated.emit(f"{SYMBOL_WARNING} 未找到任何图片文件", "warning")
            self.process_complete.emit(0, 0)
            return
        
        self.status_updated.emit(f"{SYMBOL_INFO} 找到 {total_files} 个图片文件，开始处理...", "info")
        
        # 处理每个图片文件
        for i, file_path in enumerate(image_files):
            if not self.running:
                break
                
            try:
                # 打开图片
                with Image.open(file_path) as img:
                    # 检查是否有EXIF信息
                    exif_data = img.getexif()
                    if exif_data:
                        # 创建一个没有EXIF信息的新图片
                        data = list(img.getdata())
                        new_img = Image.new(img.mode, img.size)
                        new_img.putdata(data)
                        
                        # 保存处理后的图片，覆盖原文件
                        new_img.save(file_path)
                        success_count += 1
                        self.status_updated.emit(
                            f"{SYMBOL_CHECK} 已移除EXIF信息: {os.path.basename(file_path)}", "success")
                    else:
                        self.status_updated.emit(
                            f"{SYMBOL_INFO} 无EXIF信息: {os.path.basename(file_path)}", "info")
            
            except Exception as e:
                self.status_updated.emit(
                    f"{SYMBOL_ERROR} 处理失败 {os.path.basename(file_path)}: {str(e)}", "error")
            
            # 更新进度
            progress = int((i + 1) / total_files * 100)
            self.progress_updated.emit(progress)
        
        # 处理完成
        if self.running:
            self.status_updated.emit(f"{SYMBOL_COMPLETE} 处理完成!", "success")
        else:
            self.status_updated.emit(f"{SYMBOL_STOP} 处理已停止", "warning")
            
        self.process_complete.emit(total_files, success_count)
    
    def stop(self):
        self.running = False
        self.wait()

class ExifRemoverApp(QMainWindow):
    """主应用窗口类"""
    def __init__(self):
        super().__init__()
        # 先定义支持的图片格式，再初始化UI
        self.supported_formats = ["jpg", "jpeg", "png", "gif", "bmp", "tiff"]
        self.init_ui()
        self.thread = None
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle(f"{SYMBOL_DELETE} 图片EXIF信息批量移除工具")
        self.setGeometry(100, 100, 850, 650)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # 标题标签
        title_label = QLabel(f"{SYMBOL_DELETE} 图片EXIF信息批量移除工具")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin: 10px 0px;")
        main_layout.addWidget(title_label)
        
        # 文件夹选择区域
        folder_group = QGroupBox(f"{SYMBOL_FOLDER} 目标文件夹")
        folder_group.setStyleSheet("QGroupBox {font-weight: bold; color: #34495e; border: 1px solid #bdc3c7; border-radius: 5px; margin-top: 10px; padding: 10px;}")
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        
        self.folder_edit = QLineEdit()
        self.folder_edit.setReadOnly(True)
        self.folder_edit.setStyleSheet("padding: 6px; border-radius: 3px;")
        folder_layout.addWidget(self.folder_edit, 7)
        
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self.browse_folder)
        self.browse_btn.setStyleSheet("padding: 6px 12px; background-color: #3498db; color: white; border: none; border-radius: 3px;")
        folder_layout.addWidget(self.browse_btn, 2)
        
        folder_group.setLayout(folder_layout)
        main_layout.addWidget(folder_group)
        
        # 设置区域
        settings_group = QGroupBox(f"{SYMBOL_SETTINGS} 处理设置")
        settings_group.setStyleSheet("QGroupBox {font-weight: bold; color: #34495e; border: 1px solid #bdc3c7; border-radius: 5px; margin-top: 10px; padding: 10px;}")
        settings_layout = QFormLayout()
        
        self.formats_edit = QLineEdit(", ".join(self.supported_formats))
        self.formats_edit.setToolTip("请输入要处理的图片格式，用逗号分隔")
        self.formats_edit.setStyleSheet("padding: 4px; border-radius: 3px;")
        settings_layout.addRow("图片格式:", self.formats_edit)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # 操作按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.start_btn = QPushButton(f"{SYMBOL_START} 开始处理")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("padding: 8px; background-color: #2ecc71; color: white; border: none; border-radius: 3px; font-weight: bold;")
        
        self.stop_btn = QPushButton(f"{SYMBOL_STOP} 停止处理")
        self.stop_btn.clicked.connect(self.stop_processing)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("padding: 8px; background-color: #e74c3c; color: white; border: none; border-radius: 3px; font-weight: bold;")
        
        self.help_btn = QPushButton(f"{SYMBOL_HELP} 帮助")
        self.help_btn.clicked.connect(self.show_help)
        self.help_btn.setStyleSheet("padding: 8px; background-color: #9b59b6; color: white; border: none; border-radius: 3px; font-weight: bold;")
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.help_btn)
        
        main_layout.addLayout(btn_layout)
        
        # 进度条区域
        progress_group = QGroupBox(f"{SYMBOL_PROCESS} 处理进度")
        progress_group.setStyleSheet("QGroupBox {font-weight: bold; color: #34495e; border: 1px solid #bdc3c7; border-radius: 5px; margin-top: 10px; padding: 10px;}")
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("QProgressBar {border: 1px solid #bdc3c7; border-radius: 3px; text-align: center;} QProgressBar::chunk {background-color: #3498db;}")
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel(f"{SYMBOL_INFO} 请选择文件夹并点击开始处理")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 4px;")
        progress_layout.addWidget(self.status_label)
        
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)
        
        # 日志区域
        log_group = QGroupBox(f"{SYMBOL_INFO} 处理日志")
        log_group.setStyleSheet("QGroupBox {font-weight: bold; color: #34495e; border: 1px solid #bdc3c7; border-radius: 5px; margin-top: 10px; padding: 10px;}")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #f8f9fa; border: 1px solid #bdc3c7; border-radius: 3px; padding: 5px;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, 1)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 显示窗口
        self.show()
    
    def browse_folder(self):
        """浏览并选择文件夹"""
        folder = QFileDialog.getExistingDirectory(self, "选择目标文件夹", "")
        if folder:
            self.folder_edit.setText(folder)
            self.start_btn.setEnabled(True)
            self.log_text.clear()
            self.append_log(f"{SYMBOL_FOLDER} 已选择文件夹: {folder}", "info")
            self.status_label.setText(f"{SYMBOL_INFO} 点击开始处理按钮开始移除EXIF信息")
            self.progress_bar.setValue(0)
    
    def start_processing(self):
        """开始处理图片EXIF信息"""
        folder_path = self.folder_edit.text()
        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "警告", f"{SYMBOL_WARNING} 请选择有效的文件夹")
            return
        
        # 获取图片格式设置
        formats_text = self.formats_edit.text().strip()
        if not formats_text:
            QMessageBox.warning(self, "警告", f"{SYMBOL_WARNING} 请输入图片格式")
            return
        
        file_formats = [fmt.strip().lower() for fmt in formats_text.split(",")]
        
        # 禁用开始按钮和浏览按钮，启用停止按钮
        self.start_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.formats_edit.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_text.clear()
        
        # 创建并启动处理线程
        self.thread = ExifRemoverThread(folder_path, file_formats)
        self.thread.progress_updated.connect(self.update_progress)
        self.thread.status_updated.connect(self.append_log)
        self.thread.process_complete.connect(self.process_finished)
        self.thread.start()
    
    def stop_processing(self):
        """停止处理"""
        if self.thread and self.thread.isRunning():
            reply = QMessageBox.question(self, "确认", 
                                        f"{SYMBOL_WARNING} 确定要停止处理吗?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.thread.stop()
                self.stop_btn.setEnabled(False)
                self.status_label.setText(f"{SYMBOL_STOP} 正在停止处理...")
    
    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(f"处理进度: {value}%")
    
    def append_log(self, message, msg_type):
        """添加日志信息并设置颜色"""
        self.log_text.moveCursor(QTextCursor.End)
        
        # 根据消息类型设置颜色
        if msg_type == "success":
            self.log_text.setTextColor(QColor(46, 204, 113))  # 绿色
        elif msg_type == "error":
            self.log_text.setTextColor(QColor(231, 76, 60))   # 红色
        elif msg_type == "warning":
            self.log_text.setTextColor(QColor(241, 196, 15))  # 黄色
        else:  # info
            self.log_text.setTextColor(QColor(52, 152, 219))  # 蓝色
        
        self.log_text.insertPlainText(message + "\n")
        # 恢复默认颜色
        self.log_text.setTextColor(QColor(0, 0, 0))
        # 自动滚动到底部
        self.log_text.moveCursor(QTextCursor.End)
        self.status_label.setText(message)
    
    def process_finished(self, total, success):
        """处理完成后的操作"""
        self.start_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.formats_edit.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        result_msg = f"{SYMBOL_COMPLETE} 处理完成: 共 {total} 个文件，成功处理 {success} 个"
        self.status_label.setText(result_msg)
        self.statusBar().showMessage(result_msg)
        
        QMessageBox.information(self, "处理完成", result_msg)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = f"""
        {SYMBOL_HELP} 图片EXIF信息批量移除工具使用说明
        
        1. 点击"浏览"按钮选择要处理的文件夹
        2. 可以在设置中指定要处理的图片格式（默认支持jpg, jpeg, png, gif, bmp, tiff）
        3. 点击"开始处理"按钮开始移除选中文件夹及其子文件夹中所有图片的EXIF信息
        4. 处理过程中可以点击"停止处理"按钮中断操作
        
        {SYMBOL_INFO} 注意：处理后的图片将覆盖原文件，请确保已备份重要图片
        """
        QMessageBox.information(self, "使用帮助", help_text)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.thread and self.thread.isRunning():
            reply = QMessageBox.question(self, "确认", 
                                        f"{SYMBOL_WARNING} 正在处理图片，确定要退出吗?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.thread.stop()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 设置全局字体，确保unicode符号正常显示
    font = QFont()
    font.setFamily("SimHei, WenQuanYi Micro Hei, Heiti TC, Arial Unicode MS")
    font.setPointSize(10)
    app.setFont(font)
    
    window = ExifRemoverApp()
    sys.exit(app.exec_())