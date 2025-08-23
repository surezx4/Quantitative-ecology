library(raster)
library(terra)  # 使用更高效的terra包处理大文件

# 1. 设置数据路径
data_path <- "D:/LC09_L2SP_120043_20240529_20240530_02_T1"

# 2. 加载波段数据 - 使用terra包更高效处理大文件
band_files <- list.files(
  path = data_path,
  pattern = ".*_B[1-7]\\.TIF$",
  full.names = TRUE
)

# 按波段顺序排序
band_order <- c(1:7)
ordered_files <- sapply(band_order, function(b) {
  grep(paste0("_B", b, "\\.TIF$"), band_files, value = TRUE)
})

# 创建SpatRaster对象 - 比raster更高效
lsat_stack <- rast(ordered_files)

# 3. 读取并解析MTL文件
mtl_file <- file.path(data_path, "LC09_L2SP_120043_20240529_20240530_02_T1_MTL.txt")

# 安全地读取文件
if(!file.exists(mtl_file)) {
  stop("MTL文件不存在: ", mtl_file)
}

mtl_content <- readLines(mtl_file)

# 4. 提取处理级别
find_metadata_value <- function(pattern) {
  lines <- mtl_content[grep(pattern, mtl_content, ignore.case = TRUE)]
  if(length(lines) > 0) {
    value <- gsub(".*= \"?(.*?)\"?$", "\\1", lines[1])
    return(trimws(value))
  }
  return(NA)
}

processing_level <- find_metadata_value("PROCESSING_LEVEL")
if(is.na(processing_level)) {
  # 如果无法确定处理级别，根据文件名猜测
  if(grepl("L2SP", basename(mtl_file))) {
    processing_level <- "L2SP"
    cat("根据文件名推断处理级别: L2SP\n")
  } else if(grepl("L1", basename(mtl_file))) {
    processing_level <- "L1"
    cat("根据文件名推断处理级别: L1\n")
  } else {
    stop("无法确定Landsat数据级别")
  }
}

# 5. 根据处理级别进行处理
if(grepl("L2SP", processing_level)) {
  # Level-2地表反射率产品 - 只需应用反射率缩放
  cat("处理Level-2地表反射率产品...\n")
  
  # 提取反射率参数
  extract_band_parameters <- function(param_prefix, band_count = 7) {
    params <- numeric(band_count)
    for(i in 1:band_count) {
      pattern <- paste0(param_prefix, "_BAND_", i)
      value_line <- mtl_content[grep(pattern, mtl_content, ignore.case = TRUE)][1]
      if(!is.na(value_line)) {
        value <- as.numeric(gsub(".*= (\\S+)", "\\1", value_line))
        params[i] <- value
      } else {
        stop("找不到参数: ", pattern)
      }
    }
    return(params)
  }
  
  ref_mult <- extract_band_parameters("REFLECTANCE_MULT")
  ref_add <- extract_band_parameters("REFLECTANCE_ADD")
  
  # 应用反射率转换 - 使用分块处理
  lsat_reflectance <- lsat_stack
  for(i in 1:nlyr(lsat_stack)) {
    lsat_reflectance[[i]] <- lsat_stack[[i]] * ref_mult[i] + ref_add[i]
  }
  
} else if(grepl("L1", processing_level)) {
  # Level-1产品 - 需要辐射定标和大气校正
  cat("处理Level-1产品...\n")
  
  # 提取辐射定标参数
  extract_band_parameters <- function(param_prefix, band_count = 7) {
    params <- numeric(band_count)
    for(i in 1:band_count) {
      pattern <- paste0(param_prefix, "_BAND_", i)
      value_line <- mtl_content[grep(pattern, mtl_content, ignore.case = TRUE)][1]
      if(!is.na(value_line)) {
        value <- as.numeric(gsub(".*= (\\S+)", "\\1", value_line))
        params[i] <- value
      } else {
        stop("找不到参数: ", pattern)
      }
    }
    return(params)
  }
  
  rad_mult <- extract_band_parameters("RADIANCE_MULT")
  rad_add <- extract_band_parameters("RADIANCE_ADD")
  
  # 提取太阳高度角
  sun_elevation_line <- mtl_content[grep("SUN_ELEVATION", mtl_content, ignore.case = TRUE)][1]
  sun_elevation <- as.numeric(gsub(".*= (\\S+)", "\\1", sun_elevation_line))
  
  # 辐射定标：将DN值转换为辐射亮度
  lsat_radiance <- lsat_stack
  for(i in 1:nlyr(lsat_stack)) {
    lsat_radiance[[i]] <- lsat_stack[[i]] * rad_mult[i] + rad_add[i]
  }
  
  # 大气校正 - 黑暗像元减法（流式处理）
  cat("执行大气校正...\n")
  
  # 使用SWIR2波段（B7）识别黑暗像元
  dark_band <- lsat_radiance[[7]]
  
  # 计算黑暗像元阈值（最低1%的值） - 使用抽样方法
  sample_size <- min(1e6, ncell(dark_band))  # 抽样100万个像元或全部像元
  dark_values_sample <- spatSample(dark_band, size = sample_size, method = "regular")
  dark_threshold <- quantile(dark_values_sample, probs = 0.01, na.rm = TRUE)
  
  # 创建黑暗像元掩膜 - 使用抽样
  dark_mask <- dark_band < dark_threshold
  
  # 计算每个波段的黑暗像元平均值 - 使用抽样
  dark_values <- sapply(1:nlyr(lsat_radiance), function(i) {
    band_sample <- spatSample(lsat_radiance[[i]], size = sample_size, method = "regular")
    mask_sample <- spatSample(dark_mask, size = sample_size, method = "regular")
    mean(band_sample[mask_sample], na.rm = TRUE)
  })
  
  # 应用校正 - 使用分块处理
  lsat_corrected <- lsat_radiance
  for(i in 1:nlyr(lsat_radiance)) {
    lsat_corrected[[i]] <- lsat_radiance[[i]] - dark_values[i]
  }
  
  # 转换为地表反射率 - 使用分块处理
  to_reflectance <- function(radiance_band, sun_elev) {
    # 考虑太阳高度角的反射率转换
    radiance_band * pi / (sin(sun_elev * pi/180) * 100)
  }
  
  lsat_reflectance <- lsat_corrected
  for(i in 1:nlyr(lsat_corrected)) {
    lsat_reflectance[[i]] <- to_reflectance(lsat_corrected[[i]], sun_elevation)
  }
} else {
  stop("未知的处理级别: ", processing_level)
}

