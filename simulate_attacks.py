import os
import ctypes

# 1. Buffer overflow simulation (trigger segfault)
def buffer_overflow_sim():
    libc = ctypes.CDLL(None)
    # This will cause a segfault
    try:
        ctypes.string_at(0)
    except:
        pass

# 2. Privilege escalation attempt
def priv_esc_attempt():
    # Try to access protected files
    files = ["/etc/shadow", "/root/.ssh/id_rsa", "/proc/kallsyms"]
    for f in files:
        try:
            with open(f, 'r') as fp:
                fp.read(10)
        except:
            pass

# 3. Process injection simulation
def process_injection_sim():
    import subprocess
    # Suspicious ptrace use
    subprocess.run(["strace", "-p", "1"], timeout=1)

if __name__ == "__main__":
    print("Simulating attacks...")
    buffer_overflow_sim()
    priv_esc_attempt()
    process_injection_sim()