# HTML 打印设计完全指南

> 一份全面、详细的HTML打印样式开发文档，涵盖所有语法、最佳实践和常见陷阱

---

## 目录

1. [基础概念](#一基础概念)
2. [@media print 媒体查询](#二media-print-媒体查询)
3. [@page 页面规则](#三page-页面规则)
4. [页面控制属性](#四页面控制属性)
5. [内容显示控制](#五内容显示控制)
6. [字体与排版](#六字体与排版)
7. [颜色与背景](#七颜色与背景)
8. [图片处理](#八图片处理)
9. [表格打印](#九表格打印)
10. [页眉页脚](#十页眉页脚)
11. [浏览器兼容性](#十一浏览器兼容性)
12. [常见错误与陷阱](#十二常见错误与陷阱)
13. [最佳实践](#十三最佳实践)
14. [调试技巧](#十四调试技巧)

---

## 一、基础概念

### 1.1 什么是打印样式

打印样式是指当用户将网页内容打印到纸张或导出为PDF时应用的CSS规则。通过专门的打印样式，可以：

- 隐藏不必要的UI元素（导航栏、按钮、广告等）
- 调整布局和字体大小以适应纸张
- 控制分页行为
- 添加页眉页脚和页码
- 优化颜色和背景

### 1.2 打印样式的工作原理

当用户触发打印操作（`Ctrl+P` 或 `window.print()`）时，浏览器会：

1. 应用 `@media print` 中定义的所有CSS规则
2. 根据 `@page` 规则设置页面尺寸和边距
3. 计算内容布局并处理分页
4. 生成打印预览或发送到打印机

---

## 二、@media print 媒体查询

### 2.1 基本语法

```css
@media print {
  /* 打印时应用的样式 */
}
```

### 2.2 完整示例

```css
@media print {
  /* 隐藏不需要打印的元素 */
  nav, header, footer, .ads, .no-print {
    display: none !important;
  }
  
  /* 调整基础样式 */
  body {
    font-size: 12pt;
    line-height: 1.5;
    color: #000;
  }
  
  /* 确保内容宽度适应纸张 */
  .container {
    width: 100%;
    margin: 0;
    padding: 0;
  }
}
```

### 2.3 结合屏幕样式

推荐的做法是为屏幕和打印分别定义样式：

```css
/* 屏幕显示样式 */
@media screen {
  .print-only {
    display: none;
  }
}

/* 打印样式 */
@media print {
  .no-print {
    display: none !important;
  }
  .print-only {
    display: block;
  }
}
```

HTML结构示例：

```html
<nav class="no-print">网站导航</nav>
<main>主要内容</main>
<footer class="print-only">打印专用页脚 - 机密文件</footer>
```

---

## 三、@page 页面规则

### 3.1 基本语法

`@page` 规则用于设置打印页面的整体属性：

```css
@page {
  margin: 2.54cm;  /* 设置页边距 */
  size: A4;        /* 设置页面尺寸 */
}
```

### 3.2 页面尺寸设置

```css
@page {
  /* 标准纸张尺寸 */
  size: A4;           /* 210mm × 297mm */
  size: A5;           /* 148mm × 210mm */
  size: A3;           /* 297mm × 420mm */
  size: Letter;       /* 8.5in × 11in */
  size: Legal;        /* 8.5in × 14in */
  
  /* 自定义尺寸 */
  size: 210mm 297mm;  /* 自定义宽高 */
  
  /* 页面方向 */
  size: A4 landscape; /* 横向打印 */
  size: A4 portrait;  /* 纵向打印（默认） */
}
```

### 3.3 页边距设置

```css
@page {
  /* 统一边距 */
  margin: 2cm;
  
  /* 分别设置各边边距 */
  margin-top: 2cm;
  margin-right: 1.5cm;
  margin-bottom: 2cm;
  margin-left: 1.5cm;
  
  /* 简写形式 */
  margin: 2cm 1.5cm;  /* 上下 左右 */
  margin: 2cm 1.5cm 2cm 1.5cm;  /* 上 右 下 左 */
}
```

### 3.4 伪类选择器

`@page` 支持多种伪类来选择特定页面：

```css
@page {
  margin: 2cm;
}

/* 第一页 */
@page :first {
  margin-top: 3cm;  /* 第一页顶部边距更大 */
}

/* 奇数页（右侧页面） */
@page :right {
  margin-left: 3cm;   /* 左侧留出装订空间 */
  margin-right: 2cm;
}

/* 偶数页（左侧页面） */
@page :left {
  margin-left: 2cm;
  margin-right: 3cm;  /* 右侧留出装订空间 */
}

/* 空白页 */
@page :blank {
  @top-center { content: none; }  /* 空白页不显示页眉 */
}
```

### 3.5 边距区域（Chromium浏览器支持）

```css
@page {
  margin: 2cm;
  
  /* 页眉区域 */
  @top-left {
    content: "文档标题";
    font-size: 10pt;
  }
  
  @top-center {
    content: "公司机密";
    font-size: 10pt;
    color: #666;
  }
  
  @top-right {
    content: "第 " counter(page) " 页";
    font-size: 10pt;
  }
  
  /* 页脚区域 */
  @bottom-center {
    content: "© 2024 公司名称";
    font-size: 9pt;
    color: #999;
  }
}
```

**支持的边距区域：**

- `@top-left-corner`
- `@top-left`
- `@top-center`
- `@top-right`
- `@top-right-corner`
- `@bottom-left-corner`
- `@bottom-left`
- `@bottom-center`
- `@bottom-right`
- `@bottom-right-corner`
- `@left-top`
- `@left-middle`
- `@left-bottom`
- `@right-top`
- `@right-middle`
- `@right-bottom`

---

## 四、页面控制属性

### 4.1 分页控制属性

CSS提供三个主要属性控制分页行为：

| 属性 | 说明 | 常用值 |
|------|------|--------|
| `page-break-before` | 元素前是否分页 | `auto`, `always`, `avoid`, `left`, `right` |
| `page-break-after` | 元素后是否分页 | `auto`, `always`, `avoid`, `left`, `right` |
| `page-break-inside` | 元素内部是否允许分页 | `auto`, `avoid` |

**现代标准属性（推荐同时使用）：**

| 属性 | 说明 |
|------|------|
| `break-before` | 替代 `page-break-before` |
| `break-after` | 替代 `page-break-after` |
| `break-inside` | 替代 `page-break-inside` |

### 4.2 强制分页示例

```css
@media print {
  /* 每个章节从新页面开始 */
  h1 {
    page-break-before: always;
    break-before: page;
  }
  
  /* 章节结束后分页 */
  .chapter {
    page-break-after: always;
    break-after: page;
  }
  
  /* 避免在标题后断开 */
  h2, h3 {
    page-break-after: avoid;
    break-after: avoid;
  }
  
  /* 避免在元素内部分页 */
  table, .keep-together {
    page-break-inside: avoid;
    break-inside: avoid;
  }
}
```

### 4.3 表格行分页控制

```css
@media print {
  table {
    page-break-inside: auto;  /* 允许表格跨页 */
    border-collapse: collapse; /* 重要：必须设置 */
  }
  
  tr {
    page-break-inside: avoid;  /* 避免行被分割 */
    break-inside: avoid;
  }
  
  td, th {
    padding: 4px;  /* 减小内边距以避免分页问题 */
  }
}
```

**⚠️ 重要提示：** 表格行分页控制需要设置 `border-collapse: collapse`，否则可能不生效。

### 4.4 孤行和寡行控制

```css
@media print {
  p {
    /* 段落顶部至少保留3行 */
    widows: 3;
    
    /* 段落底部至少保留3行 */
    orphans: 3;
  }
}
```

- **Widows（寡行）**：段落最后一行单独出现在新页面顶部
- **Orphans（孤行）**：段落第一行单独出现在页面底部

---

## 五、内容显示控制

### 5.1 隐藏不需要的元素

```css
@media print {
  /* 常见的需要隐藏的元素 */
  nav,              /* 导航栏 */
  header,           /* 页头 */
  footer,           /* 页脚 */
  aside,            /* 侧边栏 */
  .ads,             /* 广告 */
  .sidebar,         /* 侧边内容 */
  .comments,        /* 评论 */
  .share-buttons,   /* 分享按钮 */
  .breadcrumb,      /* 面包屑导航 */
  .no-print {       /* 自定义类 */
    display: none !important;
  }
}
```

### 5.2 显示打印专用内容

```css
@media screen {
  .print-only {
    display: none;
  }
}

@media print {
  .print-only {
    display: block;
  }
  
  /* 打印专用水印 */
  .watermark::before {
    content: "机密文件";
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-45deg);
    font-size: 72pt;
    color: rgba(200, 200, 200, 0.3);
    pointer-events: none;
    z-index: 1000;
  }
}
```

### 5.3 链接处理

```css
@media print {
  /* 显示链接URL */
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 90%;
    color: #666;
  }
  
  /* 外部链接特殊标记 */
  a[href^="http"]::after {
    content: " ↗ " attr(href);
  }
  
  /* 移除链接样式 */
  a {
    text-decoration: none;
    color: #000;
  }
}
```

### 5.4 二维码打印

```css
@media screen {
  .print-qr {
    display: none;
  }
}

@media print {
  .print-qr {
    display: block;
    position: fixed;
    bottom: 1cm;
    right: 1cm;
    width: 3cm;
    height: 3cm;
  }
}
```

---

## 六、字体与排版

### 6.1 打印字体单位

**推荐单位优先级：**

1. **pt（点）** - 最常用，1pt = 1/72英寸
2. **mm/cm** - 公制单位，适合精确控制
3. **in** - 英制单位

**避免使用：**
- px - 屏幕单位，打印时不一致
- em/rem - 相对单位，打印时可能不稳定

### 6.2 字体大小设置

```css
@media print {
  body {
    font-size: 12pt;      /* 正文字体 */
    line-height: 1.5;     /* 行高 */
  }
  
  h1 { font-size: 18pt; }
  h2 { font-size: 16pt; }
  h3 { font-size: 14pt; }
  h4 { font-size: 12pt; }
  
  small, .footnote {
    font-size: 10pt;      /* 脚注最小9pt */
  }
}
```

### 6.3 字体族选择

```css
@media print {
  body {
    /* 打印安全字体 */
    font-family: 
      "Times New Roman",  /* 衬线字体，正式文档 */
      Georgia,
      "Songti SC",        /* 中文宋体 */
      serif;
  }
  
  /* 或使用无衬线字体 */
  .modern-doc {
    font-family:
      Arial,
      Helvetica,
      "Microsoft YaHei",  /* 中文微软雅黑 */
      sans-serif;
  }
}
```

**打印安全字体推荐：**

| 字体 | 类型 | 适用场景 |
|------|------|----------|
| Times New Roman | 衬线 | 正式文档、论文 |
| Georgia | 衬线 | 屏幕阅读优化 |
| Arial | 无衬线 | 现代商务文档 |
| Helvetica | 无衬线 | 专业设计 |
| Courier New | 等宽 | 代码、表格 |

### 6.4 段落和文本样式

```css
@media print {
  p {
    text-align: justify;      /* 两端对齐 */
    text-indent: 2em;         /* 首行缩进 */
    margin-bottom: 0.5em;
    orphans: 3;
    widows: 3;
  }
  
  /* 标题样式 */
  h1, h2, h3 {
    page-break-after: avoid;
    break-after: avoid;
  }
  
  /* 列表样式 */
  ul, ol {
    margin-left: 2em;
  }
  
  li {
    margin-bottom: 0.25em;
  }
}
```

---

## 七、颜色与背景

### 7.1 强制打印背景色/背景图

默认情况下，浏览器会忽略背景色和背景图以节省墨水。要强制打印：

```css
@media print {
  * {
    /* WebKit浏览器 */
    -webkit-print-color-adjust: exact !important;
    
    /* 标准属性 */
    color-adjust: exact !important;
    
    /* Firefox */
    print-color-adjust: exact !important;
  }
}
```

### 7.2 灰度打印

```css
@media print {
  /* 强制灰度 */
  body {
    filter: grayscale(100%);
  }
  
  /* 或选择性灰度 */
  .grayscale-print {
    filter: grayscale(100%);
  }
}
```

**⚠️ 注意：** 某些浏览器或打印机驱动可能忽略CSS滤镜，特别是当用户启用"彩色打印"时。

### 7.3 优化颜色打印

```css
@media print {
  /* 移除阴影效果 */
  * {
    box-shadow: none !important;
    text-shadow: none !important;
  }
  
  /* 确保文字对比度 */
  body {
    color: #000 !important;
    background: #fff !important;
  }
  
  /* 链接颜色 */
  a {
    color: #000 !important;
    text-decoration: underline;
  }
}
```

### 7.4 背景色替代方案

由于背景色打印不可靠，建议使用边框替代：

```css
/* 屏幕样式 */
.highlight {
  background-color: yellow;
  padding: 2px 4px;
}

/* 打印样式 */
@media print {
  .highlight {
    background-color: transparent;
    border: 1px solid #000;
    padding: 2px 4px;
  }
}
```

---

## 八、图片处理

### 8.1 图片尺寸控制

```css
@media print {
  img {
    max-width: 100% !important;  /* 防止图片溢出 */
    height: auto !important;      /* 保持宽高比 */
  }
  
  /* 特定图片尺寸限制 */
  .print-logo {
    max-width: 5cm;
    max-height: 2cm;
  }
  
  /* 隐藏装饰性图片 */
  .decorative-img {
    display: none;
  }
}
```

### 8.2 图片分辨率

```css
@media print {
  /* 高DPI屏幕图片优化 */
  img {
    image-resolution: 300dpi;  /* 设置打印分辨率 */
  }
}
```

### 8.3 图片分页控制

```css
@media print {
  figure, .image-container {
    page-break-inside: avoid;  /* 避免图片被分割 */
    break-inside: avoid;
  }
  
  /* 大图单独一页 */
  .full-page-image {
    page-break-before: always;
    page-break-after: always;
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
}
```

### 8.4 背景图片处理

```css
@media print {
  /* 打印背景图片 */
  .with-bg-image {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    background-image: url('image.jpg');
    background-size: cover;
  }
  
  /* 移除背景图片 */
  .no-bg-print {
    background-image: none !important;
  }
}
```

---

## 九、表格打印

### 9.1 基础表格样式

```css
@media print {
  table {
    width: 100%;
    border-collapse: collapse;  /* 必须设置 */
    page-break-inside: auto;
  }
  
  thead {
    display: table-header-group;  /* 每页重复表头 */
  }
  
  tfoot {
    display: table-footer-group;  /* 每页重复表尾 */
  }
  
  tr {
    page-break-inside: avoid;     /* 避免行被分割 */
    break-inside: avoid;
  }
  
  th, td {
    border: 1px solid #000;
    padding: 4px 8px;
    text-align: left;
  }
  
  th {
    background-color: #f0f0f0;    /* 需要配合 print-color-adjust */
    font-weight: bold;
  }
}
```

### 9.2 复杂表格处理

```css
@media print {
  /* 宽表格横向打印 */
  .wide-table {
    page: landscape;
  }
  
  @page landscape {
    size: A4 landscape;
  }
  
  /* 表格容器 */
  .table-wrapper {
    overflow-x: visible;
  }
  
  /* 防止表格跨页时出现问题 */
  tbody tr:last-child {
    page-break-after: avoid;
  }
}
```

### 9.3 表格分页优化

```css
@media print {
  /* 确保表头在新页面重复 */
  thead {
    display: table-header-group;
  }
  
  /* 长表格优化 */
  .long-table {
    page-break-inside: auto;
  }
  
  .long-table tr {
    page-break-inside: avoid;
  }
  
  /* 表格标题行不分割 */
  .long-table th {
    page-break-inside: avoid;
  }
}
```

---

## 十、页眉页脚

### 10.1 使用 @page 边距区域（Chromium支持）

```css
@page {
  margin: 2cm 1.5cm;
  
  @top-center {
    content: "文档标题";
    font-size: 10pt;
    border-bottom: 0.5pt solid #000;
    padding-bottom: 5pt;
  }
  
  @bottom-center {
    content: "第 " counter(page) " 页，共 " counter(pages) " 页";
    font-size: 9pt;
  }
}

/* 首页不同样式 */
@page :first {
  @top-center {
    content: none;  /* 首页不显示页眉 */
  }
}
```

### 10.2 使用固定定位（通用方案）

```css
@media print {
  /* 页眉 */
  .print-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 2cm;
    text-align: center;
    font-size: 10pt;
    border-bottom: 1px solid #ccc;
  }
  
  /* 页脚 */
  .print-footer {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 1.5cm;
    text-align: center;
    font-size: 9pt;
    border-top: 1px solid #ccc;
  }
  
  /* 为页眉页脚留出空间 */
  body {
    margin-top: 2.5cm;
    margin-bottom: 2cm;
  }
}
```

### 10.3 使用表格实现重复页眉页脚

```html
<table>
  <thead>
    <tr>
      <td>
        <div class="header-content">
          <h2>公司Logo</h2>
          <hr>
        </div>
      </td>
    </tr>
  </thead>
  <tfoot>
    <tr>
      <td>
        <div class="footer-content">
          <hr>
          <p>页脚内容</p>
        </div>
      </td>
    </tr>
  </tfoot>
  <tbody>
    <tr>
      <td>
        <!-- 主要内容 -->
      </td>
    </tr>
  </tbody>
</table>
```

```css
@media print {
  table {
    width: 100%;
    border-collapse: collapse;
  }
  
  thead {
    display: table-header-group;  /* 每页重复 */
  }
  
  tfoot {
    display: table-footer-group;  /* 每页重复 */
  }
  
  /* 隐藏实际的thead/tfoot内容，只用于占位 */
  thead td, tfoot td {
    padding: 0;
  }
}
```

### 10.4 页码计数器

```css
@page {
  @bottom-center {
    content: counter(page);
  }
}

/* 从特定数字开始计数 */
@page {
  counter-reset: page 10;  /* 从第10页开始 */
}
```

---

## 十一、浏览器兼容性

### 11.1 主要特性支持情况

| 特性 | Chrome | Firefox | Safari | Edge | IE |
|------|--------|---------|--------|------|-----|
| `@media print` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `@page` | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| `@page :first` | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| `@page :left/:right` | ✅ | ✅ | ⚠️ | ✅ | ❌ |
| 边距区域 (@top-left等) | ✅ | ❌ | ❌ | ✅ | ❌ |
| `page-break-*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `break-*` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `widows/orphans` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `print-color-adjust` | ✅ | ✅ | ✅ | ✅ | ❌ |
| `counter(page)` | ✅ | ❌ | ❌ | ✅ | ❌ |

### 11.2 兼容性处理方案

```css
@media print {
  /* 同时使用新旧属性 */
  .no-break {
    page-break-inside: avoid;
    break-inside: avoid;
  }
  
  /* 背景色打印 */
  * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    color-adjust: exact;
  }
}
```

### 11.3 IE兼容性处理

```css
@media print {
  /* IE使用传统属性 */
  table {
    border-collapse: collapse;
    page-break-inside: auto;
  }
  
  tr {
    page-break-inside: avoid;
  }
  
  /* IE不支持 @page，使用body边距 */
  body {
    margin: 2cm;
  }
}
```

---

## 十二、常见错误与陷阱

### 12.1 ❌ 错误1：使用 body 边距代替 @page

```css
/* ❌ 错误：body边距在打印时可能被忽略 */
body {
  margin: 2cm;
}

/* ✅ 正确：使用 @page 设置页边距 */
@page {
  margin: 2cm;
}
```

### 12.2 ❌ 错误2：使用 px 作为打印字体单位

```css
/* ❌ 错误：px在打印时不一致 */
body {
  font-size: 16px;
}

/* ✅ 正确：使用 pt */
body {
  font-size: 12pt;
}
```

### 12.3 ❌ 错误3：忘记设置 border-collapse

```css
/* ❌ 错误：表格行分页控制不生效 */
table {
  page-break-inside: avoid;
}

/* ✅ 正确：必须设置 border-collapse */
table {
  border-collapse: collapse;
  page-break-inside: auto;
}

tr {
  page-break-inside: avoid;
}
```

### 12.4 ❌ 错误4：背景色/背景图不显示

```css
/* ❌ 错误：背景色默认不打印 */
.highlight {
  background-color: yellow;
}

/* ✅ 正确：强制打印背景 */
@media print {
  * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
}
```

### 12.5 ❌ 错误5：图片溢出页面

```css
/* ❌ 错误：图片可能超出页面 */
img {
  width: 100%;
}

/* ✅ 正确：限制最大宽度 */
@media print {
  img {
    max-width: 100% !important;
    height: auto !important;
  }
}
```

### 12.6 ❌ 错误6：flex/grid布局分页问题

```css
/* ❌ 错误：flex容器内部分页可能有问题 */
.container {
  display: flex;
  flex-direction: column;
}

/* ✅ 正确：为子元素设置分页控制 */
@media print {
  .container {
    display: block;  /* 打印时改为块级布局 */
  }
  
  .container > * {
    page-break-inside: avoid;
  }
}
```

### 12.7 ❌ 错误7：忘记隐藏交互元素

```css
/* ❌ 错误：打印时显示按钮 */
<button>提交</button>

/* ✅ 正确：隐藏交互元素 */
@media print {
  button, .btn, input[type="submit"] {
    display: none !important;
  }
}
```

### 12.8 ❌ 错误8：页眉页脚覆盖内容

```css
/* ❌ 错误：固定定位元素可能覆盖内容 */
.header {
  position: fixed;
  top: 0;
}

/* ✅ 正确：为内容留出空间 */
@media print {
  @page {
    margin-top: 3cm;  /* 为页眉留出空间 */
  }
  
  .header {
    position: fixed;
    top: 0;
    height: 2cm;
  }
}
```

### 12.9 ❌ 错误9：链接不可见

```css
/* ❌ 错误：链接在打印时可能看不见 */
a {
  color: blue;
}

/* ✅ 正确：确保链接可见 */
@media print {
  a {
    color: #000;
    text-decoration: underline;
  }
  
  a[href]::after {
    content: " (" attr(href) ")";
  }
}
```

### 12.10 ❌ 错误10：空白页问题

```css
/* ❌ 错误：可能导致空白页 */
html, body {
  height: 100%;
}

/* ✅ 正确：重置高度 */
@media print {
  html, body {
    height: auto;
    margin: 0;
    padding: 0;
  }
}
```

---

## 十三、最佳实践

### 13.1 文件组织

推荐将打印样式单独放在文件中：

```html
<!-- 屏幕样式 -->
<link rel="stylesheet" href="screen.css" media="screen">

<!-- 打印样式 -->
<link rel="stylesheet" href="print.css" media="print">

<!-- 通用样式 -->
<link rel="stylesheet" href="common.css" media="all">
```

### 13.2 打印样式模板

```css
/* print.css - 完整打印样式模板 */

/* ========== 基础设置 ========== */
@page {
  margin: 2cm 1.5cm;
  size: A4;
}

@page :first {
  margin-top: 3cm;
}

/* ========== 隐藏元素 ========== */
@media print {
  nav, header, footer, aside,
  .ads, .sidebar, .no-print,
  button, input[type="submit"],
  .breadcrumb, .share-buttons {
    display: none !important;
  }
  
  /* ========== 基础样式 ========== */
  * {
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    box-shadow: none !important;
    text-shadow: none !important;
  }
  
  body {
    font-family: "Times New Roman", Georgia, serif;
    font-size: 12pt;
    line-height: 1.5;
    color: #000;
    background: #fff;
  }
  
  /* ========== 布局 ========== */
  .container {
    width: 100%;
    margin: 0;
    padding: 0;
  }
  
  /* ========== 标题 ========== */
  h1, h2, h3, h4, h5, h6 {
    page-break-after: avoid;
    break-after: avoid;
    color: #000;
  }
  
  h1 { font-size: 18pt; }
  h2 { font-size: 16pt; }
  h3 { font-size: 14pt; }
  
  /* ========== 段落 ========== */
  p {
    orphans: 3;
    widows: 3;
    margin-bottom: 0.5em;
  }
  
  /* ========== 链接 ========== */
  a {
    color: #000;
    text-decoration: underline;
  }
  
  a[href]::after {
    content: " (" attr(href) ")";
    font-size: 90%;
  }
  
  /* ========== 图片 ========== */
  img {
    max-width: 100% !important;
    height: auto !important;
    page-break-inside: avoid;
    break-inside: avoid;
  }
  
  /* ========== 表格 ========== */
  table {
    width: 100%;
    border-collapse: collapse;
    page-break-inside: auto;
  }
  
  thead {
    display: table-header-group;
  }
  
  tr {
    page-break-inside: avoid;
    break-inside: avoid;
  }
  
  th, td {
    border: 1px solid #000;
    padding: 4px 8px;
  }
  
  /* ========== 列表 ========== */
  ul, ol {
    margin-left: 2em;
  }
  
  li {
    page-break-inside: avoid;
    break-inside: avoid;
  }
  
  /* ========== 代码块 ========== */
  pre, code {
    font-family: "Courier New", monospace;
    font-size: 10pt;
    page-break-inside: avoid;
    break-inside: avoid;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  
  /* ========== 分页控制 ========== */
  .page-break {
    page-break-before: always;
    break-before: page;
  }
  
  .no-break {
    page-break-inside: avoid;
    break-inside: avoid;
  }
  
  /* ========== 打印专用元素 ========== */
  .print-only {
    display: block;
  }
}

@media screen {
  .print-only {
    display: none;
  }
}
```

### 13.3 实用类命名规范

```css
/* 控制显示 */
.no-print      /* 打印时隐藏 */
.print-only    /* 仅打印时显示 */
.screen-only   /* 仅屏幕显示 */

/* 分页控制 */
.page-break        /* 强制分页 */
.no-break          /* 避免分页 */
.keep-together     /* 保持在一起 */

/* 打印优化 */
.print-grayscale   /* 灰度打印 */
.print-landscape   /* 横向打印 */
.print-portrait    /* 纵向打印 */
```

### 13.4 JavaScript打印优化

```javascript
// 打印前准备
function preparePrint() {
  // 添加打印类
  document.body.classList.add('printing');
  
  // 可以在这里动态修改内容
  updatePrintContent();
  
  // 触发打印
  window.print();
  
  // 打印后清理
  setTimeout(() => {
    document.body.classList.remove('printing');
    restoreContent();
  }, 100);
}

// 打印特定区域
function printElement(elementId) {
  const element = document.getElementById(elementId);
  const originalContent = document.body.innerHTML;
  
  document.body.innerHTML = element.innerHTML;
  window.print();
  document.body.innerHTML = originalContent;
}

// 监听打印事件
window.addEventListener('beforeprint', () => {
  console.log('准备打印...');
  // 执行打印前操作
});

window.addEventListener('afterprint', () => {
  console.log('打印完成');
  // 执行打印后清理
});
```

---

## 十四、调试技巧

### 14.1 使用浏览器开发者工具

**Chrome/Edge：**
1. 打开开发者工具（F12）
2. 按 `Ctrl+Shift+P` 打开命令面板
3. 输入 "Rendering" 并选择 "Show Rendering"
4. 勾选 "Emulate CSS media type" 并选择 "print"

**Firefox：**
1. 打开开发者工具
2. 点击设置齿轮图标
3. 在 "Available Toolbox Buttons" 中启用 "Toggle print media simulation"

### 14.2 打印预览调试

```css
/* 开发时临时样式 */
@media print {
  /* 显示边框帮助调试布局 */
  * {
    outline: 1px solid red !important;
  }
  
  /* 显示分页位置 */
  .page-break {
    border-top: 2px dashed blue;
    margin-top: 10px;
  }
  
  /* 显示元素尺寸 */
  body::before {
    content: "页面尺寸: A4";
    position: fixed;
    top: 0;
    right: 0;
    background: yellow;
    padding: 5px;
    font-size: 10pt;
  }
}
```

### 14.3 常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 背景色不显示 | 浏览器默认禁用 | 使用 `print-color-adjust: exact` |
| 表格行被分割 | 未设置 `border-collapse` | 添加 `border-collapse: collapse` |
| 内容紧贴边缘 | 未使用 `@page` | 使用 `@page { margin: 2cm; }` |
| 字体太小 | 使用了 px 单位 | 改用 pt 单位 |
| 图片溢出 | 未限制最大宽度 | 设置 `max-width: 100%` |
| 出现空白页 | 高度设置问题 | 重置 `html, body { height: auto; }` |
| 页眉不重复 | 浏览器不支持 | 使用表格方案替代 |

### 14.4 跨浏览器测试清单

- [ ] Chrome/Edge 打印预览
- [ ] Firefox 打印预览
- [ ] Safari 打印预览（Mac）
- [ ] 实际打印测试
- [ ] 导出PDF测试
- [ ] 不同纸张尺寸（A4, Letter）
- [ ] 横向/纵向打印
- [ ] 灰度打印测试

### 14.5 打印测试页面

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>打印测试页面</title>
  <style>
    @page {
      margin: 2cm;
      size: A4;
    }
    
    @media print {
      * {
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
      }
      
      .test-section {
        page-break-inside: avoid;
        margin-bottom: 1cm;
        padding: 1cm;
        border: 1px solid #000;
      }
      
      .color-test {
        background-color: #ffeb3b;
        padding: 10px;
      }
      
      table {
        width: 100%;
        border-collapse: collapse;
        margin: 1cm 0;
      }
      
      th, td {
        border: 1px solid #000;
        padding: 8px;
      }
    }
  </style>
</head>
<body>
  <h1>打印测试页面</h1>
  
  <div class="test-section">
    <h2>1. 颜色测试</h2>
    <div class="color-test">这段文字应该有黄色背景</div>
  </div>
  
  <div class="test-section">
    <h2>2. 表格测试</h2>
    <table>
      <thead>
        <tr><th>列1</th><th>列2</th><th>列3</th></tr>
      </thead>
      <tbody>
        <tr><td>数据1</td><td>数据2</td><td>数据3</td></tr>
        <tr><td>数据4</td><td>数据5</td><td>数据6</td></tr>
      </tbody>
    </table>
  </div>
  
  <div class="test-section">
    <h2>3. 分页测试</h2>
    <p>这是一段很长的文本，用于测试分页行为...</p>
  </div>
  
  <button onclick="window.print()">打印测试</button>
</body>
</html>
```

---

## 附录：快速参考表

### CSS打印属性速查

| 属性 | 值 | 说明 |
|------|-----|------|
| `size` | `A4`, `A5`, `Letter`, `landscape`, `portrait` | 页面尺寸和方向 |
| `margin` | `2cm`, `1in` | 页边距 |
| `page-break-before` | `always`, `avoid`, `auto` | 元素前分页 |
| `page-break-after` | `always`, `avoid`, `auto` | 元素后分页 |
| `page-break-inside` | `avoid`, `auto` | 元素内部分页 |
| `break-before` | `page`, `avoid` | 现代分页属性 |
| `break-after` | `page`, `avoid` | 现代分页属性 |
| `break-inside` | `avoid`, `auto` | 现代分页属性 |
| `widows` | `2`, `3` | 段落顶部最小行数 |
| `orphans` | `2`, `3` | 段落底部最小行数 |
| `print-color-adjust` | `exact`, `economy` | 颜色打印控制 |

### 单位换算表

| 单位 | 换算 | 适用场景 |
|------|------|----------|
| 1in | = 96px = 2.54cm | 英制打印 |
| 1cm | = 37.8px | 公制打印 |
| 1mm | = 3.78px | 精确打印 |
| 1pt | = 1.33px = 1/72in | 字体大小 |
| 1pc | = 16px = 12pt | 排版 |

---

**文档版本：** 1.0  
**最后更新：** 2025年  
**许可证：** MIT

---

> 💡 **提示：** 打印样式的开发需要反复测试和调整。建议在实际打印前，使用多种浏览器的打印预览功能进行全面测试。
