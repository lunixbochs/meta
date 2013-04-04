meta
==========
contains two vague categories of code: utilities and snippets

* __utilities__: clever single-file solutions
  * autostrace: given a username and process name, will automatically strace+log matching processes
  * binsplit: splits a file into pieces based on the output of binwalk
  * dimmer: allows you to dim/undim monitors on Windows using hotkeys
  * hardlink: searches directories and suggests identical files to hardlink
  * macbinary: extracts a .zip, preserving \_\_MACOSX resource forks as MacBinary files
  * permute: builds chains of similar characters and permutes possible combinations.
  * pidrun: run an executable with a specified PID
  * repl: create a repl by passing arguments to an existing command
  * shotgun: quickly converts input to several formats
  * shotsum: run multiple checksums against input
  * tvsort: tries to automatically sort tv shows into an existing folder structure
  * vm: simplify managing and logging into a headless linux vmware instance

* __snippets__: batteries not included
  * python
     * netreg: wrapper around samba's remote registry access
     * singleton: metaclass implementing Singleton classes
     * tailcall: decorator allowing tail recursion without hitting python's max recursion depth
     * threadpool: decorator capable of transparently threading calls to one or more functions, with the ability to store the return values for consumption.