# 6. 限制反射率在合理范围内 (0-1) - 使用分块处理
cat("限制反射率范围...\n")
lsat_reflectance <- clamp(lsat_reflectance, lower = 0, upper = 1)

# 7. 保存结果 - 使用分块写入
output_file <- file.path(data_path, "landsat9_atmospheric_corrected.tif")
cat("保存结果到:", output_file, "\n")
writeRaster(
  lsat_reflectance,
  filename = output_file,
  datatype = "FLT4S",
  overwrite = TRUE
)

# 8. 高效验证结果
cat("验证结果...\n")

# 使用抽样方法检查反射率范围
sample_points <- spatSample(lsat_reflectance, size = 10000, method = "regular")
ref_range <- apply(sample_points, 2, function(x) range(x, na.rm = TRUE))

cat("\n反射率范围 (基于抽样):\n")
print(ref_range)

# 检查水体区域反射率 (使用抽样)
water_mask_sample <- sample_points[, 5] < 0.1  # 近红外波段反射率低于0.1的像元
water_reflectance <- colMeans(sample_points[water_mask_sample, ], na.rm = TRUE)

cat("\n水体区域平均反射率 (基于抽样):\n")
print(water_reflectance)

cat("\n处理完成！结果已保存至:", output_file, "\n")

# 9. 创建预览图 (使用抽样)
cat("创建预览图...\n")
png_file <- file.path(data_path, "landsat9_preview.png")
png(png_file, width = 1000, height = 800)
par(mfrow = c(1, 2))

# 创建小样本用于预览
preview_sample <- spatSample(lsat_reflectance, size = 100000, method = "regular")

# 假彩色合成 (植被显示为红色)
plotRGB(lsat_reflectance, r = 5, g = 4, b = 3, stretch = "hist", 
        main = "假彩色合成 (B5=红, B4=绿, B3=蓝)")

# 真彩色合成
plotRGB(lsat_reflectance, r = 4, g = 3, b = 2, stretch = "lin", 
        main = "真彩色合成 (B4=红, B3=绿, B2=蓝)")

dev.off()
cat("预览图已保存至:", png_file, "\n")