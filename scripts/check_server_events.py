import json, time
d = json.load(open('/opt/minions/definitions.json'))
events = d.get('timedSocialEventDefinitions', [])
now = int(time.time())
active = [e for e in events if e.get('startTime', 0) <= now <= e.get('finishTime', 0)]
print('Total events:', len(events))
print('Active now:', len(active))
for e in active:
    print('  ID=%d start=%d finish=%d' % (e['id'], e['startTime'], e['finishTime']))
if not active:
    print('Current time:', now)
    if events:
        first = events[0]
        print('First event start=%d finish=%d' % (first['startTime'], first['finishTime']))
