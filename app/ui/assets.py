# -*- coding: utf-8 -*-
"""
视觉资源与图标生成模块
使用 QPainter 动态绘制矢量级清晰图标，无需依赖外部图片文件
"""
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QBrush, QLinearGradient, QFont
from PyQt6.QtCore import Qt, QPointF, QRectF

GRADIENT_PRESETS = {
    "sunset": {
        "name": "落日余晖 (Sunset)",
        "stops": [(0.0, "#FA709A"), (1.0, "#FEE140")],
        "desc": "活力温暖的橙红与明黄渐变"
    },
    "aurora": {
        "name": "极光梦境 (Aurora)",
        "stops": [(0.0, "#30CFD0"), (1.0, "#330867")],
        "desc": "深邃清新的青绿至幽蓝渐变"
    },
    "midnight": {
        "name": "午夜星空 (Midnight)",
        "stops": [(0.0, "#0F2027"), (0.5, "#203A43"), (1.0, "#2C5364")],
        "desc": "沉稳深邃的商务蓝黑渐变"
    },
    "ocean": {
        "name": "蔚蓝深海 (Ocean)",
        "stops": [(0.0, "#2E3192"), (1.0, "#1BFFFF")],
        "desc": "清澈透亮的深蓝与青蓝渐变"
    },
    "lavender": {
        "name": "薰衣草幻境 (Lavender)",
        "stops": [(0.0, "#667EEA"), (1.0, "#764BA2")],
        "desc": "优雅现代的靛紫梦幻渐变"
    }
}

def create_app_icon(size: int = 64) -> QIcon:
    """动态生成精致的现代托盘与窗口图标（时钟与下班落日主题）"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. 绘制圆角背景渐变卡片
    rect = QRectF(2, 2, size - 4, size - 4)
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#FF6B6B"))  # 珊瑚红
    gradient.setColorAt(1.0, QColor("#FFA07A"))  # 暖橙
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(rect, size * 0.28, size * 0.28)

    # 2. 绘制白色时钟圆盘轮廓
    center = QPointF(size / 2.0, size / 2.0)
    clock_radius = size * 0.32
    clock_pen = QPen(QColor(255, 255, 255, 230))
    clock_pen.setWidthF(max(2.0, size * 0.065))
    clock_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(clock_pen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 40)))
    painter.drawEllipse(center, clock_radius, clock_radius)

    # 3. 绘制时针与分针（指示 18:00 / 6点钟方向）
    # 分针指向上方 12 点
    minute_hand_pen = QPen(QColor(255, 255, 255, 240))
    minute_hand_pen.setWidthF(max(1.8, size * 0.055))
    minute_hand_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(minute_hand_pen)
    painter.drawLine(center, QPointF(center.x(), center.y() - clock_radius * 0.65))

    # 时针指向下方 6 点 (18:00)
    hour_hand_pen = QPen(QColor(255, 255, 255, 255))
    hour_hand_pen.setWidthF(max(2.2, size * 0.075))
    hour_hand_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(hour_hand_pen)
    painter.drawLine(center, QPointF(center.x(), center.y() + clock_radius * 0.5))

    # 中心小圆点
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor("#FFFFFF")))
    painter.drawEllipse(center, max(1.5, size * 0.05), max(1.5, size * 0.05))

    painter.end()

    icon = QIcon()
    icon.addPixmap(pixmap)
    return icon
