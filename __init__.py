from opsdroid.matchers import match_regex
import aiohttp
import logging


logged_in = False
token = None

async def login(config, session):
    url = config['url']
    username = config['username']
    password = config['password']
    data = {
        'username': username,
        'password': password,
        'eauth': 'auto',
    }
    async with session.post(url + '/login', json=data) as resp:
        # TODO: onsider response code, handle errors.
        logged_in = True

async def run_post(runner, config):
    verify_ssl = True
    if 'verify_ssl' in config:
        verify_ssl = config['verify_ssl']
    conn = aiohttp.TCPConnector(verify_ssl=verify_ssl)
    async with aiohttp.ClientSession(connector=conn) as session:
        if not logged_in:
            await login(config, session)

        data = {
            'client': 'runner',
            'fun': runner
        }
        async with session.post(url, data) as resp:
            return resp

@match_regex(r'^salt-run (.*)')
async def salt_run(opsdroid, config, message):
    runner = message.regex.group(1)

    result = await run_post(runner, config)
    await message.respond(result.json())

