title = "\n---$(shell tput bold)$(shell tput setaf 2)$1 $(shell tput sgr0)\n"

init:
	@echo $(call title, "Generating KMS key and CMS cert.......")

build:
	@echo $(call title, "Building container........")

run:
	@echo $(call title, "Running container.........")

dev: init build
