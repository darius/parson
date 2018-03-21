#!/bin/bash

python -m coverage erase

for f in goober error_tests/bad*.itsy; do
    echo "Should fail:" ${f}
    python -m coverage run -a itsy.py ${f}
done

for f in eg/*.itsy; do
    echo "To C:" ${f}
    python -m coverage run -a itsy.py ${f}
done

python -m coverage report -m | grep -v /parson
