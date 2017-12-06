from _pybgpstream import BGPStream, BGPRecord, BGPElem
from datetime import datetime
from collections import defaultdict
import time
import sys
import os


def identify_relationships(ases, direct_only=0):
    '''
    Find out if any of the ases announcing a prefix do not have a relationship to
    the others.
    '''
    graph = defaultdict(set)
    add_pre = "../data/relationships/"
    files = os.listdir("../data/relationships")
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

    if direct_only:
        # rasies flag if announcing prefix is not direct peer of another announcing prefix
        for k, v in graph.items():
            if len(v) != len(set(ases)):
                print "No direct relationships between {0} and {1}".format(k, v-set(ases))
        return

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


# i don't want to keep opening and reading these files
# hopefully all data can be stored
add_pre = "../data/as_maps/"
files = os.listdir("../data/as_maps")
asn_to_id = dict()
id_to_country = dict()
id_to_org = dict()
for each_file in files:
    if not each_file.endswith("txt"):
        continue
    op = open(add_pre + each_file, "r").readlines()
    for line in op:
        if line.startswith("#"):
            continue
        parts = line.split("|")
        first = parts[0]
        if first.isdigit():
            id = parts[3]
            asn_to_id[first] = id
        else:
            country = parts[3]
            org = parts[2]
            id_to_country[first] = country
            id_to_org[first] = org


graph = defaultdict(set)
add_pre = "../data/relationships/"
files = os.listdir("../data/relationships")
for each_file in files:
    if not each_file.endswith("txt"):
        continue
    op = open(add_pre + each_file, "r").readlines()
    for line in op:
        if line.startswith("#"):
            continue
        parts = line.split("|")
        as1 = int(parts[0])
        as2 = int(parts[1])
        graph[as1].add(as2)
        graph[as2].add(as1)

def check_asn_owner(origins, prefix):
    # returns 0 if prefixes are questionable
    ccs, orgs = set(), set()
    cc_to_count = dict()
    for asn in origins.keys():
        try:
            asn_id = asn_to_id[asn]
            cc = id_to_country[asn_id]
            org = id_to_org[asn_id]
            cc_to_count[cc] = origins[asn]
            ccs.add(cc)
            orgs.add(org)
        except KeyError: # asn DNE
            del origins[asn]
            continue
    if len(ccs) == 0 or len(orgs) == 0:
        print "No info for origins: {0}".format(origins.keys())
        return 1
    if len(ccs) == 1: # all from same country
        return 1
    if len(orgs) == 1: # asns coming from different countries and different orgs
        print "\nASes may be part of CDN"
        return 1

    prefix_country = None
    content = os.popen('whois {0}'.format(prefix)).read().split("\n")
    for i in content:
        if i.startswith("country"):
            prefix_country = i.split(":")[1].strip()


    flag = 1
    max_asn = max(origins, key=origins.get)
    # only important than non-majority announcing countries are the same as the country in
    # which the prefix is owned
    if prefix_country is not None:
        for asn in origins.keys():
            if max_asn == asn:
                # small countries may use ASes larger coutnreis to make most of their annoucnements
                continue # doesn't matter the country which announces the most 
            asn_id = asn_to_id[asn]
            cc = id_to_country[asn_id]
            if prefix_country == cc:
                continue
            flag = 0
    if flag:
        return 1 # confirmed that lesser annoucnements are coming from the country owning the prefix
    
        
    flag = 1
    for asn1 in origins.keys():
        for asn2 in origins.keys():
            if asn1 == asn2:
                continue

            try:
                if asn1 not in graph[asn2]:
                    asn_id1 = asn_to_id[asn1]
                    cc1 = id_to_country[asn_id1]
                    asn_id2 = asn_to_id[asn2]
                    cc2 = id_to_country[asn_id2]
                    if cc1 == cc2: # same country - allow announcements ?
                        continue
                    flag = 0 # otherwise conflicting annoucnements are bad
                    if prefix_country is not None:
                        print "Prefix owned by: {0}".format(prefix_country)
                    print "{0}-{1} and {2}-{3} announced similar prefixes but are not peers/from same country".format(asn1, cc1,  asn2, cc2)

            except KeyError:
                continue
    return flag
        


        

