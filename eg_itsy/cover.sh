#!/bin/sh

python -m coverage erase

python -m coverage run -a itsy.py goober
python -m coverage run -a itsy.py eg/bad.itsy 
python -m coverage run -a itsy.py eg/bad2.itsy 

python -m coverage run -a itsy.py eg/examples.itsy 
python -m coverage run -a itsy.py eg/ion.itsy 
python -m coverage run -a itsy.py eg/regex.itsy 
python -m coverage run -a itsy.py eg/superopt.itsy

python -m coverage report -m | grep -v /parson
