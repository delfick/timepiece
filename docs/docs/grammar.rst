.. _grammar:

The Grammar
===========

Timepiece is based off an EBNF grammar using the awesome
`parsimonious <https://github.com/erikrose/parsimonious>`_ library.

The idea is that the grammar parses the specification into arbitrary sections
and then we turn those arbitrary sections into objects using the sections
specified in ``timepiece.sections``. As in, the definition of the grammar and
the definition of the valid sections and their arguments are separate.

The grammar can be seen below:

.. the_grammar::

Essentially we can create groups with parenthesis, sections are combined with
``|`` and ``&`` operators and sections are like functions with
``name(arg1: val1, arg2: val2(arg3: val3, arg:4: val4))``.

For speed concerns, the grammar contains no white space and all white space
is stripped from the specification before parsing.

