TimePiece
=========

A DSL to assist with writing specifications describing intervals and durations
of time with filters.

.. image:: https://travis-ci.org/delfick/timepiece.png?branch=master
    :target: https://travis-ci.org/delfick/timepiece

Why the name?
-------------

Because time_spec was uninspiring and a good friend suggested `timepiece`.

Naming things is difficult!

But why?
--------

Because I wanted to represent when scheduled actions should take place and I
was starting to have too many columns in my database representing everything I
wanted to be able to do.

Installation
------------

Use pip!:

.. code-block:: bash

    pip install timepiece

Or if you're developing it:

.. code-block:: bash

    pip install -e .
    pip install -e ".[tests]"

Usage
-----

Just create the timepiece and give it a specification!

.. code-block:: python

    from timepiece.spec import make_timepiece

    from datetime import datetime

    timepiece = make_timepiece()

    obj = timepiece.time_spec_to_object("between(start: now()) & interval(every: amount(num:1 size: hour))")

    print("Next time is: ", obj.following(datetime.utcnow()))

See The docs at https://timepiece.readthedocs.io for more information!

Tests
-----

To run the tests in this project, just use the helpful script:

.. code-block:: bash

    ./test.sh

Or run tox:

.. code-block:: bash

    tox

