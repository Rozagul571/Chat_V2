.PHONY: build up down logs clean create-users test

mig:
	python3 manage.py makemigrations
	python3 manage.py migrate

admin:
	python3 manage.py createsuperuser

app:
	python3 manage.py startapp apps


build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker logs chat_app


clean:
	docker-compose down -v
	docker rmi chat_app

create-users:
	docker exec -it chat_app python manage.py create_users




