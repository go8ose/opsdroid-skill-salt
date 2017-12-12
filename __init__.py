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


cookie_jar = None
# Setup a cookie jar we can re-use between requests, in order to save
# logging in repeatedly.
def setup(config):
    cookie_jar = aiohttp.CookieJar()

async def run_post(runner, config):
    verify_ssl = True
    if 'verify_ssl' in config:
        verify_ssl = config['verify_ssl']
    conn = aiohttp.TCPConnector(verify_ssl=verify_ssl)
    async with aiohttp.ClientSession(connector=conn, cookie_jar=cookie_jar) as session:
        if len([i for i in session.cookie_jar if i.key == 'session_id']) == 0:
            await login(config, session)

        data = {
            'client': 'runner',
            'fun': runner
        }
        url = config['url']
        async with session.post(url, json=data) as resp:
            return resp

@match_regex(r'^salt-run (.*)')
async def salt_run(opsdroid, config, message):
    runner = message.regex.group(1)

    try:
        result = await run_post(runner, config)
        if result.status != 200:
            await message.respond('Error returned from salt for runner {}: {} ({})'.format(runner, result.status, result.reason))
        else:
            result_text = await result.text()
            await message.respond(result_text)
    except LoginError:
        await message.respond('Login Error to salt. Check logs.')
