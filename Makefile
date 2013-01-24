.PHONY: install clean

install:
	python setup.py install
clean:
	python setup.py clean --all
	rm -rf dist/
	rm -rf *.egg-info/
