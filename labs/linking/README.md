# 第 13–14 章：链接实验

适用环境：GNU/Linux、GCC/Clang、GNU \`ar\`，动态插桩演示需要支持 \`LD_PRELOAD\` 与 \`RTLD_NEXT\` 的 ELF 装载器。**不是生产级 malloc-hook 实现。**

## 13 静态归档与符号顺序

在仓库根目录：

\`\`\`sh
mkdir -p /tmp/csapp-linking
cc -std=c11 -Wall -Wextra -Werror -c labs/linking/main.c -o /tmp/csapp-linking/main.o
cc -std=c11 -Wall -Wextra -Werror -c labs/linking/add.c -o /tmp/csapp-linking/add.o
ar rcs /tmp/csapp-linking/libarith.a /tmp/csapp-linking/add.o
cc /tmp/csapp-linking/main.o /tmp/csapp-linking/libarith.a -o /tmp/csapp-linking/demo
/tmp/csapp-linking/demo
# 42
cc /tmp/csapp-linking/libarith.a /tmp/csapp-linking/main.o -o /tmp/csapp-linking/bad
# GNU ld 单次扫描模型下：undefined reference to sum2
\`\`\`

先思考为什么第二种顺序不能满足目标文件的未解析引用，再比较 \`nm -C\`、\`readelf -rW\` 与 \`objdump -dr\` 的输出。

## 14 动态库与 LD_PRELOAD

\`\`\`sh
cc -std=c11 -Wall -Wextra -Werror labs/linking/hello_puts.c -o /tmp/csapp-linking/hello_puts
cc -std=gnu11 -Wall -Wextra -Werror -fPIC -shared labs/linking/trace_puts.c -ldl -o /tmp/csapp-linking/libtraceputs.so
LD_PRELOAD=/tmp/csapp-linking/libtraceputs.so /tmp/csapp-linking/hello_puts
# stdout: hello
# stderr: [hook] puts called
\`\`\`

再用 \`readelf -dW\`、\`readelf -rW\`、\`LD_BIND_NOW=1\` 观察依赖和绑定时机。安全执行模式、静态链接与不同 libc 配置可能改变行为。

自动回归：\`python3 scripts/verify-linking.py\`。
