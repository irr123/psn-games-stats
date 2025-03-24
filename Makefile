.PHONY: fmt
fmt:
	ruff format $(PWD)

.PHONY: lint
lint:
	ruff check $(PWD) --fix

.PHONY: srv
srv:
	python3 -m http.server -d $(PWD)
