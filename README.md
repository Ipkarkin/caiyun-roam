# Caiyun Roam

Home Assistant 自定义集成：**彩云天气（Caiyun）跟随手机 GPS 位置**。

内置的 `colorfulclouds` 集成坐标是写死的，离家后仍然只报屋企天气。本集成每 5 分钟读取
`device_tracker` / `person` 实体的 GPS 坐标，实时拉该坐标的彩云 v2.5 数据，
产出同 `colorfulclouds` 一样格式的 `weather` 实体（含 `forecast_keypoint`、
`forecast_minutely`、`forecast_probability`、`forecast_alert`、AQI 等属性），
可直接复用同一套落雨 / 概率 / 气象预警推送自动化。

## 安装

HACS → 自定义仓库 → `talosip/caiyun-roam` → Integration → 下载 → 重启 HA。

## 配置

设置 → 设备与服务 → 添加集成 → 搜索 `Caiyun Roam`：

| 字段 | 说明 |
|---|---|
| API Key | 彩云开放平台 token（https://dashboard.caiyunapp.com 注册，免费 1000 次/天） |
| Tracker | 要跟随的设备（`device_tracker.xxx` 或 `person.xxx`） |
| Name | 实体名称 |
| Interval | 轮询间隔（分钟，默认 5，最低 1） |

选项（集成 → 配置）可随时改 API Key / Tracker / 间隔。

## 属性

- `forecast_keypoint` —— 彩云一句话提示（如「10分钟后开始下雨，记得带伞」）
- `forecast_minutely` —— 分钟级降水描述
- `forecast_probability` —— 未来 2 小时每 30 分钟降雨概率（0~100）
- `forecast_alert` —— 气象预警（content 列表）
- `aqi` / `aqi_description` / `pm25` / `pm10` / `o3` / `no2` / `so2` / `co`
- `latitude` / `longitude` —— 本次实际使用的坐标

## 备注

免费 token 有滑动窗口限频，间隔不建议低于 5 分钟。
