# -*- coding: utf-8 -*-
"""
天气数据服务模块 (南京浦口区)
调用官方公开气象接口，采用后台异步线程获取，零阻塞 UI
"""
import json
import urllib.request
import threading
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

PUKOU_CITY_CODE = "101190107"  # 中国天气网/南京市浦口区编码

class WeatherService(QObject):
    weather_updated = pyqtSignal(dict)  # 信号：传递天气数据

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cached_weather = {
            "city": "南京浦口",
            "temp": "--℃",
            "type": "获取中",
            "high_low": "--",
            "text": "南京浦口 天气获取中..."
        }
        # 30 分钟刷新一次天气
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.fetch_weather_async)
        self.refresh_timer.start(1800000)

    def start(self):
        """启动时立即异步拉取一次天气"""
        self.fetch_weather_async()

    def fetch_weather_async(self):
        """后台异步线程拉取天气"""
        thread = threading.Thread(target=self._worker_fetch, daemon=True)
        thread.start()

    def _worker_fetch(self):
        # 优先使用 itboy 浦口区公开节点
        url = f"http://t.weather.itboy.net/api/weather/city/{PUKOU_CITY_CODE}"
        data = None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            data = None

        if data and data.get("status") == 200:
            try:
                wendu = data["data"]["wendu"]
                forecast0 = data["data"]["forecast"][0]
                w_type = forecast0["type"]
                high = forecast0["high"].replace("高温 ", "").replace("℃", "")
                low = forecast0["low"].replace("低温 ", "").replace("℃", "")
                result = {
                    "city": "南京浦口",
                    "temp": f"{wendu}℃",
                    "type": w_type,
                    "high_low": f"{low}~{high}℃",
                    "text": f"南京浦口 {w_type} {wendu}℃ ({low}~{high}℃)"
                }
                self.cached_weather = result
                self.weather_updated.emit(result)
                return
            except Exception:
                pass

        # 备用节点：wttr.in 浦口
        try:
            backup_url = "https://wttr.in/Pukou?format=j1"
            req = urllib.request.Request(backup_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                b_data = json.loads(resp.read().decode("utf-8"))
                current = b_data["current_condition"][0]
                temp = current.get("temp_C", "--")
                desc = current.get("lang_zh", [{}])[0].get("value", "晴")
                result = {
                    "city": "南京浦口",
                    "temp": f"{temp}℃",
                    "type": desc,
                    "high_low": "--",
                    "text": f"南京浦口 {desc} {temp}℃"
                }
                self.cached_weather = result
                self.weather_updated.emit(result)
                return
        except Exception:
            pass
