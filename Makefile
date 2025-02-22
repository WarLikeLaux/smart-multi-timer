.PHONY: all collect

all: collect

collect:
	@echo "Collecting Python files..."
	@bash collect.sh $$(find src -type f -name "*.py")