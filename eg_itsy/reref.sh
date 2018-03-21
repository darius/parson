# Reset the reference outputs to match the current outputs.

cd eg
for f in *.c; do
    cp ${f} ${f}.ref
done
