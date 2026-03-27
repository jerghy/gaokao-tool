# 服务端图片分割功能 Spec

## Why
当前图片分割功能在前端使用 Canvas 裁剪图片生成 base64，存在以下问题：
1. 大量图片时内存占用高
2. 首次加载需要等待裁剪完成
3. base64 比原始文件大约 33%

通过将分割功能移到服务端，可以：
1. 减少前端内存占用
2. 提高加载速度（分割后的图片可缓存）
3. 分割后的图片可作为普通图片文件加载

## What Changes
- 后端新增图片分割 API 接口
- 分割后的图片保存到服务器临时目录
- 前端打印页面改为请求服务端分割后的图片 URL
- 添加分割图片缓存机制

## Impact
- Affected specs: image-split-lines
- Affected code: app.py, print.html

## ADDED Requirements

### Requirement: 服务端图片分割 API
系统 SHALL 提供服务端图片分割 API，接收图片路径和分割线数据，返回分割后的图片 URL 列表。

#### Scenario: 分割图片成功
- **WHEN** 前端发送图片分割请求，包含图片路径和分割线数据
- **THEN** 服务端返回分割后的图片 URL 列表

#### Scenario: 分割图片缓存命中
- **WHEN** 相同图片和分割线组合的请求再次发送
- **THEN** 服务端直接返回已缓存的分割图片 URL

### Requirement: 前端请求分割图片
前端打印页面 SHALL 在渲染时请求服务端分割图片，而不是在前端使用 Canvas 裁剪。

#### Scenario: 加载分割图片
- **WHEN** 打印页面渲染包含分割线的图片
- **THEN** 前端请求服务端分割 API 获取分割后的图片 URL

## MODIFIED Requirements

### Requirement: 打印页面图片分割
打印页面根据分割线正确分割图片，改为使用服务端分割后的图片 URL。

## REMOVED Requirements
无
