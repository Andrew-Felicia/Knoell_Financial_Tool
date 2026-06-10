Always activate the venv before working. You'll see `(venv)` in your terminal prompt when it's active.
Activate (Windows):
venv\Scripts\activate



flask --app wsgi db init      # first time only

flask --app wsgi db migrate -m "initial tables"
#altenative
python -m flask --app wsgi:app db migrate -m "initial tables"

flask --app wsgi db upgrade
#altenative
python -m flask --app wsgi:app db upgrade

Then start the server:
flask --app wsgi run --debug