from json import loads

from helga import log
from helga.plugins.webhooks import authenticated, route


logger = log.getLogger(__name__)


# These are the only message types we care about
TYPE_MAP = {
    'incident.trigger': 'triggered',
    'incident.acknowledge': 'acknowledged by',
    'incident.unacknowledge': 'unacknowledged due to timeout',
    'incident.resolve': 'resolved',
}


@route('/pagerduty/(?P<channel>[\w\-_]+)', methods=['POST'])
@authenticated
def announce(request, irc_client, channel):
    if not channel.startswith('#'):
        channel = '#{0}'.format(channel)

    body = request.content.read()
    if not body:
        request.setResponseCode(400)
        return 'JSON payload is required'
    payload = loads(body)

    if not payload['messages']:
        return 'No messages sent'

    message = payload['messages'][-1]
    if message['type'] not in TYPE_MAP:
        return 'No messages sent'

    _type = TYPE_MAP[message['type']]
    if message['type'] == 'incident.acknowledge':
        _type = '{} {}'.format(,
            _type,
            message['data']['incident']['assigned_to_user'])

    description = 'PagerDuty alert {}: {} for {} {}'.format(
        _type,
        message['data']['incident']['trigger_summary_data']['subject'],
        message['data']['incident']['service']['name'],
        message['data']['incident']['html_url'],
    )

    logger.info('Sending message to %s: "%s"', channel, description)
    irc_client.msg(channel, description)

    # Return accepted
    return 'Message Sent'
