import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import re
from pathlib import Path

class ImageDirectoryGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 图片文件名目录生成器")
        self.root.geometry("700x500")
        self.root.configure(bg='#2C3E50')
        
        # 设置颜色和样式
        self.colors = {
            'bg': '#2C3E50',
            'fg': '#ECF0F1',
            'accent': '#3498DB',
            'success': '#2ECC71',
            'warning': '#F39C12',
            'error': '#E74C3C'
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # 标题
        title_label = tk.Label(
            self.root, 
            text="🖼️ 图片文件名目录生成器", 
            font=("Arial", 16, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        title_label.pack(pady=15)
        
        # 文件夹选择区域
        folder_frame = tk.Frame(self.root, bg=self.colors['bg'])
        folder_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            folder_frame, 
            text="📁 选择图片文件夹:", 
            font=("Arial", 12),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(side='left')
        
        self.folder_path = tk.StringVar()
        self.folder_entry = tk.Entry(
            folder_frame, 
            textvariable=self.folder_path, 
            width=50,
            font=("Arial", 10),
            bg='#34495E',
            fg=self.colors['fg'],
            insertbackground=self.colors['fg']
        )
        self.folder_entry.pack(side='left', padx=10)
        
        browse_btn = tk.Button(
            folder_frame,
            text="🔍 浏览",
            command=self.browse_folder,
            font=("Arial", 10, "bold"),
            bg=self.colors['accent'],
            fg='white',
            relief='flat',
            padx=15
        )
        browse_btn.pack(side='left')
        
        # 选项区域
        options_frame = tk.Frame(self.root, bg=self.colors['bg'])
        options_frame.pack(fill='x', padx=20, pady=15)
        
        # 文件类型选择
        type_frame = tk.Frame(options_frame, bg=self.colors['bg'])
        type_frame.pack(anchor='w', pady=5)
        
        tk.Label(
            type_frame, 
            text="📄 文件类型:", 
            font=("Arial", 11),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(side='left')
        
        self.file_types = {
            "🖼️ 所有图片": ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            "📷 JPEG格式": ['.jpg', '.jpeg'],
            "🖌️ PNG格式": ['.png'],
            "🎨 其他格式": ['.gif', '.bmp', '.tiff', '.webp']
        }
        
        self.selected_type = tk.StringVar(value="🖼️ 所有图片")
        for file_type in self.file_types.keys():
            tk.Radiobutton(
                type_frame,
                text=file_type,
                variable=self.selected_type,
                value=file_type,
                bg=self.colors['bg'],
                fg=self.colors['fg'],
                selectcolor=self.colors['accent'],
                font=("Arial", 10)
            ).pack(side='left', padx=10)
        
        # 排序选项
        sort_frame = tk.Frame(options_frame, bg=self.colors['bg'])
        sort_frame.pack(anchor='w', pady=5)
        
        tk.Label(
            sort_frame, 
            text="🔢 排序方式:", 
            font=("Arial", 11),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(side='left')
        
        self.sort_method = tk.StringVar(value="🔤 按文件名")
        sort_methods = ["🔤 按文件名", "🔢 按数字序号"]
        for method in sort_methods:
            tk.Radiobutton(
                sort_frame,
                text=method,
                variable=self.sort_method,
                value=method,
                bg=self.colors['bg'],
                fg=self.colors['fg'],
                selectcolor=self.colors['accent'],
                font=("Arial", 10)
            ).pack(side='left', padx=10)
        
        # 操作按钮区域
        button_frame = tk.Frame(self.root, bg=self.colors['bg'])
        button_frame.pack(pady=15)
        
        generate_btn = tk.Button(
            button_frame,
            text="🚀 生成目录",
            command=self.generate_directory,
            font=("Arial", 12, "bold"),
            bg=self.colors['success'],
            fg='white',
            relief='flat',
            padx=20,
            pady=8
        )
        generate_btn.pack(side='left', padx=10)
        
        clear_btn = tk.Button(
            button_frame,
            text="🗑️ 清空结果",
            command=self.clear_results,
            font=("Arial", 12, "bold"),
            bg=self.colors['warning'],
            fg='white',
            relief='flat',
            padx=20,
            pady=8
        )
        clear_btn.pack(side='left', padx=10)
        
        # 结果显示区域
        result_frame = tk.Frame(self.root, bg=self.colors['bg'])
        result_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(
            result_frame, 
            text="📋 生成的目录:", 
            font=("Arial", 12, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['fg']
        ).pack(anchor='w')
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            width=80,
            height=15,
            font=("Arial", 11),
            bg='#1C2833',
            fg='#EAECEE',
            insertbackground='white'
        )
        self.result_text.pack(fill='both', expand=True, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="🟢 就绪 - 选择文件夹开始生成目录")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w',
            font=("Arial", 9),
            bg='#34495E',
            fg=self.colors['fg']
        )
        status_bar.pack(fill='x', side='bottom', ipady=3)
    
    def browse_folder(self):
        """浏览文件夹"""
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
            self.status_var.set(f"📁 已选择文件夹: {folder_selected}")
    
    def extract_number(self, filename):
        """从文件名中提取数字用于排序"""
        numbers = re.findall(r'\d+', filename)
        return int(numbers[0]) if numbers else float('inf')
    
    def get_image_files(self, folder_path):
        """获取指定文件夹中的所有图片文件"""
        if not folder_path or not os.path.exists(folder_path):
            return []
        
        selected_extensions = self.file_types[self.selected_type.get()]
        image_files = []
        
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if os.path.isfile(file_path):
                ext = Path(file).suffix.lower()
                if ext in selected_extensions:
                    image_files.append(file)
        
        return image_files
    
    def sort_files(self, files):
        """根据选择的排序方式对文件进行排序"""
        sort_method = self.sort_method.get()
        
        if sort_method == "🔢 按数字序号":
            return sorted(files, key=self.extract_number)
        else:  # 按文件名
            return sorted(files)
    
    def generate_directory(self):
        """生成目录"""
        folder_path = self.folder_path.get()
        
        if not folder_path:
            messagebox.showwarning("⚠️ 警告", "请先选择图片文件夹！")
            return
        
        if not os.path.exists(folder_path):
            messagebox.showerror("❌ 错误", "选择的文件夹不存在！")
            return
        
        try:
            self.status_var.set("⏳ 正在扫描图片文件...")
            self.root.update()
            
            # 获取图片文件
            image_files = self.get_image_files(folder_path)
            
            if not image_files:
                messagebox.showinfo("ℹ️ 信息", "在指定文件夹中未找到图片文件！")
                self.status_var.set("🟡 未找到图片文件")
                return
            
            # 排序文件
            sorted_files = self.sort_files(image_files)
            
            # 生成目录内容
            self.status_var.set("📝 正在生成目录...")
            self.root.update()
            
            directory_content = self.create_directory_content(sorted_files)
            
            # 显示结果
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, directory_content)
            
            # 保存到文件
            self.save_to_file(directory_content, folder_path)
            
            self.status_var.set(f"✅ 完成！共处理 {len(sorted_files)} 个文件")
            messagebox.showinfo("✅ 完成", f"成功生成目录！\n共处理 {len(sorted_files)} 个文件")
            
        except Exception as e:
            self.status_var.set("❌ 生成目录时出错")
            messagebox.showerror("❌ 错误", f"生成目录时出错：{str(e)}")
    
    def create_directory_content(self, files):
        """创建目录内容 - 只包含文件名（不带扩展名）"""
        content = ""
        
        for filename in files:
            # 去掉文件扩展名
            name_without_extension = Path(filename).stem
            content += f"{name_without_extension}\n"
        
        return content
    
    def save_to_file(self, content, folder_path):
        """将目录内容保存到文件"""
        try:
            filename = f"图片文件名目录_{os.path.basename(folder_path)}_{self.get_timestamp()}.txt"
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.status_var.set(f"💾 目录已保存到: {filename}")
            
        except Exception as e:
            messagebox.showwarning("⚠️ 警告", f"保存文件时出错：{str(e)}")
    
    def clear_results(self):
        """清空结果"""
        self.result_text.delete(1.0, tk.END)
        self.status_var.set("🟢 就绪 - 选择文件夹开始生成目录")
    
    def get_timestamp(self):
        """获取时间戳用于文件名"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

def main():
    root = tk.Tk()
    app = ImageDirectoryGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()