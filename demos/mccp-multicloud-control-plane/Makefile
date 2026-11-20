# Run every target from demos/mccp-multicloud-control-plane
RG        ?= rg-contoso-mccp
LOCATION  ?= eastus2
ATTACH_RG ?=
BICEP_MAIN   = infra/mccp/main.bicep
ATTACH_FLAG  = $(if $(ATTACH_RG),--attach-rg $(ATTACH_RG),)

.PHONY: demo test bicep-build whatif deploy clean

demo:
	uv run python -m mccp demo --mode local --color

test:
	uv run pytest -q

bicep-build:
	az bicep build --file $(BICEP_MAIN) --stdout > /dev/null && echo "bicep OK"

# preview only, deploys nothing. Example: make whatif ATTACH_RG=<your-fsa-lab-rg>
whatif:
	bash infra/mccp/deploy.sh --rg $(RG) --location $(LOCATION) $(ATTACH_FLAG) --what-if-only

deploy:
	bash infra/mccp/deploy.sh --rg $(RG) --location $(LOCATION) $(ATTACH_FLAG)

clean:
	rm -rf artifacts/mccp
