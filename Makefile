.PHONY: start build-dev run-dev install-deps test-oauth test-new-auth

install:
	pip install -r requirements-dev.txt 

start:
	uvicorn main:app --reload

build-dev:
	docker build -t chauffeur .

run-dev:
	docker run -p 8000:8000 --env FIREBASE_SERVICE_ACCOUNT_KEY=/app/serviceAccountKey.json -v ../serviceAccountKey.json:/app/serviceAccountKey.json chauffeur

test-oauth:
	python tests/test_oauth.py

test-new-auth:
	python tests/test_new_auth.py
