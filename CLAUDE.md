# 冶金平台 v2 编码规范

## 全局规则

- **禁止硬编码服务器地址/IP** — 外部链接统一用 `window.location.hostname` 动态构建，如 `` `http://${window.location.hostname}:8001` ``
