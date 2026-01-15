#!/usr/bin/python3

from bcc import BPF

# instead of r before the quotes, we can write \n as \\n
BPF(text=r'''
int kprobe__sys_clone(void *ctx) {
	bpf_trace_printk("Hello, World!\n");
	return 0;
}
''').trace_print()

"""
The lines appearing in your terminal indicate that the kernel is successfully running your C code. Let's break down one line:
b' chrome-1019836 [009] ...21 164697.714678: bpf_trace_printk: Hello, World!'

1. b'...': This indicates the output is a Python byte string.
2. chrome: The name of the process that triggered the event.
3. 1019836: The Process ID (PID).
4. [009]: The CPU core number the code ran on.
5. 164697.714678: The timestamp (uptime) of the event.
6. Hello, World!: Your custom message from the BPF program.
"""
