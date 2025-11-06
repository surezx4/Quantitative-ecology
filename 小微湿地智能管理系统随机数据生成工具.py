# -*- coding: utf-8 -*-
"""
Created on Fri Aug 22 18:46:37 2025

@author: 10681
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import random

def generate_demo_data():
    # 连接数据库
    conn = sqlite3.connect('wetland.db')
    cursor = conn.cursor()
    
    # 清空现有数据
    cursor.execute("DELETE FROM wetland_data")
    conn.commit()
    
    # 定义湿地位置
    locations = ['湿地A', '湿地B', '湿地C', '湿地D', '湿地E']
    
    # 生成时间序列（过去两年，每月3次监测）
    start_date = datetime.now() - timedelta(days=730)
    dates = []
    current_date = start_date
    while current_date <= datetime.now():
        # 每月生成3个监测日期
        for _ in range(3):
            dates.append(current_date)
        # 移动到下个月
        current_date = current_date + timedelta(days=30)
    
    # 生成模拟数据
    data = []
    for date in dates:
        for location in locations:
            # 基础值，每个湿地略有不同
            base_values = {
                '湿地A': {'water_quality': 7.8, 'biodiversity': 0.75, 'vegetation': 0.82, 'water_level': 1.2},
                '湿地B': {'water_quality': 6.9, 'biodiversity': 0.68, 'vegetation': 0.78, 'water_level': 1.1},
                '湿地C': {'water_quality': 8.1, 'biodiversity': 0.81, 'vegetation': 0.85, 'water_level': 1.4},
                '湿地D': {'water_quality': 7.2, 'biodiversity': 0.72, 'vegetation': 0.80, 'water_level': 1.3},
                '湿地E': {'water_quality': 7.5, 'biodiversity': 0.70, 'vegetation': 0.79, 'water_level': 1.0}
            }
            
            # 季节性变化
            month = date.month
            season_factor = 1.0 + 0.1 * np.sin(2 * np.pi * (month - 3) / 12)  # 春季最高
            
            # 随机波动
            random_factor = 1.0 + np.random.normal(0, 0.05)
            
            # 计算各项指标
            base = base_values[location]
            water_quality = base['water_quality'] * season_factor * random_factor
            biodiversity = base['biodiversity'] * season_factor * random_factor
            vegetation = base['vegetation'] * season_factor * random_factor
            water_level = base['water_level'] * season_factor * random_factor
            
            # 温度和降雨量（有季节性）
            if month in [12, 1, 2]:  # 冬季
                temperature = 5 + np.random.normal(0, 3)
                rainfall = 5 + np.random.exponential(3)
            elif month in [3, 4, 5]:  # 春季
                temperature = 15 + np.random.normal(0, 4)
                rainfall = 15 + np.random.exponential(5)
            elif month in [6, 7, 8]:  # 夏季
                temperature = 25 + np.random.normal(0, 5)
                rainfall = 25 + np.random.exponential(7)
            else:  # 秋季
                temperature = 15 + np.random.normal(0, 4)
                rainfall = 10 + np.random.exponential(4)
            
            # 添加一些异常值（5%的概率）
            if random.random() < 0.05:
                water_quality *= 0.7  # 水质下降
                
            if random.random() < 0.03:
                water_level *= 0.6  # 水位异常低
                
            if random.random() < 0.02:
                biodiversity *= 0.8  # 生物多样性下降
            
            # 确保数值在合理范围内
            water_quality = max(4.0, min(9.5, water_quality))
            biodiversity = max(0.4, min(0.95, biodiversity))
            vegetation = max(0.5, min(0.98, vegetation))
            water_level = max(0.3, min(2.5, water_level))
            temperature = max(-5, min(40, temperature))
            rainfall = max(0, min(100, rainfall))
            
            # 添加到数据列表
            data.append((
                date.strftime('%Y-%m-%d'),
                location,
                round(water_quality, 2),
                round(biodiversity, 3),
                round(vegetation, 3),
                round(water_level, 2),
                round(temperature, 1),
                round(rainfall, 1)
            ))
    
    # 插入数据库
    cursor.executemany('''
        INSERT INTO wetland_data 
        (date, location, water_quality, biodiversity_index, vegetation_coverage, water_level, temperature, rainfall)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    
    conn.commit()
    conn.close()
    
    print(f"已生成 {len(data)} 条演示数据")
    
    # 同时保存为CSV文件便于查看
    df = pd.DataFrame(data, columns=[
        'date', 'location', 'water_quality', 'biodiversity_index', 
        'vegetation_coverage', 'water_level', 'temperature', 'rainfall'
    ])
    df.to_csv('wetland_demo_data.csv', index=False)
    print("数据已保存为 wetland_demo_data.csv")

if __name__ == '__main__':
    generate_demo_data()