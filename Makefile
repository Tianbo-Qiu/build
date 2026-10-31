.PHONY: serve build new clean

serve: ## Preview locally with drafts at localhost:1313
	hugo server -D

build: ## Build the site into public/
	hugo --gc --minify

new: ## Create a draft note: make new note=k8s/container/cgroups
	@test -n "$(note)" || (echo "usage: make new note=k8s/container/cgroups" && exit 1)
	hugo new content $(note).md

clean: ## Remove build output
	rm -rf public resources/_gen .hugo_build.lock
