#!/bin/sh
# Preview the Qwen4 release fireworks on macOS and Linux: bash preview-release-animation.sh
cd "$(dirname "$0")" || exit 1
exec python3 qwen4_listener.py --celebrate
