.PHONY: serve build new clean

serve: ## Preview locally with drafts at localhost:1313
	hugo server -D

build: ## Build the site into public/
	hugo --gc --minify

new: ## Create a draft note: make new name=some-topic
	@test -n "$(name)" || (echo "usage: make new name=some-topic" && exit 1)
	hugo new content notes/$(name).md

clean: ## Remove build output
	rm -rf public resources/_gen .hugo_build.lock
