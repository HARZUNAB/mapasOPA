#!/bin/bash
gnome-terminal -- bash -c "echo '$1'; echo '$2'; scbulletin -d postgresql://sysop:sysop@localhost/seiscomp -E '$2'; exec bash"
