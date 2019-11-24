brew_altuser
====

Installs Homebrew on macOS to a new user named "brew", sets up /opt/sudobrew as a passwordless sudo command to run the `brew` command as the "brew" user.

To use, run `./install_brew_altuser.sh`

### Extras

Run `chmod 750 "$HOME"` if you want to prevent homebrew builds from accessing your home directory.

If your shell isn't `zsh` or `bash`, you'll want to port this alias to your shell profile `brew() { sudo /opt/sudobrew "$@"; }` so you can run the `brew` command.

Casks that install apps to /Applications don't work, and will never work, as the `brew` user does not and should not have `sudo`. Figure something else out.
