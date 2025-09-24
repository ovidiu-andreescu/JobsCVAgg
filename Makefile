.PHONY: up down logs nuke

up:
	docker compose up -d localstack

down:
	docker compose down -v

logs:
	docker logs -f localstack

nuke:
	docker compose down -v && docker volume rm $$(docker volume ls -q | grep localstack_data || true) || true
