# Splitzie

## Development commands

* Formatting: `black .`
* Make message file: `python manage.py makemessages -l nl`
* Compile message file: `python manage.py compilemessages`


## Database support

Only PostgreSQL is supported.

Do not use SQLite, also not for development,
because it [does not have](https://www.sqlite.org/datatype3.html#storage_classes_and_datatypes)
a decimal type.
Instead currency is stored as floats, leading to rounding errors.

## Code style

* JavaScript: Google Style Guide (https://google.github.io/styleguide/jsguide.html)


## To do

* GET page for immediate delete of linked e-mail.
* Recover groups form.

## Future work (in no particular order)

* Progressive Enhancement: gracefully degrade when JavaScript is disabled.
* Maybe store currency as integers (cents) in the database instead of decimals.
  This enables support for SQLite.
* Export payments
