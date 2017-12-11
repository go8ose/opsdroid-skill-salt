from opsdroid.matchers import match_regex
import aiohttp
import logging


logged_in = False
token = None

async def login(config, session):
    url = config['skills']['salt']['url']
    username = config['skills']['salt']['username']
    password = config['skills']['salt']['password']
    data = {
        'username': username,
        'password': password,
        'eauth': 'auto',
    }
    async with session.post(url + '/login', data) as resp:
        # TODO: handle an error condition

async def run_post(runner, config):
    async with aiohttp.ClientSession() as session:
        if not logged_in:
            await login(config, session)
            # TODO: check this cookie handling
            token = session.cookie_jar['token']
        else:
            session.cookie_jar.update_cookies({'token': token)

        data = {
            'client': 'runner',
            'fun': runner
        }
        async with session.post(url, data) as resp:
            return resp

@match_regex(r'^salt-run (.*)')
async def salt_run(opsdroid, config, message):
    runner = message.group[1]

    await result = run_post(runner)
    await.message.respond(result.json())

