# FLAI
Philisense的AI代码库，FLAI，其中FL是flx（飞利信）的简写，AI是人工智能的简写，FLAI 读法与 Fly（飞翔）相同。
## 使用方法
### 添加环境变量
将FLAI的上一级目录添加到PYTHONPATH环境变量。
例如，我的目录结构为 /home/work/FLAI，则在~/.bashrc中添加如下一行：
```export PYTHONPATH=/home/work:$PYTHONPATH```
### 导入模块
例如我要使用detect_symbol下的databunch模块，则执行如下语句：
```from FLAI.detect_symbol.exp import databunch```
