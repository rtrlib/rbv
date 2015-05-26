# util

## cli-validator

The REST BGP Validator requires a binary of the cli-validator tool provided by
the RTRlib, which has to be downloaded and compiled separately.

Get current RTRlib version from github

    $ git clone https://github.com/rtrlib/rtrlib.git

Compile RTRlib using cmake out-of-source build

    $ cd <path/to/rtrlib>
    $ mkdir release ; cd release
    $ cmake -DCMAKE_BUILD_TYPE=release ../

If any error is raised, please consult readme or build instructions of RTRlib.

Copy cli-validator binary to RBV

    $ cp tools/cli-validator <path/to/RBV>/src/util/.
