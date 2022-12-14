================================
 GNU Mailman Coding Style Guide
================================

Copyright (C) 2002-2022 Barry A. Warsaw


Python coding style guide for GNU Mailman Core
==============================================

This document contains a style guide for Python programming, as used in GNU
Mailman Core.  `PEP 8`_ is the basis for this style guide so its
recommendations should be followed except for the differences outlined here.
Core is a Python 3 application, so this document assumes the use of Python 3.

Much of the style guide is enforced by the command ``tox -e qa``.

* When creating new modules, start with the `GNU Mailman Python template`_ as
  an example.

* Public module-global names should be exported in the ``__all__`` but use the
  ``@public`` decorator from the public_ package to do this for all classes
  and functions.

* Imports are always put at the top of the file, just after any module
  comments and docstrings, and before module globals and constants.

  Imports should be grouped, with the order being:

  1. non-``from`` imports, grouped from shortest module name to longest module
     name, with ties being broken by alphabetical order.
  2. ``from``-imports grouped alphabetically.

  Put a single blank line between the non-``from`` import and the
  ``from``-imports.

* Right hanging comments are discouraged, in favor of preceding comments.
  E.g. bad::

    foo = baz(bar)  # This has a side-effect of fooing the bar.

  Good::

    # This has a side-effect of fooing the bar.
    foo = blarzigop(bar)

  Comments should always be complete sentences, with proper capitalization and
  full stops (periods) at the end.  We use two spaces after periods.

* Put two blank lines between any top level construct or block of code
  (e.g. after import blocks).  Put only one blank line between methods in a
  class.  No blank lines between the class definition and the first method in
  the class.  No blank lines between a class/method and its docstrings.

* Try to minimize the vertical whitespace in a class or function.  If you're
  inclined to separate stanzas of code for readability, consider putting a
  comment in describing what the next stanza's purpose is.  Don't put useless
  or obvious comments in just to avoid vertical whitespace though.

* Unless internal quote characters would mess things up, the general rule is
  that single quotes should be used for short strings and double quotes for
  triple-quoted multi-line strings and docstrings.  E.g.::

    foo = 'a foo thing'
    warn = "Don't mess things up"
    notice = """Our three chief weapons are:
             - surprise
             - deception
             - an almost fanatical devotion to the pope
             """

* Write docstrings for modules, functions, classes, and methods.  Docstrings
  can be omitted for special methods (e.g. ``__init__()`` or ``__str__()``)
  where the meaning is obvious.

* `PEP 257`_ describes good docstrings conventions.  Note that most
  importantly, the ``"""`` that ends a multiline docstring should be on a line
  by itself, e.g.::

    """Return a foobang

    Optional plotz says to frobnicate the bizbaz first.
    """

* For one liner docstrings, keep the closing ``"""`` on the same line.

* ``fill-column`` for docstrings should be 78.

* When testing the emptiness of sequences, use ``if len(seq) == 0`` instead of
  relying on the falseness of empty sequences.  However, if a variable can be
  one of several false values, it's okay to just use ``if seq``, though a
  preceding comment is usually in order.

* Always decide whether a class's methods and instance variables should be
  public or non-public.

  Single leading underscores are generally preferred for non-public
  attributes.  Use double leading underscores only in classes designed for
  inheritance to ensure that truly private attributes will never name clash.
  These should be rare.

  Public attributes should have no leading or trailing underscores unless they
  conflict with reserved words, in which case, a single trailing underscore is
  preferable to a leading one, or a corrupted spelling, e.g. ``class_`` rather
  than ``klass``.


.. _`PEP 8`: https://www.python.org/peps/pep-0008.html
.. _`GNU Mailman Python template`: https://gitlab.com/mailman/mailman/blob/master/template.py
.. _public: https://public.readthedocs.io/en/latest/
.. _`PEP 257`: https://www.python.org/peps/pep-0257.html
