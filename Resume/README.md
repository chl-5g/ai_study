# 简历 LaTeX 项目

将简历维护为 `.tex` 源文件，通过 XeLaTeX 编译生成 PDF。

## 依赖安装

需要安装 XeLaTeX 和中文字体支持：

**macOS（推荐 MacTeX）：**

```bash
brew install --cask mactex
```

安装后重启终端，确认 `xelatex` 可用：

```bash
which xelatex
```

**Linux（Ubuntu/Debian）：**

```bash
sudo apt install texlive-xetex texlive-lang-chinese texlive-fonts-recommended
```

## 使用方法

### 单次编译

```bash
cd Resume/
python3 build_resume.py
```

编译成功后生成 `resume.pdf`，辅助文件（.aux, .log 等）会自动清理。

### 自动监控模式

```bash
python3 build_resume.py --watch
```

启动后会持续监控 `resume.tex`，每次保存文件后自动重新编译。按 `Ctrl+C` 退出。

## 文件说明

| 文件 | 说明 |
|------|------|
| `resume.tex` | 简历 LaTeX 源文件 |
| `build_resume.py` | 编译脚本（支持 --watch） |
| `resume.pdf` | 编译生成的 PDF |
