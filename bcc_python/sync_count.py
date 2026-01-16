#!/usr/bin/python3

from __future__ import print_function
from bcc import BPF
from bcc.utils import printb

# define BPF program
prog = """
#include <uapi/linux/ptrace.h>

BPF_HASH(last);

int count_trace (struct pt_regs ctx) {
	u64 ts, *tsp, *cnt_ptr, delta, key_ts = 0, key_count = 1, counter = 0;

	// attempt to read stored count
	cnt_ptr = last.lookup(&key_count);
	if (cnt_ptr != NULL) {
		counter = *cnt_ptr;
	}
	counter++;
	last.update(&key_count, &counter);

	// attempt to read stored timestamp
	tsp = last.lookup(&key_ts);
	if (tsp != NULL) {
		delta = bpf_ktime_get_ns() - *tsp;
		if (delta < 1000000000) {
			// output if time is less than 1 second
			bpf_trace_printk("%d %d\\n", delta / 1000000, counter);
		}
		last.delete(&key_ts);
	}
	// update stored timestamp
	ts = bpf_ktime_get_ns();
	last.update(&key_ts, &ts);
	return 0;
}
"""

# load BPF program
b = BPF(text=prog)
b.attach_kprobe(event=b.get_syscall_fnname("sync"), fn_name="count_trace")
print("Tracing for quick sync's... Ctrl-C to end")

# format output
start = 0
while 1:
	try:
		(task, pid, cpu, flags, ts, msg) = b.trace_fields()
		if start == 0:
			start = ts
		ts = ts - start
		ms, count = msg.split(b" ")
		printb(b"At time %.2f s: multiple syncs detected, last %s ms ago, count %s" % (ts, ms, count))
	except KeyboardInterrupt:
		exit()
