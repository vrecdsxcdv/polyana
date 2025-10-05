PY=python3
VENV=venv
ACT=source $(VENV)/bin/activate

.PHONY: venv install check run stop logs test set-commands chatid

venv:
	$(PY) -m venv $(VENV)

install: venv
	$(ACT) && pip install --upgrade pip && pip install -r requirements.txt

check:
	$(ACT) && $(PY) scripts/check_env.py

run:
	$(ACT) && $(PY) app.py

stop:
	./scripts/kill_dupes.sh

logs:
	tail -n 150 -f bot.log

test:
	$(ACT) && pytest -q

set-commands:
	$(ACT) && $(PY) scripts/set_commands.py

chatid:
	$(ACT) && $(PY) scripts/check_env.py