#!/bin/bash -ue

# you need to run this script as root
if [[ "$(id -u)" != 0 ]]; then
    set -x
    exec sudo "$0"
fi

user=port
gid=12 # everyone=12
njobs=$(getconf _NPROCESSORS_ONLN)

# finds the first unused uid
alloc_uid() {
    local n=502
    while id "$n" &>/dev/null; do
        let n++
    done
    echo "$n"
}

remove_trailing_lines() {
    sed -i.bak -e :a -e '/^\n*$/{$d;N;};/\n$/ba' "$1"
}

# create user
if id -u "$user" &>/dev/null; then
    echo "[-] User $user exists, skipping user creation"
else
    echo "[+] Creating User: $user"
    dscl . create "/Users/$user"
    dscl . create "/Users/$user" UserShell /usr/bin/false # /usr/bin/false prevents login
    dscl . create "/Users/$user" RealName "MacPorts"
    uid=$(alloc_uid)
    dscl . create "/Users/$user" UniqueID "$uid"
    dscl . create "/Users/$user" PrimaryGroupID "$gid"
    dscl . create "/Users/$user" NFSHomeDirectory /opt/local/var/macports/home
    dscl . create "/Users/$user" IsHidden 1

    echo "[+] Created User: $user (uid=$uid gid=$gid)"
fi

# populate /usr/local
echo "[+] Creating and setting permissions on directories in /opt/local"
mkdir -p /opt/local

# install macports
echo "[+] Installing macports to /opt/local"
cd "$(mktemp -d)"
curl -L https://github.com/macports/macports-base/releases/download/v2.7.1/MacPorts-2.7.1.tar.bz2 | tar xz --strip 1
./configure --prefix=/opt/local --with-install-user=port --with-install-group=everyone
make -j"$njobs"
make install
echo "+universal" >> /opt/local/etc/macports/variants.conf
chown -R "$user:everyone" /opt/local

# set up sudoport
echo "[+] Creating /opt/sudoport"
mkdir -p /opt
if [[ -e /opt/sudoport ]]; then
    chflags noschg /opt/sudoport
    rm -f /opt/sudoport
fi
echo '#!/bin/sh
cd /
export EDITOR=vim
export HOME=/tmp
exec sudo -E -u '"$user"' /opt/local/bin/port "$@"
' > /opt/sudoport
chown root:staff /opt/sudoport
chmod 555 /opt/sudoport
chflags schg /opt/sudoport

# set up visudo
tmpdir=$(mktemp -d)
cd "$tmpdir"
cp /etc/sudoers .
sed -i.bak -e '/\/opt\/sudoport/d' sudoers
remove_trailing_lines sudoers
echo >> sudoers
echo "$SUDO_USER ALL=NOPASSWD: /opt/sudoport *" >> sudoers
visudo -cf sudoers
cp sudoers /etc/sudoers
cd /
rm -rf "$tmpdir"

# set up .bash_profile and .zprofile
setup_profile() {
    local profile="$1"
    echo "[+] Update $profile"
    cd "$HOME"
    if [[ -e "$profile" ]]; then
        sed -i.bak -e '/port() {/d' "$profile"
        remove_trailing_lines "$profile"
        echo >> .bash_profile
    else
        touch "$profile"
        chown "$SUDO_UID:$SUDO_GID" "$profile"
    fi
    echo 'port() { sudo /opt/sudoport "$@"; }; export PATH="/opt/local/bin:/opt/local/sbin:$PATH"' >> "$profile"
}
setup_profile .bash_profile
setup_profile .zprofile

# xcode-select --install
# xcodebuild -license accept
