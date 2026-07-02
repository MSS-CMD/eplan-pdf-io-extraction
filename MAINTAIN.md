# 维护指南

## 新图纸适配流程

**第一步：识别模板类型**

拿到新图纸后，打开第一页DI页，看Bit标签的y坐标：

```
DI Bit 0  x=233  y=571   → EPLAN_S7_1500_标准模板
DI Bit 0  x=...  y=520   → 新模板，需要新建条目
```

**第二步：修改 config.json**

如果是已知模板，直接用对应的模板名即可。

如果是新模板，在 `列布局模板` 中添加一个新条目：

```json
{
  "列布局模板": {
    "新模板名称": {
      "说明": "这个模板的特征",
      "DI": {
        "bit_label_re": "^(DI|FDI) Bit (\\d+)$",
        "address_re": "^I\\d{4}\\.\\d$",
        "bit_label_y": 571,
        "address_y_range": [580, 605],
        "desc_y_range": [665, 715]
      },
      "DQ": {
        "bit_label_re": "^DO Bit (\\d+)$",
        "address_re": "^Q\\d{4}\\.\\d$",
        "bit_label_y": 178,
        "address_y_range": [148, 172],
        "desc_y_range": [665, 715]
      }
    }
  }
}
```

**第三步：验证**

```bash
python run_extract.py 新图纸.pdf
```

检查输出的I/O点数是否符合预期。

---

## 常见改法

### 1. 英文图纸 → 改 `页面类型关键词`

```json
"DI": ["Digital Input Module", "数字量输入模块 16位"]
```

### 2. 坐标偏移 → 改 `bit_label_y` / `address_y_range`

从PDF第一页读出Bit标签的y坐标，填入即可。

### 3. 地址格式不同 → 改 `address_re`

| PLC系列 | 地址格式 | 正则 |
|:--------|:---------|:-----|
| S7-1500 | I1000.0 | `^[IQ]\d{4}\.\d$` |
| S7-1200 | %IW0.0 | `^%[IQ]W\d+\.\d$` |

### 4. 完全新的页面类型 → 加解析器

参考 `framework/parsers/` 下已有的写法，新增一个解析器文件，然后在入口脚本注册。

---

## 重新打包exe

```bash
pip install pyinstaller
pyinstaller --onefile --name "EPLAN_IO_Extract" ^
  --add-data "framework;framework" ^
  --add-data "framework\config.json;framework" ^
  --hidden-import pymupdf --hidden-import openpyxl ^
  --distpath "." run_extract.py
```
