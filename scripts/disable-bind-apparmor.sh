set -x
if [ -f "/etc/apparmor.d/usr.sbin.named" ]; then
    mkdir -p /etc/apparmor.d/disable
    touch /etc/apparmor.d/disable/usr.sbin.named
    service apparmor restart
fi
