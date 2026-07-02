# EPLAN I/O 自动提取工具

## 概述

从 EPLAN 电气图纸 PDF 中自动提取 PLC I/O 表，生成结构化 Excel。

## 功能

- 自动识别页面类型（DI/DQ/安全输入输出/IOLINK/阀岛/AI）
- 自动检测布局坐标参数（无需手动配置）
- 支持 7 种 I/O 类型
- 一键导出带格式的 Excel（颜色区分、筛选、汇总）

## 快速开始

### 方式一：exe 运行（无需环境）

1. 下载 `EPLAN_IO_Extract.exe`
2. 将 PDF 拖拽到 exe 上，或双击 exe 选择文件
3. 等待完成，自动在同目录生成 `xxx_IO_总表.xlsx`

### 方式二：源码运行（需 Python）

```bash
pip install pymupdf openpyxl
python run_extract.py 图纸.pdf
```

## 项目结构

```
├── extract.bat              # 双击/拖拽入口
├── launcher.py              # 启动器
├── run_extract.py           # 提取脚本
├── framework/
│   ├── core.py              # 主引擎（发现+调度+后处理）
│   ├── config.json          # 模板配置（新图纸改这里）
│   ├── parsers/
│   │   ├── column.py        # DI/DQ/安全输入输出 列解析
│   │   ├── iolink.py        # IOLINK 双模式解析
│   │   ├── valve.py         # 阀岛解析
│   │   └── analog.py        # AI模拟量解析
│   └── utils/
│       ├── text.py          # 文本工具+后处理
│       └── excel.py         # Excel导出
└── projects/                # 项目入口脚本示例
```

## 配置说明

新图纸模板不同时，修改 `framework/config.json`：

- `页面类型关键词`：不同CAD软件的关键词
- `列布局模板`：DI/DQ的坐标参数
- `安全输出布局`：安全模块配置
- `IOLINK模式检测`：信号名搜索范围

## 验证结果

| 项目 | 页数 | I/O点数 | 类型 |
|:----|:----:|:-------:|:-----|
| PLC1 | 557 | 1,260 | DI+DQ+IOLINK+阀岛+AI |
| PLC3 | 226 | 188 | DI+DQ+安全输入+安全输出 |
| PLC7 | 702 | 496 | DI+DQ+IOLINK+阀岛+AI |
