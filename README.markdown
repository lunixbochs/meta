meta
==========
contains two vague categories of code: utilities and snippets

* __utilities__: clever single-file solutions
  * autostrace: given a username and process name, will automatically strace+log matching processes
  * bitsplit: splits a file into pieces based on the output of binwalk
  * dimmer: allows you to dim/undim monitors on Windows using hotkeys
  * hardlink: searches directories and suggests identical files to hardlink
  * macbinary: extracts a .zip, preserving __MACOSX resource forks as MacBinary files
  * permute: builds chains of similar characters and permutes possible combinations.
  * pidrun: run an executable with a specified PID
  * shotgun: quickly and intelligently converts input to several formats
  * tvsort: tries to automatically sort tv shows into an existing folder structure

* __snippets__: batteries not included
  * python
     * netreg: wrapper around samba's remote registry access
     * singleton: metaclass implementing Singleton classes
     * tailcall: decorator allowing tail recursion without hitting python's max recursion depth
     * threadpool: decorator capable of transparently threading calls to one or more functions, with the ability to store the return values for consumption.
