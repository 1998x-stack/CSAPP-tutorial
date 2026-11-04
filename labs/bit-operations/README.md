# 位表示与字段操作

运行 `lab_endianness` 输出本机对象字节序；运行 `lab_bit_math` 验证 32 位循环左移与字段提取。

学习要点：在 C 中，位移宽度不能等于或大于类型宽度。对无符号整数做循环移位，需先取 `count % 32` 并单独处理 `count=0`。字段掩码也要处理 `width=32` 的特殊情况。

验收：`ctest --test-dir .build/labs -R "bit_math|endian" --output-on-failure`。
