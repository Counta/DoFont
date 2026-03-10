# DoFont
一个将两字体合二为一以及将字体以对应规则对应替换的工具，用Python编写。

## 依赖
依赖文件写于Requirements.txt。
具体为 `fonttools 4.62.0` 

## 每个文件的作用？

### merge_fonts.py
这个文件定义了 `补丁字体` 和 `基底字体` ，补丁字体的字形会打在基底字体上，并替换基底字体对应码位的字形。
有一个TUI，引导你输入补丁字体和基底字体的路径，并输出内容。

### apply_mapping.py
这个文件允许你按照规则来替换字体对应字形的显示方法，使用了直接更改码位的方式让一个字直接映射到另一个字的显示上。
提供了规则模板文件，你可以参照模板写出自己的规则。
为了支持批量替换，支持了 `.*` 通配符。

## TODOs
1.为可变字重字体添加支持

2.尝试制作WebUI

## 致谢
[OpenCC](https://github.com/BYVoid/OpenCC) 原始项目替换表的基础来源

[TCFontCreator](https://github.com/GuiWonder/TCFontCreator) 这一替换字形的想法来源，项目当初只是为了为此添加批处理功能
