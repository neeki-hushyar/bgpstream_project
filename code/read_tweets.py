import twitter
import sys


api_key = '3dfJyzySTem2FpmIcNivnQhTC' # consumer key
api_secret = 'kIoDvGEYVWZi77imIKD9O5twQFrEEMQRfdBeqC1LgEVd7ssJRR' # consumer secret

access_key = '938180030856867840-OImYQ0EP4VN4fckH1fjkuILbpud52T3'
access_secret = 'JsIsu53F7tSdyLbXCZnNfRUaB02VxEC5gnfCgdhZhLH0N'

api = twitter.Api(consumer_key=api_key, consumer_secret=api_secret, access_token_key=access_key, access_token_secret=access_secret)

t = api.GetUserTimeline(screen_name='bgpstream', count=24000, exclude_replies=True)
all = t
oldest = t[-1].id-1
while len(t) > 0:
    t = api.GetUserTimeline(screen_name='bgpstream', count=24000, max_id=oldest,exclude_replies=True)
    oldest = t[-1].id-1
    all += t
    break

tweets = [i.AsDict() for i in all]

results = open('results4.txt', 'r')
printed = set()
for line in results.readlines():
    if line.startswith('Prefixes'):
        parts = line.split(" ")
        prefix = parts[2].strip()[2:12]
        if len(str(prefix)) == 1:
            continue
        for i in tweets:
            if prefix in i['text']:
                print "Prefix {0} possibly hijacked".format(prefix)
                print i['text']
    if line.startswith('AS '):
        parts = line.split(" ")
        asn = parts[2]
        for i in tweets:
            if "hijacked prefix AS" + str(asn) in i['text']:
                if asn not in printed:
                    print "\nASN {0} has been flagged".format(asn)
                    print i['text']
                    printed.add(asn)
print "Total number of flagged ASes overlapping: ", len(printed)


    
