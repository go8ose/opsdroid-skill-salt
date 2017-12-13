from opsdroid.matchers import match_regex
import aiohttp
import logging


class LoginError(Exception):
    pass

async def login(config, session):
    url = config['url']
    data = {
        'username': config['username'],
        'password': config['password'],
        'eauth': config['eauth'],
    }
    async with session.post(url + '/login', json=data) as resp:
        if resp.status != 200:
            logging.warning(
                "Login to {} failed, status={}. username={}, eauth={}".format(
                resp.request_info.url, resp.status, config['username'],
                config['eauth']))
            raise LoginError


# Setup some things we can re-use for each time we're invoked.  Hopefully by
# persisting (in-memory) the cookie_jar we'll and connector we'll save some
# time.  We store them in the config object as a convinent way of accessing
# them later.
def setup(opsdroid):
    verify_ssl = True
    my_config = [s for s in opsdroid.config['skills'] if s['name'] == 'salt'][0]
    if 'verify_ssl' in my_config:
        verify_ssl = my_config['verify_ssl']
    my_config['aio_connector'] = aiohttp.TCPConnector(verify_ssl=verify_ssl)
    my_config['aio_cookiejar'] = aiohttp.CookieJar()

async def dispatch_salt_run(runner, config):
    async with aiohttp.ClientSession(connector=config['aio_connector'], cookie_jar=config['aio_cookiejar']) as session:
        if len([i for i in session.cookie_jar if i.key == 'session_id']) == 0:
            await login(config, session)

        data = {
            'client': 'runner',
            'fun': runner
        }
        url = config['url']
        async with session.post(url, json=data) as resp:
            return resp

async def dispatch_salt(tgt, function, tgt_type, config, *arg, **kwarg):
    async with aiohttp.ClientSession(connector=config['aio_connector'], cookie_jar=config['aio_cookiejar']) as session:
        if len([i for i in session.cookie_jar if i.key == 'session_id']) == 0:
            await login(config, session)

        data = {
            'client': 'local',
            'tgt': tgt,
            'tgt_type': tgt_type,
            'fun': function,
            'arg': arg,
            'kwarg': kwarg,
        }
        url = config['url']
        async with session.post(url, json=data) as resp:
            return resp

@match_regex(r'^salt-run (.*)')
async def salt_run(opsdroid, config, message):
    '''Pass users command to the salt master, specifically asking the master
    to run one of the runner modules. Your salt master authentication system
    must have allowed the configured user to have '@runner' in order for
    this to work'''
    runner = message.regex.group(1)

    try:
        result = await dispatch_salt_run(runner, config)
        if result.status != 200:
            await message.respond('Error returned from salt for runner {}: {} ({})'.format(runner, result.status, result.reason))
        else:
            result_text = await result.text()
            await message.respond(result_text)
    except LoginError:
        await message.respond('Login Error to salt. Check logs.')

@match_regex(r'^salt (?P<target>\S+)\s+(?P<function>(?:\w|[.])+)(?:\s+(?P<remaining>.*))?')
async def salt(opsdroid, config, message):
    '''Pass users command to the salt master for execution. We don't
    sanitise this at all, your salt master _must_ be configured with
    appropriate access controls to allow this, and to not allow things that
    you consider unsafe.  And given that this is coming from a chat channel,
    you should probably be fairly consertative about what you consider to be
    safe.'''
    tgt = message.regex.group('target')
    function = message.regex.group('function')
    try:
        remaining = message.regex.group('remaining').split()
    except AttributeError:
        # If there was no remaining, then message.regex.group('remaining')
        # is NoneType, which won't split()
        remaining = []

    # I need to split up the remaining into arguments and keyword arguments.
    args = [i for i in remaining if '=' not in i]
    kwargs = [i for i in remaining if '=' in i]
    kwargs_dict = dict([i.split('=') for i in kwargs])

    # Default the targetting type to glob, but allow them to override that
    tgt_type = 'glob'
    if 'tgt_type' in kwargs_dict:
        tgt_type = kwargs_dict['tgt_type']
        del kwargs_dict['tgt_type']

    try:
        result = await dispatch_salt(tgt=tgt, function=function, tgt_type=tgt_type, 
            config=config, *args, **kwargs_dict)
        if result.status != 200:
            await message.respond('Error returned from salt {}: {} ({})'.format(data, result.status, result.reason))
        else:
            result_text = await result.text()
            await message.respond(result_text)
    except LoginError:
        await message.respond('Login Error to salt. Check logs.')
