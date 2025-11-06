import sys
import xml.etree.ElementTree as ET
import asyncio
import pandas as pd
from itertools import chain
from aiohttp import ClientSession, TCPConnector
import chardet
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar, 
                             QFileDialog, QGroupBox, QComboBox, QMessageBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from PyQt5.QtCore import QSize
import qdarkstyle
import csv

URL = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'

class AsyncWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(pd.DataFrame)
    error = pyqtSignal(str)

    def __init__(self, query_list, api_key, step=10):
        super().__init__()
        self.query_list = query_list
        self.api_key = api_key
        self.step = step

    async def async_query_batch(self):
        async def _esearch_(_common, _session):
            url = URL + 'esearch.fcgi?db=taxonomy&term=' + _common + '&api_key=' + self.api_key
            async with _session.get(url) as response:
                _esearch_result = ET.fromstring(await response.text(encoding='UTF-8'))
                _id_list = [__.text for _ in _esearch_result if _.tag == 'IdList' for __ in _]
                return _id_list

        async def _esummary_(_id_list, _session):
            url = URL + 'esummary.fcgi?db=taxonomy&id=' + ','.join(_id_list) + '&api_key=' + self.api_key
            async with _session.get(url) as response:
                _esummary_result = ET.fromstring(await response.text(encoding='UTF-8'))
                _tmp_list = []
                for _item in _esummary_result:
                    _tmp_dict = {_.attrib.get('Name'): _.text for _ in _item}
                    _tmp_list.append({'common': _tmp_dict.get('CommonName'), 'scientific': _tmp_dict.get('ScientificName')})
                return _tmp_list

        async def wrapper(_query, _func, _session, recur=0):
            recur += 1
            if recur > 3:
                self.progress.emit(f"❌ {_query} 在3次尝试后失败")
                return []
            try:
                return await _func(_query, _session)
            except Exception as e:
                self.progress.emit(f"⚠️ 重试 {_query}: {str(e)}")
                return await wrapper(_query, _func, _session, recur)

        async with ClientSession(connector=TCPConnector(limit=10)) as session:
            esearch_results = []
            esummary_results = []
            
            self.progress.emit("🔍 开始esearch搜索...")
            batch_list = [self.query_list[i:i + self.step] for i in range(0, len(self.query_list), self.step)]
            
            for i, per_batch in enumerate(batch_list):
                self.progress.emit(f"📦 处理批次 {i+1}/{len(batch_list)}")
                tmp = await asyncio.gather(*[asyncio.create_task(wrapper(per_query, _esearch_, session)) for per_query in per_batch])
                esearch_results += chain(*tmp)
                await asyncio.sleep(1)
            
            esearch_results = [_ for _ in esearch_results if not _ == []]
            self.progress.emit(f"✅ esearch完成，找到 {len(esearch_results)} 个结果")
            
            if not esearch_results:
                self.progress.emit("❌ esearch未找到任何结果")
                return pd.DataFrame()

            self.progress.emit("📋 开始esummary搜索...")
            _step = max(1, int(len(esearch_results) / 10))
            batch_list = [esearch_results[i:i + _step] for i in range(0, len(esearch_results), _step)]
            
            tmp = await asyncio.gather(*[asyncio.create_task(wrapper(per_query, _esummary_, session)) for per_query in batch_list])
            esummary_results += chain(*tmp)
            await asyncio.sleep(1)
            
            self.progress.emit(f"✅ esummary完成，检索到 {len(esummary_results)} 条记录")
            return pd.DataFrame(esummary_results)

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.async_query_batch())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class NCBIQueryGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('NCBI分类学查询工具 🧬')
        self.setGeometry(100, 100, 900, 700)
        
        # 设置蓝色调色板
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(240, 248, 255))  # AliceBlue
        palette.setColor(QPalette.WindowText, QColor(25, 25, 112))  # MidnightBlue
        palette.setColor(QPalette.Base, QColor(230, 240, 255))
        palette.setColor(QPalette.AlternateBase, QColor(208, 228, 255))
        palette.setColor(QPalette.Button, QColor(70, 130, 180))  # SteelBlue
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.Highlight, QColor(65, 105, 225))  # RoyalBlue
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel('NCBI分类学查询工具 🧬')
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 10px; background-color: #4169E1; color: white; border-radius: 5px;")
        layout.addWidget(title)
        
        # API密钥部分
        api_group = QGroupBox("🔑 API密钥配置")
        api_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        api_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("输入您的NCBI API密钥（可选但推荐）")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addWidget(self.api_key_input)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # 文件选择部分
        file_group = QGroupBox("📁 文件操作")
        file_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        file_layout = QVBoxLayout()
        
        # 输入文件选择
        input_layout = QHBoxLayout()
        self.input_file = QLineEdit()
        self.input_file.setPlaceholderText("选择输入CSV文件...")
        input_btn = QPushButton("浏览...")
        input_btn.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_file)
        input_layout.addWidget(input_btn)
        file_layout.addLayout(input_layout)
        
        # 列选择
        column_layout = QHBoxLayout()
        column_layout.addWidget(QLabel("选择包含查询词的列:"))
        self.column_combo = QComboBox()
        column_layout.addWidget(self.column_combo)
        file_layout.addLayout(column_layout)
        
        # 输出文件选择
        output_layout = QHBoxLayout()
        self.output_file = QLineEdit()
        self.output_file.setPlaceholderText("选择输出CSV文件...")
        output_btn = QPushButton("浏览...")
        output_btn.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.output_file)
        output_layout.addWidget(output_btn)
        file_layout.addLayout(output_layout)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 按钮
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("🚀 开始查询")
        self.start_btn.clicked.connect(self.start_query)
        self.start_btn.setEnabled(False)
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.clicked.connect(self.cancel_query)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        # 状态输出
        status_group = QGroupBox("📊 状态信息")
        status_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        status_layout = QVBoxLayout()
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        status_layout.addWidget(self.status_output)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # 结果预览
        results_group = QGroupBox("👁️ 结果预览")
        results_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        results_layout = QVBoxLayout()
        self.results_preview = QTextEdit()
        self.results_preview.setReadOnly(True)
        results_layout.addWidget(self.results_preview)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # 初始化工作线程
        self.worker = None
        
        # 当文件被选择时启用开始按钮
        self.input_file.textChanged.connect(self.check_inputs)
        self.output_file.textChanged.connect(self.check_inputs)
        
    def check_inputs(self):
        if self.input_file.text() and self.output_file.text():
            self.start_btn.setEnabled(True)
        else:
            self.start_btn.setEnabled(False)
    
    def select_input_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择输入CSV文件", "", "CSV文件 (*.csv);;所有文件 (*)"
        )
        if file_path:
            self.input_file.setText(file_path)
            self.detect_csv_columns(file_path)
    
    def detect_csv_columns(self, file_path):
        try:
            # 检测文件编码
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            # 使用检测到的编码读取CSV
            df = pd.read_csv(file_path, encoding=encoding, nrows=5)
            
            # 更新列选择下拉框
            self.column_combo.clear()
            self.column_combo.addItems(df.columns.tolist())
            
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法读取CSV文件: {str(e)}")
    
    def select_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出CSV文件", "", "CSV文件 (*.csv);;所有文件 (*)"
        )
        if file_path:
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            self.output_file.setText(file_path)
    
    def start_query(self):
        # 获取API密钥
        api_key = self.api_key_input.text().strip() or "demo_key"
        
        # 获取输入文件和列
        input_file = self.input_file.text()
        output_file = self.output_file.text()
        column_name = self.column_combo.currentText()
        
        try:
            # 通过编码检测读取输入CSV
            with open(input_file, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            
            df = pd.read_csv(input_file, encoding=encoding)
            query_list = df[column_name].dropna().astype(str).tolist()
            
            if not query_list:
                QMessageBox.warning(self, "错误", "在选定的列中未找到有效的查询词。")
                return
            
            self.status_output.append(f"📖 从'{column_name}'列加载了 {len(query_list)} 个查询词")
            
            # 在处理过程中禁用UI元素
            self.start_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 不确定进度
            
            # 启动工作线程
            self.worker = AsyncWorker(query_list, api_key)
            self.worker.progress.connect(self.update_status)
            self.worker.finished.connect(self.query_finished)
            self.worker.error.connect(self.query_error)
            self.worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"处理输入文件失败: {str(e)}")
    
    def cancel_query(self):
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            self.status_output.append("❌ 查询已被用户取消")
            self.reset_ui()
    
    def update_status(self, message):
        self.status_output.append(message)
    
    def query_finished(self, result_df):
        if result_df is None or result_df.empty:
            self.status_output.append("❌ 未从NCBI获取到任何结果")
            self.reset_ui()
            return
        
        # 将结果保存到CSV
        output_file = self.output_file.text()
        try:
            result_df.to_csv(output_file, index=False, encoding='utf-8')
            self.status_output.append(f"💾 结果已保存至: {output_file}")
            
            # 显示预览
            preview_text = result_df.head(10).to_string(index=False)
            self.results_preview.setPlainText(f"前10条结果:\n\n{preview_text}")
            
            # 显示成功消息
            QMessageBox.information(self, "成功", 
                                  f"查询成功完成！\n\n"
                                  f"检索到 {len(result_df)} 条结果。\n"
                                  f"已保存至: {output_file}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存结果失败: {str(e)}")
        
        self.reset_ui()
    
    def query_error(self, error_message):
        QMessageBox.critical(self, "错误", f"查询过程中发生错误: {error_message}")
        self.status_output.append(f"❌ 错误: {error_message}")
        self.reset_ui()
    
    def reset_ui(self):
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

def main():
    app = QApplication(sys.argv)
    
    # 应用蓝色主题样式表
    blue_style = """
        QMainWindow, QWidget {
            background-color: #f0f8ff;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #4682b4;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
        QPushButton {
            background-color: #4682b4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #5a9bd4;
        }
        QPushButton:disabled {
            background-color: #b0c4de;
        }
        QLineEdit, QComboBox {
            padding: 6px;
            border: 1px solid #a9a9a9;
            border-radius: 4px;
            background-color: white;
        }
        QTextEdit {
            border: 1px solid #a9a9a9;
            border-radius: 4px;
            background-color: white;
        }
        QProgressBar {
            border: 1px solid #a9a9a9;
            border-radius: 4px;
            text-align: center;
            background-color: white;
        }
        QProgressBar::chunk {
            background-color: #4682b4;
            width: 10px;
        }
    """
    app.setStyleSheet(blue_style)
    
    window = NCBIQueryGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()