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
## 开发与贡献
### notebook设置`__package__`
当运行.ipynb文件时，python编译器认为它是主模块，即`__name__='main'`，它无父包，即`__package__=None`.
当一个模块的`__package__=None`时，无法使用相对引用，即如 `from ..exp import xx`
会报错。为了在notebook内使用相对引用，我们在每个.ipynb头部先设置`__package__`变量，使用如下代码:
```python
from pathlib import Path
d = Path('.').absolute()
__package__ = ''
while True:
    name = d.name
    __package__ = name+__package__
    if name=='FLAI':
        break
    else:
        __package__ = '.'+__package__
        d = d.parent
print(__package__)
```
关于python编译器对相对引用的处理方式，可以参见[该博客文章](https://vimiix.com/post/2017/12/29/import-
error-relative-no-parent/)。
