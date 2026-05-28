# 环境配置

本文件包含首次执行 trace-badcase-analyzer 时需要完成的环境检测和配置步骤。

> **何时读取此文件**：首次在新环境中执行本 skill 时读取。环境检测结果可在同一 session 内复用，无需重复执行。

---

## Python 路径检测

Windows 上 `python3` 通常不可用，需要自动探测可用的 Python 可执行路径：

```
1. 尝试 `python --version`，成功则用 `python`
2. 尝试 `python3 --version`，成功则用 `python3`
3. 均失败则搜索常见安装路径：
   - Windows: C:/Users/*/AppData/Local/Programs/Python/*/python.exe
   - macOS/Linux: /usr/local/bin/python3, /usr/bin/python3
4. 将检测到的 Python 可执行路径存为变量 $PYTHON_CMD，后续统一使用
```

## 路径规范

所有文件路径在 prompt 和脚本调用中统一使用正斜杠 `/`，避免 Windows `\` 在 shell 中被转义。例如：
- ✅ `C:/Users/Shihao/Desktop/traces/`
- ❌ `C:\Users\Shihao\Desktop\traces\`
