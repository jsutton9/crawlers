SETUP

This project is written in Python 2.7 and depends on the Python Tkinter package. It has only been tested on Ubuntu 14.04, but the OS interaction is pretty limited, so it is likely to work on other platforms.

The program may been run with a command of this form:

python evolve.py [CONFIG]

where CONFIG specifies an optional plaintext configuration file.

~~~~~~~~~~~~~~~~~~~~

CONFIGURATION

A configuration file specifies various parameters which affect the program. The .config files included include all parameters which may be specified. If any parameters were to be excluded, they would be set to some default values at the beginning of the evolve.py file. If the program is run without any configuration file, all of these default values will be used.

Notes on a few of these parameters:

run_time: This specifies how long, in seconds, the program is to run. However, if an output file is specified, the population is saved after every generation, so the program may be interrupted (e.g. with ctrl-c) without losing progress.

scoring_process_count: The physics simulation used for evaluation may be run with multiple threads. This parameter is included to prevent the program from monopolizing your processor.

rule_count, material_count: These parameters dictate the length of the genome. As the physics are the performance bottleneck, there is little cost to setting these values high. You should not set these values so that they are inconsistent with a saved population you use.

input_file, output_file: If the input_file is set and the file is present, a population will be loaded from this file. Otherwise, a new random population is generated. The population is written to the ouput file after every generation.
