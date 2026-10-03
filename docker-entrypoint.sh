#!/bin/bash
set -e

# Load I2C kernel module (needed for OLED)
modprobe i2c-dev 2>/dev/null || true

# Shutdown wrappers: use nsenter + force flags to bypass systemd chroot guard
# systemctl and shutdown are symlinks to systemctl which refuses to run in
# a container context. -f flag forces the raw kernel syscall.
#
# Each argument is matched as a whole token (not a substring of the full
# command line), so a "-c"/cancel request or a message argument that merely
# mentions "reboot"/"halt" can't be misread as a request to actually power
# off or reboot the host.
cat > /usr/local/bin/shutdown << 'WRAP'
#!/bin/bash
mode="poweroff"
for arg in "$@"; do
    case "$arg" in
        -c) exit 0 ;;  # nothing is ever scheduled, so there's nothing to cancel
        --help) echo "Usage: shutdown [-r|-h|-H|-P] [-c] [time] [message]"; exit 0 ;;
        -r|--reboot) mode="reboot" ;;
        -h|-H|-P|--poweroff|--halt) mode="poweroff" ;;
    esac
done
case "$mode" in
    reboot) exec nsenter -t 1 -a -- /sbin/reboot -f ;;
    *)      exec nsenter -t 1 -a -- /sbin/poweroff -f ;;
esac
WRAP
chmod +x /usr/local/bin/shutdown

for cmd in reboot poweroff halt; do
    case $cmd in
        reboot)   target="/sbin/reboot" ;;
        poweroff) target="/sbin/poweroff" ;;
        halt)     target="/sbin/halt" ;;
    esac
    printf '#!/bin/bash\nfor arg in "$@"; do [ "$arg" = "--help" ] && exit 0; done\nexec nsenter -t 1 -a -- %s -f "$@"\n' "$target" > "/usr/local/bin/$cmd"
    chmod +x "/usr/local/bin/$cmd"
done

# systemctl wrapper: translate shutdown commands, bypass chroot guard.
# Only the real systemctl power-management subcommands (first argument)
# are intercepted - e.g. "systemctl status reboot.target" passes through
# to the real systemctl untouched.
cat > /usr/local/bin/systemctl << 'SYSCTL'
#!/bin/bash
case "$1" in
    poweroff) exec nsenter -t 1 -a -- /sbin/poweroff -f ;;
    reboot)   exec nsenter -t 1 -a -- /sbin/reboot -f ;;
    halt)     exec nsenter -t 1 -a -- /sbin/halt -f ;;
    *)        exec /usr/bin/systemctl "$@" ;;
esac
SYSCTL
chmod +x /usr/local/bin/systemctl

# sudo wrapper: when the command being run under sudo is one of the
# wrappers above, drop the "sudo" and dispatch straight to it (it already
# knows how to tell reboot/poweroff/halt apart). Anything else - including
# "sudo <flags> shutdown ..." - falls through to the real sudo, matching
# the pironman5 NOPASSWD sudoers rule's plain "sudo <cmd> ..." form.
cat > /usr/local/bin/sudo << 'SUDO'
#!/bin/bash
case "$1" in
    shutdown|reboot|poweroff|halt|systemctl)
        cmd="$1"
        shift
        exec "/usr/local/bin/$cmd" "$@"
        ;;
    *)
        exec /usr/bin/sudo "$@"
        ;;
esac
SUDO
chmod +x /usr/local/bin/sudo

CONFIG_PATH="${CONFIG_PATH:-/data/config.json}"
mkdir -p "$(dirname "$CONFIG_PATH")"

exec /opt/pironman5/venv/bin/pironman5 --config-path "$CONFIG_PATH" start
