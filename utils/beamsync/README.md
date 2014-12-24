beamsync
====

Disable BeamSync on OS X.

Building
----

    sh beamsync.m

Running
----

    ./beamsync


Running at Login
----

1. Update Program in `self.beamsync.disable.plist` to point to the compiled `beamsync` binary.
2. Place `self.beamsync.disable.plist` inside `~/Library/LaunchAgents`.
