import os
import pipes
import requests
import subprocess
import sys

def clone(url, key=None):
    if key:
        p = subprocess.Popen(['ssh-agent', 'bash', '-c', 'ssh-add ' + pipes.quote(key) + ' &>/dev/null; git clone ' + pipes.quote(url)])
    else:
        p = subprocess.Popen(['git', 'clone', url])
    p.communicate()

def clone_all(org, username, token, key=None):
    url = 'https://api.github.com/orgs/{}/repos'.format(org)
    r = requests.get(url, auth=(username, token))
    for repo in r.json():
        clone(repo['ssh_url'], key)
        print

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage: %s <org> <username> [ssh key path]' % sys.argv[0]
        sys.exit(1)

    org = sys.argv[1]
    user = sys.argv[2]
    key = None
    if len(sys.argv) >= 4:
        key = sys.argv[3]

    token = raw_input('Access token: ')
    clone_all(org, user, token, key)
