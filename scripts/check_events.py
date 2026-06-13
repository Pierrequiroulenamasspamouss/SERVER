import json, time

with open(r'c:\Unity\SERVER\data\definitions.json', 'r') as f:
    data = json.load(f)

events = data.get('timedSocialEventDefinitions', [])
now = int(time.time())
print("Current Unix time:", now, "=", time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(now)))
print("Total events:", len(events))
print()
for e in events[:5]:
    start = e.get('startTime', 0)
    finish = e.get('finishTime', 0)
    active = start <= now <= finish
    print("ID=%4d  start=%d (%s)  finish=%d (%s)  ACTIVE=%s" % (
        e['id'], start, time.strftime("%Y-%m-%d", time.gmtime(start)),
        finish, time.strftime("%Y-%m-%d", time.gmtime(finish)), active))

active_events = [e for e in events if e.get('startTime',0) <= now <= e.get('finishTime',0)]
print("\nCurrently active events:", len(active_events))
for e in active_events:
    print("  -> ID=%d from %s to %s" % (e['id'], time.strftime("%Y-%m-%d", time.gmtime(e['startTime'])), time.strftime("%Y-%m-%d", time.gmtime(e['finishTime']))))
