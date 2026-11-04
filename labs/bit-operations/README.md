# 字节表示实验

目标：通过 C 标准定义的对象表示方法观察本机字节序。

运行：`cc -std=c11 -Wall -Wextra -pedantic representation.c -o representation && ./representation`

预期：打印 `endianness=little`、`endianness=big` 或 `endianness=other`，具体由目标平台决定。

