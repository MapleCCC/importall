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
	python3 -m pytest test_importall.py

profile:
	kernprof --line-by-line --view profile_entry.py > profile_output.txt

loc:
	tokei .

clean:
	rm -rf __pycache__/

.PHONY: format lint unused-imports type-check test profile loc clean
