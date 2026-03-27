# 批量将 docx 文件转换为 PDF 实施计划

## 需求概述
递归搜索指定文件夹中的所有 `.docx` 文件，并将其转换为 PDF 保存到原位置。

## 技术方案

### 方案选择
在 Windows 系统上，将 docx 转换为 PDF 有以下几种方案：

| 方案 | 优点 | 缺点 |
|------|------|------|
| **python-docx2pdf** | 简单易用，一行代码搞定 | 需要安装 Microsoft Word |
| **LibreOffice CLI** | 免费，不需要 Word | 需要安装 LibreOffice |
| **win32com (COM)** | 原生 Windows 支持，功能强大 | 需要安装 Microsoft Word，代码稍复杂 |

**推荐方案**: 使用 `win32com` 直接调用 Word COM 接口，这是 Windows 上最可靠的方式，转换质量最佳。

### 前置条件
- Windows 操作系统
- 已安装 Microsoft Word

## 实施步骤

### 步骤 1: 创建转换脚本
创建 `docx_to_pdf.py` 文件，包含以下功能：

```python
import os
import sys
from pathlib import Path

def convert_docx_to_pdf(docx_path, word_app):
    """
    将单个 docx 文件转换为 PDF
    
    Args:
        docx_path: docx 文件的完整路径
        word_app: Word COM 对象
    """
    # 使用 Word COM 接口打开文档并另存为 PDF
    ...

def batch_convert(folder_path):
    """
    递归搜索文件夹中的所有 docx 文件并批量转换
    
    Args:
        folder_path: 要搜索的文件夹路径
    """
    # 遍历文件夹，找到所有 .docx 文件
    # 调用 convert_docx_to_pdf 进行转换
    ...
```

### 步骤 2: 核心功能实现
1. **递归搜索**: 使用 `os.walk()` 或 `pathlib.Path.rglob()` 递归查找所有 `.docx` 文件
2. **Word COM 调用**: 使用 `win32com.client` 调用 Word 应用程序进行转换
3. **错误处理**: 处理转换失败的情况，记录错误日志
4. **进度显示**: 显示转换进度和结果统计

### 步骤 3: 脚本参数
- 支持命令行参数指定文件夹路径
- 支持交互式输入路径
- 支持跳过已存在的 PDF 文件

## 代码结构

```
d:\space\html\print\
└── docx_to_pdf.py    # 新建的转换脚本
```

## 实现细节

### 文件结构
```python
import os
import sys
from pathlib import Path

def convert_docx_to_pdf(docx_path, word_app):
    """将单个 docx 文件转换为 PDF"""
    docx_path = Path(docx_path).resolve()
    pdf_path = docx_path.with_suffix('.pdf')
    
    try:
        doc = word_app.Documents.Open(str(docx_path))
        doc.SaveAs(str(pdf_path), FileFormat=17)  # 17 = PDF format
        doc.Close()
        return True, None
    except Exception as e:
        return False, str(e)

def batch_convert(folder_path, skip_existing=True):
    """批量转换文件夹中的所有 docx 文件"""
    folder = Path(folder_path)
    
    if not folder.exists():
        print(f"错误：文件夹不存在: {folder_path}")
        return
    
    # 查找所有 docx 文件
    docx_files = list(folder.rglob("*.docx"))
    
    if not docx_files:
        print("未找到任何 .docx 文件")
        return
    
    print(f"找到 {len(docx_files)} 个 .docx 文件")
    
    # 初始化 Word COM
    import win32com.client
    word_app = win32com.client.Dispatch("Word.Application")
    word_app.Visible = False
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    try:
        for i, docx_file in enumerate(docx_files, 1):
            pdf_path = docx_file.with_suffix('.pdf')
            
            if skip_existing and pdf_path.exists():
                print(f"[{i}/{len(docx_files)}] 跳过（PDF已存在）: {docx_file.name}")
                skip_count += 1
                continue
            
            print(f"[{i}/{len(docx_files)}] 转换中: {docx_file.name}")
            success, error = convert_docx_to_pdf(docx_file, word_app)
            
            if success:
                success_count += 1
            else:
                error_count += 1
                print(f"  错误: {error}")
    finally:
        word_app.Quit()
    
    print(f"\n转换完成！")
    print(f"成功: {success_count}")
    print(f"跳过: {skip_count}")
    print(f"失败: {error_count}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = input("请输入要转换的文件夹路径: ").strip()
    
    batch_convert(folder)
```

## 依赖安装
```bash
pip install pywin32
```

## 使用方式
```bash
# 方式1: 命令行参数
python docx_to_pdf.py "D:\documents"

# 方式2: 交互式
python docx_to_pdf.py
# 然后输入文件夹路径
```

## 注意事项
1. 转换过程中 Word 应用程序会在后台运行，请勿手动操作
2. 如果转换大量文件，可能需要较长时间
3. 确保有足够的磁盘空间存放生成的 PDF 文件
4. 如果 docx 文件正在被其他程序打开，转换可能会失败
