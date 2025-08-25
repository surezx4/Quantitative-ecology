# app.R
library(shiny)
library(vegan)
library(DT)
library(shinyjs)
library(readxl)

# 主应用界面
ui <- navbarPage(
  "Community Ecology Analyzer",
  id = "main_nav",
  
  # 数据管理模块
  tabPanel("Data Management",
           sidebarLayout(
             sidebarPanel(
               h4("Data Import"),
               fileInput("file_input", "Upload Data", 
                         accept = c(".csv", ".txt", ".xlsx")),
               radioButtons("sep", "Separator",
                            choices = c(Comma = ",", Semicolon = ";", Tab = "\t"),
                            selected = ","),
               checkboxInput("header", "Header", TRUE),
               
               h4("Data Export"),
               downloadButton("download_data", "Download Processed Data")
             ),
             mainPanel(
               DTOutput("data_preview")
             )
           )),
  
  # 分析方法导航
  navbarMenu("Analyses",
             # PCA分析模块
             tabPanel("PCA",
                      analysisUI("pca")),
             
             # CA分析模块
             tabPanel("Correspondence Analysis",
                      analysisUI("ca")),
             
             # RDA分析模块
             tabPanel("Redundancy Analysis",
                      analysisUI("rda")),
             
             # CCA分析模块
             tabPanel("Canonical Correspondence Analysis",
                      analysisUI("cca"))
  )
)

# 服务器逻辑
server <- function(input, output, session) {
  # 响应式数据存储
  rv <- reactiveValues(
    data = NULL,
    env_data = NULL
  )
  
  # 数据导入
  observeEvent(input$file_input, {
    req(input$file_input)
    ext <- tools::file_ext(input$file_input$name)
    
    tryCatch({
      if(ext == "xlsx") {
        rv$data <- read_excel(input$file_input$datapath)
      } else {
        rv$data <- read.csv(input$file_input$datapath,
                            sep = input$sep,
                            header = input$header)
      }
    }, error = function(e) {
      showNotification(paste("Error:", e$message), type = "error")
    })
  })
  
  # 数据预览
  output$data_preview <- renderDT({
    req(rv$data)
    datatable(rv$data, options = list(scrollX = TRUE))
  })
  
  # 数据导出
  output$download_data <- downloadHandler(
    filename = function() {
      paste("community_data_", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(rv$data, file, row.names = FALSE)
    }
  )
  
  # 注册分析方法
  callModule(pcaAnalysis, "pca", data = reactive(rv$data))
  callModule(caAnalysis, "ca", data = reactive(rv$data))
  callModule(rdaAnalysis, "rda", data = reactive(rv$data))
  callModule(ccaAnalysis, "cca", data = reactive(rv$data))
}

# 通用分析界面模板
analysisUI <- function(id) {
  ns <- NS(id)
  tagList(
    sidebarLayout(
      sidebarPanel(
        h4("Analysis Parameters"),
        uiOutput(ns("params_ui")),
        mainPanel(
          tabsetPanel(
            tabPanel("Results", verbatimTextOutput(ns("results"))),
            tabPanel("Plot", plotOutput(ns("plot"))),
            tabPanel("Download", 
                     downloadButton(ns("download_results"), "Download Results"),
                     downloadButton(ns("download_plot"), "Download Plot"))
          )
        )
      )
    )
}

# PCA分析模块 ============================================================
pcaAnalysis <- function(input, output, session, data) {
  ns <- session$ns
  
  # 参数界面
  output$params_ui <- renderUI({
    req(data())
    tagList(
      selectInput(ns("scale"), "Scale variables", 
                  choices = c("TRUE" = TRUE, "FALSE" = FALSE), 
                  selected = TRUE),
      actionButton(ns("run"), "Run Analysis")
    )
  })
  
  # 运行分析
  pca_result <- eventReactive(input$run, {
    req(data())
    df <- data()
    # 仅保留数值列
    num_cols <- sapply(df, is.numeric)
    df <- df[, num_cols]
    
    # 执行PCA
    pca <- rda(df, scale = as.logical(input$scale))
    return(pca)
  })
  
  # 显示结果
  output$results <- renderPrint({
    req(pca_result())
    summary(pca_result())
  })
  
  # 绘图
  output$plot <- renderPlot({
    req(pca_result())
    biplot(pca_result(), main = "PCA Biplot")
  })
  
  # 结果下载
  output$download_results <- downloadHandler(
    filename = "pca_results.txt",
    content = function(file) {
      capture.output(summary(pca_result()), file = file)
    }
  )
  
  # 图形下载
  output$download_plot <- downloadHandler(
    filename = "pca_plot.png",
    content = function(file) {
      png(file)
      biplot(pca_result())
      dev.off()
    }
  )
}

# CA分析模块 =============================================================
caAnalysis <- function(input, output, session, data) {
  # 类似PCA模块的实现
  # ...
}

# RDA分析模块 ============================================================
rdaAnalysis <- function(input, output, session, data) {
  # 需要环境变量数据
  # ...
}

# CCA分析模块 ============================================================
ccaAnalysis <- function(input, output, session, data) {
  # 需要环境变量数据
  # ...
}

# 运行应用
shinyApp(ui, server)