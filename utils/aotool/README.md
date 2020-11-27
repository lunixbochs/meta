aotool
====

Create and dump Rosetta 2 .aot assemblies (without using root or disabling SIP).

Building
----

    sh aotool.c

Usage
----

```
Usage: aotool -l <exe or dylib> <out.aot> # Dump an .aot for an existing x86_64 binary
       aotool -c <file.c> <out.aot>       # Compile a C file and dump the resulting .aot
       aotool -d <file.c>                 # Compile a C file and show both x86_64 and .aot arm64 disassembly.
```
