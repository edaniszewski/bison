<p align="center">
    <a href="https://travis-ci.org/edaniszewski/bison"><img src="https://travis-ci.org/edaniszewski/bison.svg?branch=master" /></a>
    <a href='https://coveralls.io/github/edaniszewski/bison'><img src='https://coveralls.io/repos/github/edaniszewski/bison/badge.svg' /></a>
    <a href="https://pypi.python.org/pypi/bison"><img src="https://img.shields.io/pypi/v/bison.svg"></a>
    <a href="LICENSE"><img src="https://img.shields.io/github/license/edaniszewski/bison.svg"></a>
        
<h1 align="center">bison</h1>
</p>

<p align="center">Python application configuration</p>


## What is Bison?
Bison is a configuration solution for Python applications that aims to be simple
and intuitive. It supports:
* reading from YAML config files
* reading from environment variables
* setting explicit values
* setting defaults
* configuration validation
* configuration access/manipulation with dot notation

Instead of implementing custom configuration reading and parsing, you can use
Bison to handle it for you.

Bison was inspired by [Viper][viper] and the lack of good
application configuration solutions for Python (at least, in my opinion). Documentation
for Bison can be found on [ReadtheDocs][docs]

Bison uses the following precedence order. Each item in the list takes precedence
over the item below it.
- override (e.g. calling `Bison.set()`)
- environment
- config file
- defaults

## Installation
Bison can be installed with `pip`
```
pip install bison
```
or with `pipenv`
```
pipenv install bison
```

## Using Bison
### Creating a configuration Scheme
A configuration scheme is not required by Bison, but having one allows you to set default
values for configuration fields as well as do configuration validation. It is pretty easy
to create a new Scheme:

```python
scheme = bison.Scheme()
```

A Scheme is really just a container for configuration options, so without any options, a
Scheme is somewhat useless.

#### Configuration Options
There are currently three types of configuration options:
- `bison.Option`
- `bison.DictOption`
- `bison.ListOption`

Their intended functionality should be mostly obvious from their names. An `Option` represents
a singular value in a configuration. A `DictOption` represents a dictionary or mapping of values
in a configuration. A `ListOption` represents a list of values in a configuration.

See the [documentation][docs] for more on how options can be configured.

Any number of options can be added to a Scheme, but as a simple example we can define a Scheme
which expects a key "log", and a key "count".

```python
scheme = bison.Scheme(
    bison.Option('log'),
    bison.Option('count'),
)
```

#### Configuration Validation
Validation operates based on the constraints set on the options. Above, there are no
constraints (other than the need for those keys to exist), so any value for "log" and
"count" will pass validation.

An option can be constrained in different ways by using its keyword arguments. For example,
to ensure the value for "count" is an integer,
```python
bison.Option('count', field_type=int)
```

Or, to restrict the values to a set of choices
```python
bison.Option('log', choices=['debug', 'info', 'warn', 'error'])
```

The [documentation][docs] goes into more detail about other validation settings.

#### Setting Defaults
If a default value is not set on an option, it is considered required. In these cases,
if the key specified by that value is not present in the parse configuration, it will
cause a validation failure.

If a default value is set, then the absence of that field in the configuration will not
cause a validation failure.

```python
bison.Option('log', default='info')
```

### Configuring Bison
Once you have a Scheme to use (if you'd like to), it will need to be passed to a Bison
object to manage the config building. 

```python
scheme = bison.Scheme()
config = bison.Bison(scheme)
```

There are a few options that can be set on the Bison object to change how it
searches for and builds the unified configuration. 

For reading configuration files
```python
config.config_name = 'config'  # name of the config file (no extension)
config.add_config_paths(       # paths to look in for the config file
    '.',
    '/tmp/app'
)
config.config_format = bison.YAML # the config format to use
```

For reading environment variables
```python
config.env_prefix = "MY_APP"  # the prefix to use for environment variables
config.auto_env = True  #  automatically bind all options to env variables based on their key
```

### Building the unified config
Once the scheme has been set (if using) and Bison has been configured, the only thing
left to do is to read in all the config sources and parse them into a unified config.
This is done simply with
```python
config.parse()
```

### Example
Below is a complete example for parsing a hypothetical application configuration which
is described by the following YAML config.
```yaml
log: debug
port: 5000
settings:
  requests:
    timeout: 3
backends:
  - host: 10.1.2.3
    port: 5001
  - host: 10.1.2.4
    port: 5013
  - host: 10.1.2.5
    port: 5044
```

```python
import bison

# the scheme for the configuration. this allows us to set defaults
# and validate configuration data
config_scheme = bison.Scheme(
    bison.Option('log', default='info', choices=['debug', 'info', 'warn', 'error']),
    bison.Option('port', field_type=int),
    bison.DictOption('settings', scheme=bison.Scheme(
        bison.DictOption('requests', scheme=bison.Scheme(
            bison.Option('timeout', field_type=int)
        ))
    )),
    bison.ListOption('backends', member_scheme=bison.Scheme(
        bison.Option('host', field_type=str),
        bison.Option('port', field_type=int)
    ))
)

# create a new Bison instance to store and manage configuration data
config = bison.Bison(scheme=config_scheme)

# set the config file name to 'app' (default is 'config') and set the
# search paths to '.' and '/tmp/app/config'
config.config_name = 'app'
config.add_config_paths('.', '/tmp/app/config')

# set the environment variable prefix and enable auto-env
config.env_prefix = 'MY_APP'
config.auto_env = True

# finally, parse the config sources to build the unified configuration
config.parse()
```

See the [example](example) directory for this example along with demonstrations
of how to access configuration data.

## Future Work
There is more that can be done to improve Bison and expand its functionality. If
you wish to contribute, open a pull request. If you have questions or feature requests,
open an issue. Below are some high level ideas for future improvements:

* Support additional configuration formats (JSON, TOML, ...)
* Versioned configurations


[docs]: http://readthedocs
[viper]: https://github.com/spf13/viper