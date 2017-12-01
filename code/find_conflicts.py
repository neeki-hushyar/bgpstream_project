from _pybgpstream import BGPStream, BGPRecord, BGPElem
from datetime import datetime
from collections import defaultdict
import time
import sys
import os


def identify_relationships(ases):
    '''
    Find out if any of the ases announcing a prefix do not have a relationship to
    the others.
    '''
    graph = defaultdict(set)
    add_pre = "../data/"
    files = os.listdir("../data")
    for each_file in files:
        if not each_file.endswith("txt"):
            continue
        #print "reading file: ", each_file
        op = open(add_pre + each_file, "r").readlines()
        for line in op:
            if line.startswith("#"):
                continue
            parts = line.split("|")
            as1 = int(parts[0])
            as2 = int(parts[1])
            # ignore relationship type for now
            # just confirm connection exists
            if as1 in ases:
                if as2 in ases:
                    graph[as1].add(as2)
                    graph[as2].add(as1)

    flag = 0 
    for each_as in ases:
        connections = dfs(each_as, graph, [])
        conflicting = list(set(connections) - set(ases))
        if len(conflicting) > 0:
            print "AS #{0} has unexpected conflict with {1}".format(each_as, conflicting)
            flag = 1
    if flag == 0:
        print "No conflicts found"

def dfs(each_as, graph, visited):
    # determine connectedness
    visited.append(each_as)
    for each_peer_as in graph[each_as]:
        if each_peer_as not in visited:
            visited = dfs(each_peer_as, graph, visited)
    return visited

stream = BGPStream()

rec = BGPRecord()

# convert time
d = defaultdict(set) # prefix -> asn
filters = ['route-views2', 'route-views3', 'route-views4', 'route-views6', 'rrc00', 'rrc01', 'rrc02', 'rrc03', 'rrc04', 'rrc05', 'rrc06']

for filter in filters:
    for t in ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']:
        t1 = datetime.strptime("2015-04-01 {0}:02:30".format(t), "%Y-%m-%d %H:%M:%S")
        t1 = int(time.mktime(t1.timetuple()))
        t2 = datetime.strptime("2015-04-01 {0}:04:30".format(t), "%Y-%m-%d %H:%M:%S")
        t2 = int(time.mktime(t2.timetuple()))

        stream.add_filter("collector", filter)
        stream.add_filter("record-type", "updates")
        stream.add_interval_filter(1427846570, 1427846670)
        stream.start()

        while stream.get_next_record(rec):
            #print rec.status, rec.project + "." + rec.collector, rec.time
            elem = rec.get_next_elem()
            while elem:
                #print "Type: {0}\nPeer Address: {1}\nPeer ASN: {2}".format(elem.type, elem.peer_address, elem.peer_asn)

                prefix = None
                for k, v in elem.fields.items():
                    #print "{0}: {1}".format(k, v)
                    if k == "prefix":
                        prefix = v
                if prefix:
                    d[prefix].add(elem.peer_asn)
                #print ""
                elem = rec.get_next_elem()

for k, v in d.items():
    if len(v) > 1:
        #print "{0}: {1}".format(k, list(v))
        print "Prefix: {0}".format(k)
        identify_relationships(list(v))


