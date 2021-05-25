MAKEFLAGS += .silent

format:
	isort .
	black .

lint:
	find . -type f -name "*.py" | xargs pylint

unused-imports:
	find . -type f -name "*.py" | xargs pylint --disable=all --enable=W0611

type-check:
	mypy .
	pyright

test:
	python3 -m pytest

prof:
	kernprof -lv profile_entry.py > profile_output.txt

loc:
	tokei .

clean:
	rm -rf __pycache__/

.PHONY: format lint unused-imports type-check test prof loc clean
