#!/bin/bash
# Simulate normal user/system activities
for i in {1..100}; do
    ls -la /tmp
    cat /etc/passwd | head -5
    ps aux | grep -v grep
    sleep 0.1
done