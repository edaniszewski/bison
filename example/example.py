"""
A (contrived) example of how to use bison
"""

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


# now, for examples sake, lets see how data can be accessed

print('Unified configuration: {}'.format(config.config))

print('Getting values:')
print('\tlog: {}'.format(config.get('log')))
print('\tport: {}'.format(config.get('port')))
print('\tsettings: {}'.format(config.get('settings')))
print('\tsettings.requests.timeout: {}'.format(config.get('settings.requests.timeout')))

print('Setting values:')
print('\tlog (pre):  {}'.format(config.get('log')))
config.set('log', 'warn')
print('\tlog (post): {}'.format(config.get('log')))
