#!/bin/bash
# Automated test.

python -m coverage erase

for f in goober error_tests/bad*.itsy; do
    echo "Should fail:" ${f}
    python -m coverage run --source=. -a itsy.py ${f}
done

for f in eg/*.itsy; do
    echo
    echo "To C:" ${f}
    python -m coverage run --source=. -a itsy.py ${f}
    fc=${f%.*}.c
    if test -f ${fc}.ref; then
        diff -u ${fc}.ref ${fc}
        # TODO raise error at exit if there was a diff
    else
        echo '  (No ref)'
    fi
done

echo
echo 'Halping testme'
python -m coverage run --source=. -a pyhalp.py <testme.py 
# So testme didn't get noticed by coverage.py because it was Halp that ran it.
# Just screen it out of the coverage report below.

echo
python -m coverage report -m | egrep -v 'pyhalp|structs|testme'
