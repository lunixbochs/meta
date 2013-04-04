#!/bin/bash -u

root="/Volumes/Nifty/VMware Fusion"
name="Ubuntu 64-bit"
hostname="ubuntu"
dir="/mnt/hgfs/Macintosh HD"
chdir="$dir/$(pwd)"
vm_path="$root/$name.vmwarevm/$name.vmx"

if which -s vmrun; then
    vmrun="vmrun"
else
    vmrun="/Applications/VMware Fusion.app/Contents/Library/vmrun"
fi

env="$(cat <<EOF
    export HOST_HOME="$HOME"
    [[ -d "$chdir" ]] && cd "$chdir" || echo "You should mount your host drive as '$dir' in the guest or edit this script."
EOF
)"

script="$(cat <<EOF
    $env
    bash --login
EOF
)"

function getpid {
    ps aux | grep -i "$name.vmwarevm" | grep vmware-vmx | awk '{print $2}'
}

function login {
    if [[ -n "$(getpid)" ]]; then
        if [[ $# -gt 1 ]]; then
            flags="$1"
            shift
            ssh -q "$hostname" -tt "$flags" "$env" $'\n' "$@"
        else
            ssh -q "$hostname" -tt "$@" "$script"
        fi
    fi
}

pid="$(getpid)"
if [[ $# -ge 1 ]]; then
    cmd="$1"
    shift
    case "$cmd" in
    -h|h|help|-help)
        echo "Usage: vm"
        echo "      x|x11 - connect with X forwarding"
        echo "      connect|login|ssh - open a shell"
        echo "      hup|kill|stop - kill the vm"
        echo "      vnc - open 'Chicken of the VNC' pointed at the vm console"
        echo "      status - print status"
    ;;
    x11|x)
        login -X "$@"
    ;;
    connect|login|ssh)
        login -- "$@"
    ;;
    hup|kill|stop)
        if [[ -z "$pid" ]]; then
            echo "Not running."
        else
            echo "Stopping..."
            kill -SIGHUP "$pid"
            exit 0
        fi
    ;;
    vnc)
        if [[ -z "$pid" ]]; then
            echo "Not running."
        else
            echo '' | nc localhost 5902 &>/dev/null
            if [[ $? -eq 0 ]]; then
                open -a chicken --args localhost:5902
                exit 0
            else
                echo "VNC doesn't seem to be open on localhost:5902"
                exit 2
            fi
        fi
    ;;
    status)
        echo -n "status: "
        if [[ -n "$pid" ]]; then
            echo "running (pid $pid)"
        else
            echo "stopped."
        fi
    ;;
    *)
    login -- "$cmd" "$@"
    ;;
    esac
elif [[ $# -eq 0 ]]; then
    if [[ -z "$pid" ]]; then
        echo "Starting... "
        $vmrun start "$vm_path" nogui
        for i in $(seq 1 10); do
            ping -c1 -t5 "$hostname" &>/dev/null && break
        done
        ping -c1 -t1 "$hostname" &>/dev/null
        if [[ $? -ne 0 ]]; then
            echo "timeout."
            exit 1
        fi
        sleep 3
        echo " done."
    fi
    login
fi

