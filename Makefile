.PHONY: test rank validate sandbox clean

test:
	python -m pytest tests/ -v

rank:
	python rank.py --candidates ./candidates.jsonl --out ./Code_With_Errors.csv

validate:
	python validate_submission.py Code_With_Errors.csv

honeypot:
	python scripts/honeypot_check.py --submission Code_With_Errors.csv --dataset candidates.jsonl

sandbox:
	python sandbox_app.py --host 127.0.0.1 --port 7860

docker-build:
	docker build -t redrob-ranker .

docker-run:
	docker run --rm -p 7860:7860 redrob-ranker

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__ .pytest_cache
