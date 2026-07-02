# 维护指南

新图纸来了，按下面场景改对应的文件，不需要动 Python 代码。

---

## 场景一：英文图纸

**改 `framework/config.json` → `页面类型关键词`**

```json
{
  "页面类型关键词": {
    "DI": ["Digital Input Module", "数字量输入模块 16位"],
    "DQ": ["Digital Output Module", "数字量输出模块 16位"]
  }
}
```

框架会依次匹配，任一关键词命中即识别为该类型。

## 场景二：坐标偏移（不同EPLAN模板）

框架通常能自动检测坐标，但如果页面布局差异太大，可以预设模板。

**改 `framework/config.json` → `列布局模板`**

```json
{
  "列布局模板": {
    "EPLAN_COMPACT": {
      "DI": {
        "bit_label_re": "^(DI|FDI) Bit (\\d+)$",
        "address_re": "^I\\d{4}\\.\\d$",
        "bit_label_y": 520,
        "address_y_range": [530, 550],
        "device_tag_y_range": [540, 560],
        "desc_y_range": [620, 660]
      }
    }
  }
}
```

添加新模板后，框架的 `auto_config()` 会尝试匹配——检测到 Bit 标签在 y≈520 时会自动用 `EPLAN_COMPACT` 模板。

## 场景三：地址格式不同

不同 PLC 系列地址格式不同。如果自动检测失败，需改解析器中的 `address_re`。

| PLC 系列 | 地址格式 | 正则 |
|:---------|:---------|:-----|
| S7-1500 | I1000.0 / Q1000.0 | `^[IQ]\d{4}\.\d$` |
| S7-1200 | %IW0.0 / %QW0.0 | `^%[IQ]W\d+\.\d$` |
| 其他 | AI0 / AO0 | `^[AI]O?\d+$` |

在 `config.json` → `列布局模板` 中对应类型的 `address_re` 字段修改。

## 场景四：IOLINK 信号名搜索不到

改 `framework/config.json` → `IOLINK模式检测`

```json
{
  "IOLINK模式检测": {
    "signal_pattern": "S\\d{4}_",
    "search_radius_x": 450,
    "search_radius_y": 120
  }
}
```

- `search_radius_x`：从地址向右搜索的像素范围
- `search_radius_y`：从地址上下搜索的像素范围
- 如果信号名在远处，增大这两个值

## 场景五：完全新的页面类型

需要新写一个解析器放入 `framework/parsers/`，然后在入口脚本中注册：

```python
register("新类型", new_parser.parse)
```

参考已有的 `column.py`（列布局）或 `valve.py`（阀岛）的写法。

## 验证方法

改完后，用对应 PDF 跑一下验证：

```bash
python run_extract.py 图纸.pdf
```

看输出的 I/O 统计是否符合预期：
- DI/DQ 每页固定 8 点（标准 16 位模块）
- 地址范围连续无跳空
- 描述字段无页眉噪声残留

## 重新打包 exe

如果源码有改动，需要重新生成 exe：

```bash
pip install pyinstaller
pyinstaller --onefile --name "EPLAN_IO_Extract" ^
  --add-data "framework;framework" ^
  --add-data "framework\config.json;framework" ^
  --hidden-import pymupdf --hidden-import openpyxl ^
  --distpath "." run_extract.py
```
