
#

Working title: Splitzie


## Development

* Formatting: `$ black .`
* Build CSS (requires Tailwind CLI): `tailwindcss -i ./tailwind.css -o ./groupsplit/static/style.css --minify`
  * Add `--watch` to rebuild as needed.


## Database support

SQLite is not supported because it does not have a decimal type [1].
Instead currency is stored as floats, leading to rounding errors.
You need to use a PostgreSQL server, also for development.
For PostgreSQL to work you should install `psycopg` using
for instance `pip install psycopg[binary]`.

[1] https://www.sqlite.org/datatype3.html#storage_classes_and_datatypes

## Design

* Group accessible using a shared code, e.g. via the URL: `/groups/huiwearhuajklsdnjkgfd/`
* It is possible to link e-mail addresses to a group. Each address:
  * receives notifications,
  * can be used to recover group access by receiving an email that lists all groups linked to the address.
* Group: name, secret code, linked e-mails, people
* You can dynamically add people when adding an expense.


## Code style

* JavaScript: Google Style Guide (https://google.github.io/styleguide/jsguide.html)


## Future work (in loose of priority)

* E-mails
* Progressive Enhancement: gracefully degrade when JavaScript is disabled.
* Rename project files to a better name (Splitzie?).
* Dark mode
* Maybe store currency as integers (cents) in the database instead of decimals.
  This enables support for SQLite.
* Replace messy VanillaJS with Alpine.js.
* Export payments

