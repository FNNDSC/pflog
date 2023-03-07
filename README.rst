pflog
=====

|Version| |MIT License| |ci|

Abstract
--------

This software is a lightweight user of the ``pftel-client`` library that
allows for logging to a remote logging service. Both stand-alone and
modular use cases are supported. At the moment only minimal coverage of
server API is provided.

Overview
--------

``pflog`` is a simple app that is both a stand alone client as well as a
module for logging to a ``pftel`` telemetry server.

Installation
------------

Local python venv
~~~~~~~~~~~~~~~~~

For *on the metal* installations, ``pip`` it:

.. code:: bash

   pip install pflog

docker container
~~~~~~~~~~~~~~~~

.. code:: bash

   docker pull fnndsc/pflog

Runnning
--------

The simplest way to use ``pflog`` in script mode is

.. code:: bash

   export PFTEL=http://localhost:22223 # obviously change this as needed
   pflog --pftelURL $PFTEL --verbosity 1 --log "Hello world!"

This writes messages to default ``logObject`` under a ``logCollection``
that is the timestamp of the event transmission. Within the
``logCollection`` will be single ``logEvent`` called ``000-event``.

Arguments
---------

.. code:: html

           --pftelURL <pftelURL>
           The URL of the pftel instance. Typically:

                   --pftelURL http://some.location.somewhere:22223

           and is a REQUIRED parameter.

           --log <logMessage>
           The actual message to log. Use quotes to protect messages that
           contain spaces:

                   --log "Hello, world!"

           [--logObject <logObjectInPTFEL>] "default"
           [--logCollection <logCollectionInPFTEL>] `timestamp`
           [--logEvent <logEventInPFTEL>] "event"
           [--appName <appName>]
           [--execTime <execTime>]
           Logs are stored within the pftel database in

               `{logObjectInPFTEL}`/`{logCollectionInPFTEL}`/`{logEventInPFTEL}`

           if not specified, use defaults as shown. The <appName> and <execTime>
           are stored within the <logEventInPFTEL>.

           [--asyncio]
           If specified, use asyncio, else do sync calls.

           [--detailed]
           If specified, return detailed responses from the server.

           [--test]
           If specified, run a small internal test on multi-logger calls.

           [--pftelUser <user>] ("chris")
           The name of the pftel user. Reserved for future use.

           [--inputdir <inputdir>]
           An optional input directory specifier. Reserverd for future use.

           [--outputdir <outputdir>]
           An optional output directory specifier. Reserved for future use.

           [--man]
           If specified, show this help page and quit.

           [--verbosity <level>]
           Set the verbosity level. The app is currently chatty at level 0 and level 1
           provides even more information.

           [--debug]
           If specified, toggle internal debugging. This will break at any breakpoints
           specified with 'Env.set_trace()'

           [--debugTermsize <253,62>]
           Debugging is via telnet session. This specifies the <cols>,<rows> size of
           the terminal.

           [--debugHost <0.0.0.0>]
           Debugging is via telnet session. This specifies the host to which to connect.

           [--debugPort <7900>]
           Debugging is via telnet session. This specifies the port on which the telnet
           session is listening.

Development
-----------

Instructions for developers.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To debug, the simplest mechanism is to trigger the internal remote
telnet session with the ``--debug`` CLI. Then, in the code, simply add
``Env.set_trace()`` calls where appropriate. These can remain in the
codebase (i.e. you don’t need to delete/comment them out) since they are
only *live* when a ``--debug`` flag is passed.

Testing
~~~~~~~

Run unit tests using ``pytest``. Coming soon!

*-30-*

.. |Version| image:: https://img.shields.io/docker/v/fnndsc/pl-pflog?sort=semver
   :target: https://hub.docker.com/r/fnndsc/pl-pflog
.. |MIT License| image:: https://img.shields.io/github/license/fnndsc/pl-pflog
   :target: https://github.com/FNNDSC/pl-pflog/blob/main/LICENSE
.. |ci| image:: https://github.com/FNNDSC/pl-pflog/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/FNNDSC/pl-pflog/actions/workflows/ci.yml
