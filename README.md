# pflog

[![Version](https://img.shields.io/docker/v/fnndsc/pflog?sort=semver)](https://hub.docker.com/r/fnndsc/pflog)
[![MIT License](https://img.shields.io/github/license/fnndsc/pflog)](https://github.com/FNNDSC/pflog/blob/main/LICENSE)
[![ci](https://github.com/FNNDSC/pflog/actions/workflows/build.yml/badge.svg)](https://github.com/FNNDSC/pflog/actions/workflows/build.yml)

## Abstract

This software is a lightweight user of the `pftel-client` library that allows for logging to a remote logging service. Both stand-alone and modular use cases are supported. At the moment only minimal coverage of server API is provided.

## Overview

`pflog` is a simple app that is both a stand alone client as well as a module for logging to a `pftel` telemetry server.


## Installation

### Local python venv

For _on the metal_ installations, `pip` it:

```bash
pip install pflog
```

### docker container

```bash
docker pull fnndsc/pflog
```

## Runnning

### Script mode

To use `pflog` in script mode you simply call the script with appropriate arguments (and of course this assumes you have a server instance at the `$PFTEL` location)

```bash
export PFTEL=http://localhost:22223 # obviously change this as needed

pflog                                           \
        --log              "Hello, world!"      \
        --pftelURL         $PFTEL               \
        --verbosity        1                    \
```

### Module mode

To use `pflog` in python module mode, you declare an object and instantiate with a dictionary of values. The dictionary keys are _identical_ to the script CLI keys:

```python
from pflog               import pflog

log:pflog.Pflog        = pflog.Pflog( {
        'log'           : 'Hello, world!',
        'pftelURL'      : 'http://localhost:22223',
        'verbosity'     : '1'
    }
)
d_tlog:dict             = log.run()

# You can use this same object to log more messages:
log('This is another message')
log('and so is this!')

```

This writes messages to a `logObject` called _default_ under a `logCollection` that is the timestamp of the event transmission. Within the `logCollection` will be `logEvent`s  prefixed by an incremental counter, so `000-event`, `001-event`, etc.

### Decorators and convenience functions

##### Convenience helper

The python module additionally offers a convience function `pfprint` that offers a function-like _throw back_ to C-style `fprintf` while hiding the complexity of creating and using a `Pflog` object:

```python
pfprint('https://some.telemetry.server/api/v1/weather/MA/boston', 'Brrr... it is freezing today!')
```

will log the message `Brr... it is freezing today!` in the event called `boston` of the collection `MA` of the set/object called `weather`. Note that each call of `pfprint` will create effectively a singleton object and a new connection to the telemetry server that is not reused (unlike the snippet above).

##### Timing and logging with decorators

A decorator called `tel_logTime` is also available. In the simplest case

```python
@tel_logTime
weather_model(arg1, arg2)
```

will simply print the total execution time of the function `weather_model`. This information can be additionally logged to a telemetry service using

```python
@tel_logTime(
        pftelDB = 'https://some.telemetry.server/ap1/v1/weather/MA/boston-%timestamp',
        log     = 'Weather prediction execTime'
)
weather_model(arg1, arg2)
```

which will record the execution time of the function to the `pftelDB`. Note that the `%timestamp` in the `event` field `boston-%timestamp` will be parsed at runtime with as a `pftag` string and appropriately substituted. The `log = 'Weather prediction execTime'` is simply an optional logging string that is also written to the log event. Equivalently one could do

```python
@tel_logTime(
        pftelDB = 'https://some.telemetry.server/ap1/v1/weather/MA/event',
        event   = 'boston-%timestamp'
        log     = 'Weather prediction execTime'
)
weather_model(arg1, arg2)
```

Finally, note the special case where the function to be decorated contains a python `Namespace` with an attribute called `pftelDB`. In this case, the decorator will determine the `pftelDB` from the decorated function's arguments. This is particularly useful when the main entry point for a python program uses these options and we wish to log telemetry:

```shell
# Imagine we have a python program called 'weather_app' and it has a CLI option:
weather_app --pftelDB https://some.telemetry.server/ap1/v1/weather/MA/boston-%timestamp
```

```python
# In python, assuming we have parsed the CLI with Argparser into a Namespace variable
# called 'options', we could simply do

@tel_logTime
main(options)
```

And the decorator will determine `pftelDB` from the `options`. For simplicity the `event` and `log` named args have been omitted. Note that the first decorator example was assumed to _not_ have a `Namespace` in either `arg1` nor `arg2`.

## Arguments

```html
        --pftelURL <pftelURL> | --pftelDB <URLDBpath>
        The URL of the pftel instance. Typically:

                --pftelURL http://some.location.somewhere:22223

        either this or '--pftelDB' MUST be specified. See below for --pftelDB.

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

        [--pftelDB <DBURLpath>]
        This is an alternate CLI that specifies a DB POST URL:

            --pftelDB   <URLpath>/<logObject>/<logCollection>/<logEvent>

        for example

            --pftelDB http://localhost:22223/api/v1/weather/massachusetts/boston

        Indirect parsing of each of the object, collection, event strings is
        available through `pftag` so any embedded pftag SGML is supported. So

            http://localhost:22223/api/vi/%platform/%timestamp_strmsk|**********_/%name

        would be parsed to, for example:

            http://localhost:22223/api/vi/Linux/2023-03-11/posix

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

```


## Development

### Instructions for developers.

To debug, the simplest mechanism is to trigger the internal remote telnet session with the `--debug` CLI. Then, in the code, simply add `Env.set_trace()` calls where appropriate. These can remain in the codebase (i.e. you don't need to delete/comment them out) since they are only _live_ when a `--debug` flag is passed.

### Testing

Run unit tests using `pytest`. Coming soon!

_-30-_
