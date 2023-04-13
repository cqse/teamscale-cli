publish_release:
	rm -rf build
	python3 setup.py bdist_egg bdist_wheel
	python3 -m twine upload dist/*
