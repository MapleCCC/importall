MAKEFLAGS += .silent

format:
	isort .
	black .

lint:
	find . -type f -name "*.py" | xargs pylint

type-check:
	mypy .
	pyright

test:
	python3 -m pytest

loc:
	tokei .

clean:
	rm -rf __pycache__/

.PHONY: format lint type-check test loc clean
