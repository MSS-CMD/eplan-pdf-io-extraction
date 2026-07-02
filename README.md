# EPLAN I/O 自动提取工具

从 EPLAN 电气图纸 PDF 中自动提取 PLC I/O 表，生成结构化 Excel。

## 快速使用

**方式一：exe（无需环境）**
```
把PDF拖到 EPLAN_IO_Extract.exe 上松开，自动出Excel
```

**方式二：源码（需 Python）**
```bash
pip install pymupdf openpyxl
python run_extract.py 图纸.pdf
```

**方式三：拖拽/选文件**
```
双击 extract.bat → 选PDF → 自动提取
或 把PDF拖到 extract.bat 上
```

## 项目结构

```
├── extract.bat              # 双击/拖拽入口
├── launcher.py              # 启动器
├── run_extract.py           # 提取脚本
├── MAINTAIN.md              # ← 维护指南（新图纸看这个）
└── framework/
    ├── core.py              # 主引擎
    ├── config.json          # 模板配置
    ├── parsers/             # 4个解析器
    └── utils/               # 工具函数
```

## 已验证项目

| 项目 | 页数 | I/O点数 | 包含类型 |
|:----|:----:|:-------:|:---------|
| PLC1 | 557 | 1,260 | DI+DQ+IOLINK+阀岛+AI |
| PLC3 | 226 | 188 | DI+DQ+安全输入+安全输出 |
| PLC7 | 702 | 496 | DI+DQ+IOLINK+阀岛+AI |
