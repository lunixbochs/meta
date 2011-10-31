#!/bin/bash -u
# given one or more directories, generates hardlink suggestions automatically
# based on file size and a quick md5 hashes of a distributed data samples

if [[ $# -lt 1 ]]; then
	echo "Usage: hardlink <dir> [dir...]"
	exit 1
fi

ref=""
matches=""

sample_count=5
sample_size=1024

# because we're 0-indexed
let sample_count--

uname="$(uname)"
case "$uname" in
	Linux)
		bytes='stat -c%s'
		md5='md5sum -b'
		;;
	Darwin)
		bytes='stat -f%z'
		md5='md5'
		;;
	*)
		echo "Unknown platform '$uname'."
		echo "Feel free to add functions for your platform and submit a patch"
	;;
esac

# <file> <start> <count>
function range {
	tail "-c+$2" "$1" | head "-c$3"
}

# <file> <filesize>
function sample {
	filesize="$2"

	i=0
	while ((i<=sample_count)); do
		start=$((filesize / sample_count * i))
		range "$1" "$start" "$sample_size"
		let i++
	done
}

# <file> <filesize> <hash>
function add {
	if [[ -n "$ref" ]]; then
		ref="$ref
$1"
	else
		ref="$1"
	fi
}

# <file>
function check {
	filesize=$($bytes "$1")
	hashed=$(sample "$1" "$filesize" | $md5 | awk {'print $1'})

	comp="$filesize $hashed"
	match="$(echo "$ref" | grep " $comp\$")"
	if [[ -n "$match" ]]; then
		echo "$1" "$match"
	else
		add "$1 $comp"
	fi
}

# <path>
function scan {
	for file in $(find "$1" -type f); do
		check "$file"
	done
}

# remove duplicates
scan "$(echo "$@" | tr ' ' '\n' | uniq | xargs)"

