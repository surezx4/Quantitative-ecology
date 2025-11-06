import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import os
from PIL import Image, ImageTk
import threading
import math
import shapefile
import tempfile
from io import BytesIO
import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.crs import CRS
import json
import time

class OpenCycleMapDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("OpenCycleMap高级下载器 - 支持SHP边界和TIFF拼接")
        self.root.geometry("750x700")
        
        # 存储边界坐标
        self.boundary_coords = []
        self.downloaded_tiles = []
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建GUI界面组件"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="下载参数", padding="5")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 边界文件导入
        ttk.Label(input_frame, text="边界文件:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.boundary_file = ttk.Entry(input_frame, width=30)
        self.boundary_file.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        ttk.Button(input_frame, text="导入SHP", command=self.import_shp).grid(row=0, column=2, padx=2)
        ttk.Button(input_frame, text="清除边界", command=self.clear_boundary).grid(row=0, column=3, padx=2)
        
        # 经纬度范围
        coords_frame = ttk.Frame(input_frame)
        coords_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(coords_frame, text="左下角经度:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.min_lon = ttk.Entry(coords_frame, width=15)
        self.min_lon.insert(0, "116.0")
        self.min_lon.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(0, 10))
        
        ttk.Label(coords_frame, text="左下角纬度:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.min_lat = ttk.Entry(coords_frame, width=15)
        self.min_lat.insert(0, "39.5")
        self.min_lat.grid(row=0, column=3, sticky=tk.W, pady=2, padx=(0, 10))
        
        ttk.Label(coords_frame, text="右上角经度:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.max_lon = ttk.Entry(coords_frame, width=15)
        self.max_lon.insert(0, "117.0")
        self.max_lon.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(0, 10))
        
        ttk.Label(coords_frame, text="右上角纬度:").grid(row=1, column=2, sticky=tk.W, pady=2)
        self.max_lat = ttk.Entry(coords_frame, width=15)
        self.max_lat.insert(0, "40.5")
        self.max_lat.grid(row=1, column=3, sticky=tk.W, pady=2, padx=(0, 10))
        
        # 下载参数
        params_frame = ttk.Frame(input_frame)
        params_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(params_frame, text="缩放级别 (1-18):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.zoom = ttk.Combobox(params_frame, values=[str(i) for i in range(1, 19)], width=13)
        self.zoom.set("14")
        self.zoom.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(0, 20))
        
        ttk.Label(params_frame, text="下载模式:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.download_mode = ttk.Combobox(params_frame, 
                                         values=["矩形范围", "边界范围(精确)", "边界范围(外接矩形)"], 
                                         width=18)
        self.download_mode.set("矩形范围")
        self.download_mode.grid(row=0, column=3, sticky=tk.W, pady=2, padx=(0, 20))
        
        ttk.Label(params_frame, text="输出格式:").grid(row=0, column=4, sticky=tk.W, pady=2)
        self.output_format = ttk.Combobox(params_frame, 
                                         values=["单独瓦片", "拼接TIFF(地理参考)", "拼接TIFF(Web墨卡托)"], 
                                         width=18)
        self.output_format.set("拼接TIFF(地理参考)")
        self.output_format.grid(row=0, column=5, sticky=tk.W, pady=2)
        
        # 保存路径
        ttk.Label(input_frame, text="保存路径:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.save_path = ttk.Entry(input_frame, width=30)
        self.save_path.insert(0, "./opencyclemap_output")
        self.save_path.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        ttk.Button(input_frame, text="浏览", command=self.browse_path).grid(row=3, column=3, pady=2)
        
        # 控制按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        self.download_btn = ttk.Button(button_frame, text="开始下载", command=self.start_download)
        self.download_btn.grid(row=0, column=0, padx=5)
        
        self.preview_btn = ttk.Button(button_frame, text="预览区域", command=self.preview_area)
        self.preview_btn.grid(row=0, column=1, padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 状态标签
        self.status = ttk.Label(main_frame, text="准备就绪")
        self.status.grid(row=3, column=0, columnspan=2)
        
        # 边界信息显示
        self.boundary_info = ttk.Label(main_frame, text="未导入边界文件", foreground="blue")
        self.boundary_info.grid(row=4, column=0, columnspan=2, pady=2)
        
        # 日志文本框
        log_frame = ttk.LabelFrame(main_frame, text="下载日志", padding="5")
        log_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.log_text = tk.Text(log_frame, height=15, width=70)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        input_frame.columnconfigure(1, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def import_shp(self):
        """导入SHP边界文件"""
        file_path = filedialog.askopenfilename(
            title="选择SHP边界文件",
            filetypes=[("SHP文件", "*.shp"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            # 读取SHP文件
            sf = shapefile.Reader(file_path)
            shapes = sf.shapes()
            
            if not shapes:
                messagebox.showerror("错误", "SHP文件中没有找到任何图形")
                return
                
            # 提取所有坐标点
            self.boundary_coords = []
            for shape in shapes:
                points = shape.points
                self.boundary_coords.extend(points)
            
            # 计算边界范围
            lons = [point[0] for point in self.boundary_coords]
            lats = [point[1] for point in self.boundary_coords]
            
            min_lon, max_lon = min(lons), max(lons)
            min_lat, max_lat = min(lats), max(lats)
            
            # 更新输入框
            self.min_lon.delete(0, tk.END)
            self.min_lon.insert(0, f"{min_lon:.6f}")
            self.min_lat.delete(0, tk.END)
            self.min_lat.insert(0, f"{min_lat:.6f}")
            self.max_lon.delete(0, tk.END)
            self.max_lon.insert(0, f"{max_lon:.6f}")
            self.max_lat.delete(0, tk.END)
            self.max_lat.insert(0, f"{max_lat:.6f}")
            
            # 更新边界文件路径
            self.boundary_file.delete(0, tk.END)
            self.boundary_file.insert(0, file_path)
            
            # 显示边界信息
            self.boundary_info.config(
                text=f"已导入边界: {len(self.boundary_coords)}个点, 范围: {min_lon:.4f},{min_lat:.4f} ~ {max_lon:.4f},{max_lat:.4f}"
            )
            
            self.log_message(f"成功导入SHP边界文件: {os.path.basename(file_path)}")
            self.log_message(f"边界范围: 经度 {min_lon:.4f}-{max_lon:.4f}, 纬度 {min_lat:.4f}-{max_lat:.4f}")
            
        except Exception as e:
            messagebox.showerror("错误", f"读取SHP文件失败: {str(e)}")
            self.log_message(f"导入SHP文件错误: {str(e)}")
    
    def clear_boundary(self):
        """清除边界数据"""
        self.boundary_coords = []
        self.boundary_file.delete(0, tk.END)
        self.boundary_info.config(text="未导入边界文件")
        self.log_message("已清除边界数据")
    
    def browse_path(self):
        """选择保存路径"""
        path = filedialog.askdirectory()
        if path:
            self.save_path.delete(0, tk.END)
            self.save_path.insert(0, path)
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def lonlat_to_tile(self, lon, lat, zoom):
        """将经纬度转换为瓦片坐标"""
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n)
        return xtile, ytile
    
    def tile_to_lonlat(self, x, y, zoom):
        """将瓦片坐标转换为经纬度"""
        n = 2.0 ** zoom
        lon_deg = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_deg = math.degrees(lat_rad)
        return lon_deg, lat_deg
    
    def tile_to_web_mercator(self, x, y, zoom):
        """将瓦片坐标转换为Web墨卡托坐标"""
        # 瓦片边界经纬度
        lon_left, lat_top = self.tile_to_lonlat(x, y, zoom)
        lon_right, lat_bottom = self.tile_to_lonlat(x + 1, y + 1, zoom)
        
        # 转换为Web墨卡托
        x_min, y_min = self.lonlat_to_web_mercator(lon_left, lat_bottom)
        x_max, y_max = self.lonlat_to_web_mercator(lon_right, lat_top)
        
        return x_min, y_min, x_max, y_max
    
    def lonlat_to_web_mercator(self, lon, lat):
        """将经纬度转换为Web墨卡托坐标"""
        # 地球半径
        earth_radius = 6378137.0
        
        x = earth_radius * math.radians(lon)
        y = earth_radius * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
        
        return x, y
    
    def point_in_polygon(self, x, y, polygon):
        """判断点是否在多边形内（射线法）"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
            
        return inside
    
    def download_tile(self, x, y, z, folder_path):
        """下载单个瓦片"""
        # 尝试多个可能的瓦片服务器
        tile_servers = [
            f"http://tile.opencyclemap.org/cycle/{z}/{x}/{y}.png",
            f"https://tile.opencyclemap.org/cycle/{z}/{x}/{y}.png",
            f"http://a.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png",
            f"http://b.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png",
            f"http://c.tile.opencyclemap.org/cycle/{z}/{x}/{y}.png",
        ]
        
        for url in tile_servers:
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    # 保存瓦片文件
                    filename = os.path.join(folder_path, f"tile_{z}_{x}_{y}.png")
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    # 记录瓦片信息
                    tile_info = {
                        'x': x, 'y': y, 'z': z,
                        'filename': filename,
                        'bounds': self.tile_to_web_mercator(x, y, z)
                    }
                    self.downloaded_tiles.append(tile_info)
                    
                    return True
            except Exception as e:
                continue  # 尝试下一个服务器
        
        self.log_message(f"下载失败: 瓦片 {z}/{x}/{y}")
        return False
    
    def preview_area(self):
        """预览下载区域"""
        try:
            min_lon = float(self.min_lon.get())
            min_lat = float(self.min_lat.get())
            max_lon = float(self.max_lon.get())
            max_lat = float(self.max_lat.get())
            zoom = int(self.zoom.get())
            
            # 计算瓦片范围
            x_min, y_max = self.lonlat_to_tile(min_lon, min_lat, zoom)
            x_max, y_min = self.lonlat_to_tile(max_lon, max_lat, zoom)
            
            total_tiles = (x_max - x_min + 1) * (y_max - y_min + 1)
            
            # 如果有边界且选择精确模式，估算实际瓦片数
            if self.boundary_coords and self.download_mode.get() == "边界范围(精确)":
                # 简单估算：假设一半的瓦片在边界内
                estimated_tiles = total_tiles // 2
                tile_info = f"瓦片数量: {total_tiles} (估算边界内: {estimated_tiles})"
            else:
                tile_info = f"瓦片数量: {total_tiles}"
            
            messagebox.showinfo("区域预览", 
                              f"下载范围:\n"
                              f"经度: {min_lon:.4f} ~ {max_lon:.4f}\n"
                              f"纬度: {min_lat:.4f} ~ {max_lat:.4f}\n"
                              f"缩放级别: {zoom}\n"
                              f"{tile_info}\n"
                              f"X范围: {x_min} ~ {x_max}\n"
                              f"Y范围: {y_min} ~ {y_max}")
        except ValueError as e:
            messagebox.showerror("输入错误", "请输入有效的数值参数")
    
    def create_geotiff_wgs84(self, output_path, min_lon, min_lat, max_lon, max_lat):
        """创建WGS84地理参考的TIFF文件"""
        try:
            self.log_message("开始拼接TIFF文件(WGS84)...")
            
            # 计算输出图像尺寸（保持比例）
            zoom = int(self.zoom.get())
            x_min, y_max = self.lonlat_to_tile(min_lon, max_lat, zoom)
            x_max, y_min = self.lonlat_to_tile(max_lon, min_lat, zoom)
            
            # 计算每个瓦片的像素尺寸
            tile_width, tile_height = 256, 256
            
            # 计算整体图像尺寸
            total_width = (x_max - x_min + 1) * tile_width
            total_height = (y_max - y_min + 1) * tile_height
            
            # 创建空白图像
            merged_image = Image.new('RGB', (total_width, total_height))
            
            # 拼接所有瓦片
            for tile_info in self.downloaded_tiles:
                x, y, z = tile_info['x'], tile_info['y'], tile_info['z']
                
                # 计算瓦片在整体图像中的位置
                img_x = (x - x_min) * tile_width
                img_y = (y - y_min) * tile_height
                
                try:
                    tile_img = Image.open(tile_info['filename'])
                    merged_image.paste(tile_img, (img_x, img_y))
                except Exception as e:
                    self.log_message(f"处理瓦片 {z}/{x}/{y} 时出错: {str(e)}")
                    continue
            
            # 保存为TIFF并添加地理参考
            self.log_message("添加地理参考信息...")
            
            # 计算地理变换参数
            transform = from_bounds(min_lon, min_lat, max_lon, max_lat, total_width, total_height)
            
            # 转换为numpy数组
            img_array = np.array(merged_image)
            
            # 创建GeoTIFF文件
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=total_height,
                width=total_width,
                count=3,  # RGB
                dtype=img_array.dtype,
                crs=CRS.from_epsg(4326),  # WGS84
                transform=transform,
                compress='lzw'  # 压缩以减小文件大小
            ) as dst:
                # 写入RGB通道
                for i in range(3):
                    dst.write(img_array[:, :, i], i + 1)
            
            self.log_message(f"TIFF文件已保存: {output_path}")
            return True
            
        except Exception as e:
            self.log_message(f"创建TIFF文件失败: {str(e)}")
            return False
    
    def create_geotiff_web_mercator(self, output_path):
        """创建Web墨卡托投影的TIFF文件"""
        try:
            self.log_message("开始拼接TIFF文件(Web墨卡托)...")
            
            if not self.downloaded_tiles:
                self.log_message("没有可用的瓦片数据")
                return False
            
            # 计算整体边界（Web墨卡托坐标）
            x_min = min(tile['bounds'][0] for tile in self.downloaded_tiles)
            y_min = min(tile['bounds'][1] for tile in self.downloaded_tiles)
            x_max = max(tile['bounds'][2] for tile in self.downloaded_tiles)
            y_max = max(tile['bounds'][3] for tile in self.downloaded_tiles)
            
            # 计算每个瓦片的像素尺寸
            tile_width, tile_height = 256, 256
            
            # 计算整体图像尺寸（基于瓦片数量）
            zoom = self.downloaded_tiles[0]['z']
            tile_x_min = min(tile['x'] for tile in self.downloaded_tiles)
            tile_x_max = max(tile['x'] for tile in self.downloaded_tiles)
            tile_y_min = min(tile['y'] for tile in self.downloaded_tiles)
            tile_y_max = max(tile['y'] for tile in self.downloaded_tiles)
            
            total_width = (tile_x_max - tile_x_min + 1) * tile_width
            total_height = (tile_y_max - tile_y_min + 1) * tile_height
            
            # 创建空白图像
            merged_image = Image.new('RGB', (total_width, total_height))
            
            # 拼接所有瓦片
            for tile_info in self.downloaded_tiles:
                x, y, z = tile_info['x'], tile_info['y'], tile_info['z']
                
                # 计算瓦片在整体图像中的位置
                img_x = (x - tile_x_min) * tile_width
                img_y = (y - tile_y_min) * tile_height
                
                try:
                    tile_img = Image.open(tile_info['filename'])
                    merged_image.paste(tile_img, (img_x, img_y))
                except Exception as e:
                    self.log_message(f"处理瓦片 {z}/{x}/{y} 时出错: {str(e)}")
                    continue
            
            # 保存为TIFF并添加地理参考
            self.log_message("添加Web墨卡托投影信息...")
            
            # 计算地理变换参数
            transform = from_bounds(x_min, y_min, x_max, y_max, total_width, total_height)
            
            # 转换为numpy数组
            img_array = np.array(merged_image)
            
            # 创建GeoTIFF文件
            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=total_height,
                width=total_width,
                count=3,  # RGB
                dtype=img_array.dtype,
                crs=CRS.from_epsg(3857),  # Web墨卡托
                transform=transform,
                compress='lzw'  # 压缩以减小文件大小
            ) as dst:
                # 写入RGB通道
                for i in range(3):
                    dst.write(img_array[:, :, i], i + 1)
            
            self.log_message(f"TIFF文件已保存: {output_path}")
            return True
            
        except Exception as e:
            self.log_message(f"创建TIFF文件失败: {str(e)}")
            return False
    
    def start_download(self):
        """开始下载线程"""
        thread = threading.Thread(target=self.download_process)
        thread.daemon = True
        thread.start()
    
    def download_process(self):
        """下载流程主逻辑"""
        try:
            # 重置下载的瓦片列表
            self.downloaded_tiles = []
            
            # 获取参数
            min_lon = float(self.min_lon.get())
            min_lat = float(self.min_lat.get())
            max_lon = float(self.max_lon.get())
            max_lat = float(self.max_lat.get())
            zoom = int(self.zoom.get())
            save_path = self.save_path.get()
            download_mode = self.download_mode.get()
            output_format = self.output_format.get()
            
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            
            # 创建瓦片保存目录
            tiles_dir = os.path.join(save_path, "tiles")
            if not os.path.exists(tiles_dir):
                os.makedirs(tiles_dir)
            
            # 计算瓦片范围
            x_min, y_max = self.lonlat_to_tile(min_lon, min_lat, zoom)
            x_max, y_min = self.lonlat_to_tile(max_lon, max_lat, zoom)
            
            # 根据下载模式确定需要下载的瓦片
            tiles_to_download = []
            
            if download_mode == "矩形范围" or not self.boundary_coords:
                # 矩形范围内所有瓦片
                for x in range(x_min, x_max + 1):
                    for y in range(y_min, y_max + 1):
                        tiles_to_download.append((x, y, zoom))
            elif download_mode == "边界范围(外接矩形)":
                # 外接矩形内所有瓦片（与矩形范围相同）
                for x in range(x_min, x_max + 1):
                    for y in range(y_min, y_max + 1):
                        tiles_to_download.append((x, y, zoom))
            elif download_mode == "边界范围(精确)" and self.boundary_coords:
                # 精确模式：只下载边界内的瓦片
                self.log_message("计算边界内瓦片...")
                for x in range(x_min, x_max + 1):
                    for y in range(y_min, y_max + 1):
                        # 检查瓦片中心点是否在边界内
                        tile_center_lon, tile_center_lat = self.tile_to_lonlat(x + 0.5, y + 0.5, zoom)
                        if self.point_in_polygon(tile_center_lon, tile_center_lat, self.boundary_coords):
                            tiles_to_download.append((x, y, zoom))
            
            total_tiles = len(tiles_to_download)
            completed = 0
            
            self.log_message(f"开始下载，模式: {download_mode}, 总共 {total_tiles} 个瓦片")
            self.progress["maximum"] = total_tiles
            self.progress["value"] = 0
            
            self.download_btn["state"] = "disabled"
            
            # 下载所有选定瓦片
            for x, y, z in tiles_to_download:
                if self.download_tile(x, y, z, tiles_dir):
                    completed += 1
                    self.progress["value"] = completed
                    self.status["text"] = f"进度: {completed}/{total_tiles}"
                
                # 添加小延迟，避免请求过于频繁
                time.sleep(0.1)
            
            self.log_message(f"瓦片下载完成！成功下载 {completed} 个瓦片")
            
            # 根据输出格式处理数据
            if output_format == "拼接TIFF(地理参考)":
                tiff_path = os.path.join(save_path, "opencyclemap_wgs84.tif")
                if self.create_geotiff_wgs84(tiff_path, min_lon, min_lat, max_lon, max_lat):
                    self.log_message("WGS84地理参考TIFF创建成功")
                else:
                    self.log_message("WGS84地理参考TIFF创建失败")
                    
            elif output_format == "拼接TIFF(Web墨卡托)":
                tiff_path = os.path.join(save_path, "opencyclemap_webmercator.tif")
                if self.create_geotiff_web_mercator(tiff_path):
                    self.log_message("Web墨卡托投影TIFF创建成功")
                else:
                    self.log_message("Web墨卡托投影TIFF创建失败")
            
            # 保存元数据
            metadata = {
                "download_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "bounds": {
                    "min_lon": min_lon,
                    "min_lat": min_lat,
                    "max_lon": max_lon,
                    "max_lat": max_lat
                },
                "zoom_level": zoom,
                "total_tiles": completed,
                "coordinate_system": "WGS84" if output_format == "拼接TIFF(地理参考)" else "Web Mercator"
            }
            
            with open(os.path.join(save_path, "metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.log_message("元数据文件已保存")
            self.log_message(f"所有处理完成！文件保存在: {save_path}")
            messagebox.showinfo("完成", f"处理完成！成功下载 {completed} 个瓦片\n文件保存在: {save_path}")
            
        except ValueError as e:
            messagebox.showerror("输入错误", "请输入有效的数值参数")
        except Exception as e:
            self.log_message(f"下载过程出错: {str(e)}")
            messagebox.showerror("错误", f"下载过程出错: {str(e)}")
        finally:
            self.download_btn["state"] = "normal"
            self.status["text"] = "准备就绪"

def check_dependencies():
    """检查依赖库是否安装"""
    missing_deps = []
    try:
        import shapefile
    except ImportError:
        missing_deps.append("pyshp")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("Pillow")
    
    try:
        import numpy
    except ImportError:
        missing_deps.append("numpy")
    
    try:
        import rasterio
    except ImportError:
        missing_deps.append("rasterio")
    
    return missing_deps

def install_dependencies(missing_deps):
    """安装缺失的依赖库"""
    import subprocess
    import sys
    
    for dep in missing_deps:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"成功安装 {dep}")
        except subprocess.CalledProcessError:
            print(f"安装 {dep} 失败")
            return False
    return True

def main():
    # 检查依赖
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"缺少依赖库: {', '.join(missing_deps)}")
        response = input("是否自动安装缺失的依赖库？(y/n): ")
        if response.lower() == 'y':
            if not install_dependencies(missing_deps):
                print("依赖库安装失败，请手动安装后重新运行程序")
                return
        else:
            print("请手动安装缺失的依赖库后重新运行程序")
            return
    
    root = tk.Tk()
    app = OpenCycleMapDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()