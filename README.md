## Dict2Anki
[![Build Status](https://travis-ci.org/megachweng/Dict2Anki.svg?branch=master)](https://travis-ci.org/megachweng/Dict2Anki)

> [Anki2.0版本插件](https://github.com/megachweng/Dict2Anki/releases/tag/v4.0) 不再维护

**Dict2Anki** 是一款方便[有道词典](http://cidian.youdao.com/multi.html)、[欧陆词典](https://www.eudic.net/)用户同步生成单词本卡片至[Anki](https://apps.ankiweb.net/#download)的插件

### Change log
* **sonyuncen's fork**: use Collins dictinary, change the note type.
* v6.0.0
    * 导入指定单词分组
    * 添加必应（bing）词典查询API
    * 添加待删除单词列表，可选择需要删除的 Anki 卡片
    * 恢复卡片 *短语字段*
    * 一些UI优化
    * 重构代码，解决上版本奔溃问题
    * 添加单元测试


### How to install
Anki --> 工具 --> 附加组件 --> 获取插件  
插件代码：1284759083

Move noteManager.py  and youdao.py to anddon folder. (c:\Users\\{account}\AppData\Roaming\Anki2\addons21\1284759083)

### Collins

<img src="screenshots/collins.png" alt="collins_screen" style="zoom: 80%;" />



### How to use
同步
<img src = "https://raw.githubusercontent.com/megachweng/Dict2Anki/master/screenshots/sync.gif"></span>

同步删除
<img src = "https://raw.githubusercontent.com/megachweng/Dict2Anki/master/screenshots/del.gif"></span>

### Contribute Guide
非常欢迎你的贡献，请PR前确保通过了全部单元测试 `pytest test`

### Development Guide
Python > 3.6  
```
export PYTHONPATH='xxx/Dict2Anki'  
export DEVDICT2ANKI=1  
pip install -r requirements.txt  
python __init__.py
```