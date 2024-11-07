title = "\n---$(shell tput bold)$(shell tput setaf 2)$1 $(shell tput sgr0)\n"

build:
	@echo $(call title, "Building containers........")
	docker compose build

run:
	@echo $(call title, "Running containers.........")
	docker compose up -d

client:
	@echo $(call title, "Running client.............")
	docker compose run client

local: build run
