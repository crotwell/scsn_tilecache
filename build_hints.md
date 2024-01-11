
# build hints

```
conda create -n tilecache python=3.10
conda activate tilecache
python3 -m pip install --upgrade build
/bin/rm -f dist/* && python3 -m build
pip3 install dist/scsntilecache-*-py3-none-any.whl --force-reinstall

```

or if all deps are already installed, much faster:
```
pip3 install dist/scsntilecache-*-py3-none-any.whl --force-reinstall --no-deps
```

to publish:
```
python3 -m twine upload dist/*
```

for testing, use code in current directory so updates on edit:
```
pip install -v -e .
```
