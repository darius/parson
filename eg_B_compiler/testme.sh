#!/bin/bash
# Automated test.

for f in error_tests/*.b; do
    echo
    echo "Should fail:" ${f}
    fs=${f%.*}.s
    if python bcomp.py ${f} >${fs}; then
        echo "Didn't fail!"
    fi
done

for f in eg/*.b; do
    echo
    echo "To C:" ${f}
    fs=${f%.*}.s
    if python bcomp.py ${f} >${fs}; then
        echo -n    # Expected success (btw what's a no-op in bash?)
    else
        echo "Failed!"
    fi
    if test -f ${fs}.ref; then
        diff -u ${fs}.ref ${fs}
        # TODO raise error at exit if there was a diff
    else
        echo '  (No ref)'
    fi
done
