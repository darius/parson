#!/bin/bash
# Automated test.

python -m coverage erase

for f in error_tests/bad*.itsy; do
    echo
    echo "Should fail:" ${f}
    if python -m coverage run --source=. -a itsy.py ${f}; then
        echo "Didn't fail!"
    fi
done

for f in eg/*.itsy; do
    echo
    echo "To C:" ${f}
    if python -m coverage run --source=. -a itsy.py ${f}; then
        echo -n    # Expected success (btw what's a no-op in bash?)
    else
        echo "Failed!"
    fi
    fc=${f%.*}.c
    if test -f ${fc}.ref; then
        diff -u ${fc}.ref ${fc}
        # TODO raise error at exit if there was a diff
    else
        echo '  (No ref)'
    fi
done

echo
echo 'Halping halpme'
python -m coverage run --source=. -a pyhalp.py <halpme.py 
# So halpme didn't get noticed by coverage.py because it was Halp that ran it.
# Just screen it out of the coverage report below.

echo
python -m coverage report -m --omit='halpme.py,pyhalp.py,structs.py'
