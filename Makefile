title = "\n---$(shell tput bold)$(shell tput setaf 2)$1 $(shell tput sgr0)\n"

build:
	@echo $(call title, "Building containers........")
	docker compose build

run:
	@echo $(call title, "Running containers.........")
	docker compose up -d

local: build run

clean:
	@echo $(call title, "Cleaning up.................")
	docker compose down --volumes --remove-orphans
