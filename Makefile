# Makefile.prod — các lệnh tiện ích dùng trên EC2
# Cách dùng: make -f Makefile.prod <lệnh>

.PHONY: up down restart logs migrate status health shell deploy clean

up:
	docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

down:
	docker compose -f docker-compose.prod.yml down

restart:
	docker compose -f docker-compose.prod.yml restart backend

logs:
	docker compose -f docker-compose.prod.yml logs -f backend

logs-nginx:
	docker compose -f docker-compose.prod.yml logs -f nginx

migrate:
	docker exec skinaid_backend alembic upgrade head

status:
	docker compose -f docker-compose.prod.yml ps

health:
	curl -s http://localhost/health | python3 -m json.tool

shell:
	docker exec -it skinaid_backend bash

clean:
	docker image prune -f

deploy:
	git pull origin main
	docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build --remove-orphans
	sleep 15
	docker exec skinaid_backend alembic upgrade head
	docker image prune -f
