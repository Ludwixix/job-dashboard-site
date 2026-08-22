.PHONY: scrape build deploy deploy-draft lint test archive-apps clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

scrape: ## Run the daily job scraper
	python3 scrape_daily.py

build: ## Regenerate the dashboard HTML (dedup + reclassify + generate)
	python3 deduplicate_jobs.py
	python3 -c "import json; from reclassify_jobs import reclassify; d=json.load(open('jobs_nonlinkedin_2026-08-08_clean.json')); d,s=reclassify(d); json.dump(d,open('jobs_nonlinkedin_2026-08-08_final.json','w'),indent=2)"
	python3 build_categorized_dashboard.py

echo 'Dashboard generated: index_categorized.html'

build-old: ## Regenerate using the original generator
	python3 build_nonlinkedin_dashboard.py

dedup: ## Remove duplicate jobs
	python3 deduplicate_jobs.py

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