def identify_overlapping_prefixes(d, path_dict):
    # identify asns which announce varying lengths of prefixes
    # check the origins of the difference prefix lengths
    overlap = defaultdict(list)
    for k, _ in d.items():
        first_24 = ".".join(k.split(".")[:3])
        overlap[first_24].append(k)
        
    ctr = 0
    for k, v in overlap.items():
        prefix = k + '.0'
        if len(v) > 1:
            origins = defaultdict(int)
            for prefix in v:
                paths = path_dict[prefix]
                for path in paths:
                    origins[path.strip().split(" ")[-1]] += 1
            if len(origins.items()) > 1:
                    valid = check_asn_owner(origins, prefix)
                    if not valid:
                        ctr += 1
                        print "Prefixes: ", list(v)
                        for origin, count in origins.items():
                            print "AS - {0} has {1} listings".format(origin, count)
                        print "\n\n"
    print "Total prefixes checked: {0}".format(len(overlap.items()))
    print "Prefixes flagged: {0}".format(ctr)
        


def confirm_connected(d, direct=0):
    # find out if all asns announcing some prefix are connected (directly or indirectly)
    for k, v in d.items():
        if len(v) > 1:
            #print "{0}: {1}".format(k, list(v))
            print "Prefix: {0}".format(k)
            identify_relationships(list(v), direct)

def find_inconsistencies(path_dict):
    # raises flag if among different paths - the origin AS shows up as non-origin AS
    # path_dict maps prefixes to all announced AS paths
    ctr = 0
    for k, v in path_dict.items():
        og_v = v
        flag = 1
        comp = list()
        for path in v:
            comp.append(path.strip().split(" "))
        v = comp
        origins = set()
        for path in v:
            origins.add(path[-1])
        #if len(origins) > 1:
            #print "Multiple origins for {0} - {1}".format(k, list(origins))
        origins = list(origins)
        conflicts = defaultdict(set)
        for path in v:
            for origin in origins:
                if origin in path[:-1] and origin != path[-1]:
                    conflicts[origin].add(" ".join(path))
        
        if len(conflicts.items()) > 0:
            #print "\n\nPrefix: {0}, Paths: {1}".format(k, og_v)
            for k, v in conflicts.items():
                print "Origin {0} exists as non-origin in {1}".format(k, v)
            ctr += 1


def main():
    '''
    Colllect and organize data from stream of BGP data from range of collectors
    over range of time (currently 2 minutes of every hour for one day).
    '''
    stream = BGPStream()
    rec = BGPRecord()
    d = defaultdict(set) # prefix -> asn
    # choose collectors
    filters = ['route-views2', 'route-views3', 'route-views4', 'route-views6', 'rrc00', 'rrc01', 'rrc02', 'rrc03', 'rrc04', 'rrc05', 'rrc06', 'rrc10', 'route-views.kixp', 'route-views.sydney', 'route-views.saopaulo']
    for filter in filters:
        stream.add_filter("collector", filter)
    # collect data
    path_dict = defaultdict(set)
    for m in [1]:
    #for m in ['01', '02', '03', '04', '04', '05', '06', '07', '08', '09', '10', '11', '12']:
        for day in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30']:

            t1 = datetime.strptime("2017-04-{0} 00:00:01 UTC".format(day), "%Y-%m-%d %H:%M:%S %Z")
            t1 = int(time.mktime(t1.timetuple()))

            t2 = datetime.strptime("2017-04-{0} 0:59:59 UTC".format(day), "%Y-%m-%d %H:%M:%S %Z")
            t2 = int(time.mktime(t2.timetuple()))

            stream.add_filter("record-type", "ribs")
            stream.add_interval_filter(t1, t2)
            stream.start()

            while stream.get_next_record(rec):
                #print rec.status, rec.project + "." + rec.collector, rec.time
                elem = rec.get_next_elem()
                while elem:
                    #print "Type: {0}".format(elem.type)
                    #print "Peer Address: {0}".format(elem.peer_address)
                    #print "Peer ASN: {0}".format(elem.peer_asn)
                    prefix = None
                    path = None
                    for k, v in elem.fields.items():
                        #print "{0}: {1}".format(k, v)
                        if k == "prefix":
                            prefix = v
                            #if "208.65.152" in prefix:
                                #print "PAKISTAN HIJACK"
                                #print elem.fields.items()
                        if k == "as-path":
                            path = v
                            
                    if prefix:
                        d[prefix].add(elem.peer_asn)
                    if path:
                        path_dict[prefix].add(path)
                    #print ""
                    elem = rec.get_next_elem()
    return d, path_dict

if __name__=='__main__':
    d, path_dict = main()
    #find_inconsistencies(path_dict)
    identify_overlapping_prefixes(d, path_dict)
    #confirm_connected(d, 1)
