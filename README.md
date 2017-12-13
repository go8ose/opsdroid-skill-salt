# opsdroid skill reminders

This is a skill module to allow an opsdroid bot to interact with a salt 
master.  To use it you would:
 

 1. install opsdroid, see https://opsdroid.github.io
 2. Configure this salt skill, see Configuration section below
 3. Configure appropriate ACLs on your salt master, see https://docs.saltstack.com/en/latest/topics/eauth/access_control.html
 4. Configure your salt master's salt-api, i.e. https://docs.saltstack.com/en/latest/ref/netapi/all/salt.netapi.rest_cherrypy.html
 
Once that is done your opsdroid bot will relay some messages to the salt master via the salt-api.  The goal is that via your chat system you can do anything you might do with the command line salt tools.

This comes with a very large caveat.  It might not be safe for this to be possible from a chat environment.  It's up to you to deploy suitable ACLs on your salt master.  Consider the following chat message (which this skill aims to make possible, but your ACLs should probably not make possible)

```
   salt .* cmd.run 'rm -rf /'
```

## Requirements

None.

## Configuration

Here is an example configuration:

```yaml
skills:
  - other skills... 
  - name: salt
    path:  https://github.com/go8ose/opsdroid-skill-salt.git
    url: https://salt.example.com:8000   
    username: salt-account
    password: ****
    eauth: pam
```

The username, password and eauth are used directly when communicating with the salt-api daemon.  There is also a 'verify-ssl' boolean option.  You can set that to *False* if you're using a self signed certificate on the salt-api daemon during testing.

## License

GNU General Public License Version 3 (GPLv3)

