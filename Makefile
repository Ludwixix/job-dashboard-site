.PHONY: scrape build deploy deploy-draft lint test archive-apps clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

scrape: ## Run the daily job scraper
	python3 scrape_daily.py

build: reclassify ## Regenerate the dashboard HTML
	python3 build_nonlinkedin_dashboard.py

reclassify: ## Reclassify jobs into correct categories
	python3 reclassify_jobs.py

deploy: ## Deploy to Netlify (production)
	netlify deploy --prod --site 909bff86-27e5-4a34-b09e-bbb6cdc04a39

deploy-draft: ## Deploy draft to Netlify
	netlify deploy --site 909bff86-27e5-4a34-b09e-bbb6cdc04a39

lint: ## Run Python linter
	ruff check . --exclude _archive/

test: ## Run test suite
	python3 -m pytest tests/ -v

archive-apps: ## Archive application materials older than 30 days
	python3 _archive_apps.py

clean: ## Remove temp and cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
