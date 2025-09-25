SHELL := bash

TERRAFORM_DIR := terraform
FRONTEND_DIR := services/frontend
DIST_DIR := services/frontend/dist

.PHONY: up down logs nuke build deploy

up:
	docker compose up -d localstack

down:
	docker compose down -v

logs:
	docker logs -f localstack

nuke:
	docker compose down -v && docker volume rm $$(docker volume ls -q | grep localstack_data || true) || true

build:
	@echo "→ Building in $(FRONTEND_DIR)"
	@cd "$(FRONTEND_DIR)" && \
	if [ -f package-lock.json ]; then npm ci; else npm install; fi && \
	npm run build

deploy: build
	@echo "→ Deploying to S3 + CloudFront"
	@BUCKET=$$(terraform -chdir=$(TERRAFORM_DIR) output -raw frontend_bucket_name); \
	DIST_ID=$$(terraform -chdir=$(TERRAFORM_DIR) output -raw cloudfront_id); \
	DOMAIN=$$(terraform -chdir=$(TERRAFORM_DIR) output -raw cloudfront_domain); \
	test -n "$$BUCKET" && test -n "$$DIST_ID" || { echo "Missing TF outputs"; exit 1; }; \
	aws s3 sync "$(DIST_DIR)/" "s3://$$BUCKET" --delete \
	  --cache-control "public,max-age=31536000,immutable" --exclude "index.html"; \
	aws s3 cp "$(DIST_DIR)/index.html" "s3://$$BUCKET/index.html" \
	  --cache-control "no-cache,no-store,must-revalidate" --content-type "text/html"; \
	aws cloudfront create-invalidation --distribution-id "$$DIST_ID" --paths "/index.html"; \
	echo "✅ Deployed → https://$$DOMAIN"