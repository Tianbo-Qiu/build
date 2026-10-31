.PHONY: serve build index new clean

PAGEFIND = npx -y pagefind@1.5.2

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
