#!/usr/bin/env python3
from bcc import BPF
import csv
import time
import signal
import sys
from datetime import datetime

# =====================
# eBPF PROGRAM
# =====================
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

#ifdef __x86_64__
#define PT_REGS_SYSCALL_NR(ctx) ((ctx)->orig_ax)
#else
#error "Unsupported architecture"
#endif

struct data_t {
    u32 pid;
    u32 uid;
    u32 syscall;
    u64 timestamp;
    char comm[TASK_COMM_LEN];
};

BPF_PERF_OUTPUT(events);

int trace_syscall(struct pt_regs *ctx)
{
    struct data_t data = {};

    data.pid = bpf_get_current_pid_tgid() >> 32;
    data.uid = bpf_get_current_uid_gid();
    data.syscall = PT_REGS_SYSCALL_NR(ctx);
    data.timestamp = bpf_ktime_get_ns();
    bpf_get_current_comm(&data.comm, sizeof(data.comm));

    events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}
"""

# =====================
# LOAD BPF
# =====================
b = BPF(text=bpf_text)

# Attach to syscall entry point (architecture-specific)
b.attach_kprobe(event="__x64_sys_openat", fn_name="trace_syscall")
b.attach_kprobe(event="__x64_sys_execve", fn_name="trace_syscall")
b.attach_kprobe(event="__x64_sys_read", fn_name="trace_syscall")
b.attach_kprobe(event="__x64_sys_write", fn_name="trace_syscall")

# =====================
# CSV SETUP
# =====================
timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"syscall_trace_{timestamp_str}.csv"

csv_file = open(csv_filename, "w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow([
    "wall_time",
    "pid",
    "uid",
    "comm",
    "syscall_id",
    "syscall_name",
    "kernel_timestamp_ns"
])

# =====================
# EVENT HANDLER
# =====================
def handle_event(cpu, data, size):
    event = b["events"].event(data)

    try:
        syscall_name = BPF.get_syscall_fnname(event.syscall)
        syscall_name = syscall_name.replace("__x64_sys_", "")
    except Exception:
        syscall_name = "unknown"

    csv_writer.writerow([
        time.time(),
        event.pid,
        event.uid,
        event.comm.decode(errors="replace"),
        event.syscall,
        syscall_name,
        event.timestamp
    ])

# =====================
# CLEAN SHUTDOWN
# =====================
def shutdown(sig, frame):
    print("\nStopping collection...")
    csv_file.flush()
    csv_file.close()
    print(f"Saved to {csv_filename}")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

# =====================
# START
# =====================
b["events"].open_perf_buffer(handle_event)

print(f"Collecting syscalls → {csv_filename}")
print("Press Ctrl+C to stop")

while True:
    b.perf_buffer_poll()
