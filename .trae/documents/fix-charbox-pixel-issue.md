# 修复 charBox 像素值导致图片无法显示的问题

## 问题分析

在 `images.json` 中，部分 `charBox` 的值是像素值而不是比例值（0-1）。当 `charBox.size` 是像素值（如 200）时，`calculateImageScale` 函数的计算会产生极小的缩放比例，导致图片宽度接近 0。

## 解决方案

修改 `calculateImageScale` 函数，自动检测 `charBox.size` 是像素值还是比例值：

* 如果 `size > 1`，说明是像素值，需要先转换为比例值

* 如果 `size <= 1`，说明已经是比例值，直接使用

## 修改文件

### 1. `d:\space\html\print\static\print.html`

修改 `calculateImageScale` 函数：

```javascript
function calculateImageScale(charBox, imgNaturalWidth) {
    if (!charBox || !charBox.size) return null;
    
    const fontSizeMap = {
        'large': 16,
        'medium': 15,
        'small': 11
    };
    
    const targetFontSizePt = fontSizeMap[charBox.fontSize] || 11;
    const targetFontSizePx = targetFontSizePt * (96 / 72);
    
    // 检测 size 是像素值还是比例值
    let charBoxSizeRatio = charBox.size;
    if (charBox.size > 1) {
        // size 是像素值，转换为比例
        charBoxSizeRatio = charBox.size / imgNaturalWidth;
    }
    
    const charBoxPixelSize = charBoxSizeRatio * imgNaturalWidth;
    
    const scale = targetFontSizePx / charBoxPixelSize;
    
    return scale;
}
```

同样需要处理 `x` 和 `y` 字段，它们可能也是像素值。

## 实施步骤

1. 修改 `calculateImageScale` 函数，添加像素值检测逻辑
2. 测试验证修复效果

