# -*- coding: utf-8 -*-
"""
矢量 SVG 图标管理模块
包含全套现代精致 UI 矢量图标定义、SVG 文件持久化与 QIcon/QPixmap 动态加载器。
严格禁止 Emoji 字符。
"""
import os
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QByteArray, QSize
from PyQt6.QtSvg import QSvgRenderer

ICONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "resources", "icons"
)

# 基础 24x24 矢量 SVG 模板库 (使用 stroke-width="2" 或 fill 规范)
SVG_TEMPLATES = {
    # 核心对勾 (用于多选框、卡片选中标记与保存操作)
    "check": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.5 L9.5 17.5 L19.5 6.5"/>
</svg>''',

    # 粗对勾圆标 (用于卡片右上角已激活指示)
    "check_badge": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <circle cx="12" cy="12" r="11" fill="{color}"/>
  <path fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" d="M7 12 L10.5 15.5 L17 9"/>
</svg>''',

    # 侧边栏导航 0：工作台概览 (仪表盘 / 布局)
    "nav_dashboard": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <rect x="3" y="3" width="8" height="8" rx="2" fill="none" stroke="{color}" stroke-width="2"/>
  <rect x="13" y="3" width="8" height="5" rx="2" fill="none" stroke="{color}" stroke-width="2"/>
  <rect x="13" y="10" width="8" height="11" rx="2" fill="none" stroke="{color}" stroke-width="2"/>
  <rect x="3" y="13" width="8" height="8" rx="2" fill="none" stroke="{color}" stroke-width="2"/>
</svg>''',

    # 侧边栏导航 1：提醒时间与工作日 (闹钟 / 排班)
    "nav_schedule": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <circle cx="12" cy="13" r="8" fill="none" stroke="{color}" stroke-width="2"/>
  <polyline points="12,9 12,13 15,15" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <path d="M5 4 L2 7" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <path d="M19 4 L22 7" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>''',

    # 侧边栏导航 2：桌面挂件装扮 (猫咪耳朵 / 调色盘 / 装扮)
    "nav_pet": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M4 19 C4 13, 8 10, 12 10 C16 10, 20 13, 20 19" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M5 11 L3 4 L9 7" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
  <path d="M19 11 L21 4 L15 7" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
  <circle cx="9" cy="14" r="1.2" fill="{color}"/>
  <circle cx="15" cy="14" r="1.2" fill="{color}"/>
  <path d="M11 16.5 L12 17.5 L13 16.5" fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>
</svg>''',

    # 侧边栏导航 3：全屏提醒视觉 (显示屏 / 弹窗画面)
    "nav_popup": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <rect x="2" y="3" width="20" height="14" rx="2.5" fill="none" stroke="{color}" stroke-width="2"/>
  <line x1="8" y1="21" x2="16" y2="21" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="12" y1="17" x2="12" y2="21" stroke="{color}" stroke-width="2"/>
  <polygon points="10,7 15,10 10,13" fill="{color}"/>
</svg>''',

    # 侧边栏导航 4：系统与行为设置 (齿轮 / 控制滑块)
    "nav_system": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <circle cx="12" cy="12" r="3.2" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M19.4 15 a1.65 1.65 0 0 0 .33 1.82 l.06 .06 a2 2 0 0 1 -2.83 2.83 l-.06 -.06 a1.65 1.65 0 0 0 -1.82 -.33 1.65 1.65 0 0 0 -1 1.51 V21 a2 2 0 0 1 -4 0 v-.09 A1.65 1.65 0 0 0 9 19.4 a1.65 1.65 0 0 0 -1.82 .33 l-.06 .06 a2 2 0 0 1 -2.83 -2.83 l.06 -.06 a1.65 1.65 0 0 0 .33 -1.82 1.65 1.65 0 0 0 -1.51 -1 H3 a2 2 0 0 1 0 -4 h.09 A1.65 1.65 0 0 0 4.6 9 a1.65 1.65 0 0 0 -.33 -1.82 l-.06 -.06 a2 2 0 0 1 2.83 -2.83 l.06 .06 a1.65 1.65 0 0 0 1.82 .33 H9 a1.65 1.65 0 0 0 1 -1.51 V3 a2 2 0 0 1 4 0 v.09 a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82 -.33 l.06 -.06 a2 2 0 0 1 2.83 2.83 l-.06 .06 a1.65 1.65 0 0 0 -.33 1.82 V9 a1.65 1.65 0 0 0 1.51 1 H21 a2 2 0 0 1 0 4 h-.09 a1.65 1.65 0 0 0 -1.51 1 z" fill="none" stroke="{color}" stroke-width="2"/>
</svg>''',

    # 快捷操作：添加 (+ 号带圆环)
    "add_plus": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <circle cx="12" cy="12" r="9" fill="none" stroke="{color}" stroke-width="2"/>
  <line x1="12" y1="8" x2="12" y2="16" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="8" y1="12" x2="16" y2="12" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>''',

    # 快捷操作：删除 (垃圾桶 / 移除)
    "delete_trash": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <polyline points="3,6 5,6 21,6" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M19 6 v14 a2 2 0 0 1 -2 2 H7 a2 2 0 0 1 -2 -2 V6 m3 0 V4 a2 2 0 0 1 2 -2 h4 a2 2 0 0 1 2 2 v2" fill="none" stroke="{color}" stroke-width="2"/>
  <line x1="10" y1="11" x2="10" y2="17" stroke="{color}" stroke-width="2"/>
  <line x1="14" y1="11" x2="14" y2="17" stroke="{color}" stroke-width="2"/>
</svg>''',

    # 快捷操作：关闭 / 取消 (X 号)
    "close_x": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <line x1="18" y1="6" x2="6" y2="18" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="6" y1="6" x2="18" y2="18" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>
</svg>''',

    # 快捷操作：时钟 (精细表盘)
    "clock": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <circle cx="12" cy="12" r="9" fill="none" stroke="{color}" stroke-width="2"/>
  <polyline points="12,7 12,12 15.5,14" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>''',

    # 预设卡片：公文包 (标准工作日)
    "briefcase": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <rect x="2" y="7" width="20" height="14" rx="2" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M16 7 V5 a2 2 0 0 0 -2 -2 h-4 a2 2 0 0 0 -2 2 v2" fill="none" stroke="{color}" stroke-width="2"/>
  <line x1="2" y1="12" x2="22" y2="12" stroke="{color}" stroke-width="1.8"/>
  <rect x="10.5" y="10.5" width="3" height="3" rx="0.5" fill="{color}"/>
</svg>''',

    # 预设卡片：日历 (全天候)
    "calendar": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <rect x="3" y="4" width="18" height="18" rx="2" fill="none" stroke="{color}" stroke-width="2"/>
  <line x1="16" y1="2" x2="16" y2="6" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="8" y1="2" x2="8" y2="6" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="3" y1="10" x2="21" y2="10" stroke="{color}" stroke-width="2"/>
</svg>''',

    # 预设卡片：咖啡 (仅周末)
    "coffee": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M18 8 h1 a4 4 0 0 1 0 8 h-1" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M2 8 h16 v9 a4 4 0 0 1 -4 4 H6 a4 4 0 0 1 -4 -4 V8 z" fill="none" stroke="{color}" stroke-width="2"/>
  <line x1="6" y1="1" x2="6" y2="4" stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>
  <line x1="10" y1="1" x2="10" y2="4" stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>
  <line x1="14" y1="1" x2="14" y2="4" stroke="{color}" stroke-width="1.8" stroke-linecap="round"/>
</svg>''',

    # 测试与预览：眼睛 / 播放
    "test_play": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <polygon points="5,3 19,12 5,21" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
</svg>''',

    # 重置恢复：圆形撤销
    "reset_undo": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <polyline points="1,4 1,10 7,10" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M3.51 15 a9 9 0 1 0 2.13 -9.36 L1 10" fill="none" stroke="{color}" stroke-width="2"/>
</svg>''',

    # 守护盾牌 (常驻托盘状态徽章)
    "shield_check": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M9 12l2 2 4-4" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>''',

    # 开机启动：火箭
    "rocket": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z" fill="none" stroke="{color}" stroke-width="2"/>
</svg>''',

    # 提示音：扬声器音波
    "volume_bell": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M15.54 8.46a5 5 0 0 1 0 7.07" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <path d="M19.07 4.93a10 10 0 0 1 0 14.14" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>''',

    # 9 大装扮主题图标
    "theme_auto": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M12 2l2.4 5.6L20 10l-4.5 4.1L16.8 20 12 16.8 7.2 20l1.3-5.9L4 10l5.6-2.4z" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
</svg>''',

    "theme_morning": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M18 8h1a4 4 0 0 1 0 8h-1" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M6 2v3M10 2v3M14 2v3" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>''',

    "theme_noon": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" fill="none" stroke="{color}" stroke-width="2"/>
</svg>''',

    "theme_afternoon": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <circle cx="12" cy="12" r="9" fill="none" stroke="{color}" stroke-width="2"/>
  <polyline points="12 6 12 12 16 14" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>''',

    "theme_evening": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M4 4v16" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <path d="M4 4l15 6-15 6" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>
</svg>''',

    "theme_night": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M2 18h20" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M4 18c0-5 3.5-9 8-9s8 4 8 9" fill="none" stroke="{color}" stroke-width="2"/>
  <circle cx="12" cy="5" r="2" fill="{color}"/>
</svg>''',

    "theme_rain": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <path d="M23 12a11 11 0 0 0-22 0z" fill="none" stroke="{color}" stroke-width="2"/>
  <path d="M12 12v7a2 2 0 0 0 4 0" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <path d="M12 2v2" fill="none" stroke="{color}" stroke-width="2"/>
</svg>''',

    "theme_cold": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <line x1="12" y1="2" x2="12" y2="22" stroke="{color}" stroke-width="2"/>
  <line x1="3.5" y1="7" x2="20.5" y2="17" stroke="{color}" stroke-width="2"/>
  <line x1="3.5" y1="17" x2="20.5" y2="7" stroke="{color}" stroke-width="2"/>
  <circle cx="12" cy="12" r="3" fill="{color}"/>
</svg>''',

    "theme_hot": '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="{size}" height="{size}">
  <circle cx="12" cy="12" r="5" fill="none" stroke="{color}" stroke-width="2"/>
  <line x1="12" y1="1" x2="12" y2="3" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="12" y1="21" x2="12" y2="23" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="1" y1="12" x2="3" y2="12" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
  <line x1="21" y1="12" x2="23" y2="12" stroke="{color}" stroke-width="2" stroke-linecap="round"/>
</svg>'''
}

def ensure_icons_exported():
    """
    启动时确保核心图标已输出到 app/resources/icons 目录下
    以便 QSS 样式表 image: url(...) 可直接稳定加载
    """
    os.makedirs(ICONS_DIR, exist_ok=True)
    
    # 1. 导出复选框对勾 (纯白加粗)
    check_svg = get_svg_content("check", color="#FFFFFF", size=16)
    check_path = os.path.join(ICONS_DIR, "checkbox_check.svg")
    with open(check_path, "w", encoding="utf-8") as f:
        f.write(check_svg)

    # 导出高亮复选框对勾
    check_blue_svg = get_svg_content("check", color="#0284C7", size=16)
    check_blue_path = os.path.join(ICONS_DIR, "checkbox_check_blue.svg")
    with open(check_blue_path, "w", encoding="utf-8") as f:
        f.write(check_blue_svg)

def get_checkbox_check_path() -> str:
    """返回供 QSS 样式表引用的对勾 SVG 绝对路径 (以正斜杠格式)"""
    ensure_icons_exported()
    p = os.path.join(ICONS_DIR, "checkbox_check.svg")
    return p.replace("\\", "/")

def get_svg_content(name: str, color: str = "#0284C7", size: int = 24) -> str:
    """获取格式化后的 SVG XML 字符串"""
    template = SVG_TEMPLATES.get(name, SVG_TEMPLATES["check"])
    return template.format(color=color, size=size)

def get_svg_pixmap(name: str, color: str = "#0284C7", size: int = 24) -> QPixmap:
    """基于 QSvgRenderer 高清渲染出 QPixmap"""
    svg_str = get_svg_content(name, color=color, size=size)
    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
    
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    renderer.render(painter)
    painter.end()
    
    return pixmap

def get_svg_icon(name: str, color: str = "#0284C7", active_color: str = None, size: int = 20) -> QIcon:
    """生成具备常态与激活状态的矢量 QIcon"""
    icon = QIcon()
    
    # 正常态
    normal_pix = get_svg_pixmap(name, color=color, size=size)
    icon.addPixmap(normal_pix, QIcon.Mode.Normal, QIcon.State.Off)
    
    # 激活/选中态
    if active_color:
        active_pix = get_svg_pixmap(name, color=active_color, size=size)
        icon.addPixmap(active_pix, QIcon.Mode.Normal, QIcon.State.On)
        icon.addPixmap(active_pix, QIcon.Mode.Active, QIcon.State.Off)
    else:
        icon.addPixmap(normal_pix, QIcon.Mode.Normal, QIcon.State.On)
        
    return icon
