#!/bin/bash -ue

# you need to run this script as root
if [[ "$(id -u)" != 0 ]]; then
    set -x
    exec sudo "$0"
fi

user=brew
gid=12 # everyone=12

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
    dscl . create "/Users/$user" RealName "Homebrew"
    uid=$(alloc_uid)
    dscl . create "/Users/$user" UniqueID "$uid"
    dscl . create "/Users/$user" PrimaryGroupID "$gid"
    dscl . create "/Users/$user" NFSHomeDirectory /opt/homebrew/Cellar
    dscl . create "/Users/$user" IsHidden 1

    echo "[+] Created User: $user (uid=$uid gid=$gid)"
fi

# populate /opt/homebrew
echo "[+] Creating and setting permissions on directories in /opt/homebrew"
dirs=(bin Caskroom Cellar etc Frameworks Homebrew include lib opt sbin share var)
mkdir -p /opt/homebrew
cd /opt/homebrew
for dir in "${dirs[@]}"; do
    mkdir -p "$dir"
    chown brew:staff "$dir"
    chmod 755 "$dir"
done

# install homebrew
echo "[+] Installing homebrew to /opt/homebrew/Cellar"
curl -L https://github.com/Homebrew/brew/tarball/master | tar xz --strip 1 -C Homebrew
ln -fs ../Homebrew/bin/brew bin/brew
chown -R "$user":"$gid" Homebrew bin/brew

# set up sudobrew
echo "[+] Creating /opt/sudobrew"
mkdir -p /opt
if [[ -e /opt/sudobrew ]]; then
    chflags noschg /opt/sudobrew
    rm -f /opt/sudobrew
fi
echo '#!/bin/sh
cd /
export EDITOR=vim
export HOME=/tmp
export HOMEBREW_NO_ANALYTICS=1
exec sudo -E -u brew /opt/homebrew/bin/brew "$@"
' > /opt/sudobrew
chown root:staff /opt/sudobrew
chmod 555 /opt/sudobrew
chflags schg /opt/sudobrew
mkdir -p /opt/homebrew/sudobin
ln -fs /opt/sudobrew /opt/local/sudobin/brew

# set up visudo
tmpdir=$(mktemp -d)
cd "$tmpdir"
cp /etc/sudoers .
sed -i.bak -e '/\/opt\/sudobrew/d' sudoers
remove_trailing_lines sudoers
echo >> sudoers
echo "$SUDO_USER ALL=NOPASSWD: /opt/sudobrew *" >> sudoers
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
        sed -i '' -e '/^brew() {/d' "$profile"
        remove_trailing_lines "$profile"
        echo >> "$profile"
    else
        touch "$profile"
        chown "$SUDO_UID:$SUDO_GID" "$profile"
    fi
    echo 'brew() { sudo /opt/sudobrew "$@"; }; export PATH="/opt/homebrew/sudobin:/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"' >> "$profile"
}
setup_profile .bash_profile
setup_profile .zprofile

# xcode-select --install
# xcodebuild -license accept
