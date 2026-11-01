.PHONY: serve build index new clean image run-image diagrams

PAGEFIND = npx -y pagefind@1.5.2
PORT ?= 8090
DIAGRAMS = $(patsubst %.d2,%.svg,$(shell find content -name '*.d2'))

serve: index ## Preview locally with drafts at localhost:1313
	hugo server -D

build: ## Build the site and search index into public/
	hugo --gc --minify --cleanDestinationDir
	$(PAGEFIND) --site public

index: ## Build the search index into static/pagefind for hugo server
	hugo --quiet --cleanDestinationDir
	$(PAGEFIND) --site public --output-path static/pagefind

new: ## Create a draft note: make new note=k8s/container/cgroups
	@test -n "$(note)" || (echo "usage: make new note=k8s/container/cgroups" && exit 1)
	hugo new content $(note).md

clean: ## Remove build output
	rm -rf public resources/_gen static/pagefind .hugo_build.lock

image: ## Build the Docker image
	docker build -t build-site .

run-image: image ## Run the image at localhost:$(PORT), e.g. make run-image PORT=9000
	docker run --rm -p $(PORT):80 build-site

diagrams: $(DIAGRAMS) ## Render each content/**/*.d2 to an .svg beside it

%.svg: %.d2 diagram.d2
	cat diagram.d2 $< | d2 --omit-version --scale 1 - $@
