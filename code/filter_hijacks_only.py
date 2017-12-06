import pdb, collections, re , itertools
import time
from _pybgpstream import BGPStream, BGPRecord, BGPElem
from combine_id_asn import combine_id_asn
from collections import defaultdict
from get_peering_relations import get_peering_relations
import numpy as np
import matplotlib.pyplot as plt
cdn_list = ['maxcdn','cloudfare','incapsula','edgecast','cachefly','amazon','cdn77','google','akamai','cdnetworks','limelight']
asn_to_org_map = combine_id_asn()
peering_relations = get_peering_relations()

def get_duplicate_origins():
    # Create a new bgpstream instance and a reusable bgprecord instance
    stream = BGPStream()
    rec = BGPRecord()
    collectors_list= ['rrc10','rrc00','rrc00', 'rrc06', 'route-views.kixp' ]
    # Consider Singapore route view collector 
    stream.add_filter('collector','rrc10') #Italy Milan 
    # stream.add_filter('collector','rrc00')# in Amsterdam
    # stream.add_filter('collector','rrc00')# in Japan
    # stream.add_filter('collector','rrc06')# in SanJose
    # stream.add_filter('collector','route-views.kixp')#Nairobi Kenya
    # stream.add_filter('collector','route-views.sydney')# Sydney Australia
    # stream.add_filter('collector','route-views.saopaulo')# SaoPaulo

    # Consider this time interval:
    # Feb  24 18:00:00 UTC 2008 - Feb  24 20:59:11 UTC 2008
    #stream.add_interval_filter(1203876000,1203884400) # Pakistan Hijack 17557
    # April 8 15:45:00 UTC 20010 - April 8 15:59:0 UTC 20010
    #stream.add_interval_filter(1270741500,1270742340)  # China Hijack 23724
    # April 2 18:26:00 UTC 2014 - April 2 21:20:00 UTC 2014
    #stream.add_interval_filter(1396463160,1396473600) #Indonesia 4761
    # Look at Ribs data 
    #stream.add_filter('record-type','ribs')
    # Consider /22 prefix announced by youtube or more specific
    #stream.add_filter('prefix-more','208.65.152.0/22')# pakistan
    #stream.add_filter('prefix-more','63.218.188.0/22')#china
    #stream.add_filter('prefix-more','31.9.0.0/19')#indonesia
    # Start the stream

    # April 1, 2017  hour every day 
    start_apl = 1491004800
    #end_apl = 1491008400
    for time in range(1,7):
        stream.add_interval_filter(start_apl,start_apl+3600)
        start_apl += 86400

    stream.start()

    # multiple ASes announcing a prefix a prefix
    record_prefix_and_origin_ASes = collections.defaultdict(list)
    #lowest_time = 0
    # Get next record
    while(stream.get_next_record(rec)):
        # Print the record information only if it is not a valid record
        if rec.status != "valid":
            print rec.project, rec.collector, rec.type, rec.time, rec.status
        else:
            elem = rec.get_next_elem()
            while(elem):
                # Print record and elem information
                #print rec.project, rec.collector, rec.type, rec.time, rec.status,
                #print elem.type, elem.peer_address, elem.peer_asn, elem.fields
                if 'as-path' in elem.fields:

                    path_list = elem.fields['as-path'].split(" ")
                    prefix_address, network_mask= elem.fields['prefix'].split('/')

                    # if lowest_time > rec.time : 
                    #     pdb.set_trace()
                    # else:
                    #     lowest_time = rec.time

                    if  (prefix_address in record_prefix_and_origin_ASes) and (record_prefix_and_origin_ASes[prefix_address][-1][0] == path_list[-1]):
                        if rec.collector not in record_prefix_and_origin_ASes[prefix_address][-1][3] :
                            record_prefix_and_origin_ASes[prefix_address][-1][3].append(rec.collector)

                            if len (record_prefix_and_origin_ASes[prefix_address][-1][4]) < 2:
                                record_prefix_and_origin_ASes[prefix_address][-1][4].append(rec.time)
                            elif record_prefix_and_origin_ASes[prefix_address][-1][4][1] < rec.time:
                                record_prefix_and_origin_ASes[prefix_address][-1][4][1] = rec.time

                        record_prefix_and_origin_ASes[prefix_address][-1][1] += 1 # {prefix: [origin_AS,consecutive_count,prefixlen, [collector],time]}
                    else :
                        record_prefix_and_origin_ASes[prefix_address].append([path_list[-1],1,network_mask,[rec.collector], [rec.time]])

                elem = rec.get_next_elem()

    #pdb.set_trace()
    # filter prefixes from the dictionary that have more than 1 Origin Ases
    record_prefix_and_origin_ASes_suspect = {k: v for k, v in record_prefix_and_origin_ASes.items() if len(v) > 1}

    check_if_same_organization(record_prefix_and_origin_ASes_suspect)

def check_if_same_organization(record_prefix_and_origin_ASes_suspect):
    prefix_country_org= dict()
    duplicate_type_count= {'same_org':[],'cdns':[],'peer_asns':[],'hijack_or_misconfig':[]} # count of each type of duplicate 
    # compare origins
    for key, value in record_prefix_and_origin_ASes_suspect.items():
        #as list
        as_list = []
        #country list 
        country_list = []
        #organization name
        organization_list = []
        if value[0][0] in asn_to_org_map:
            country_name = asn_to_org_map[value[0][0]][3] 
            #consider the first part of the orgname only 
            org_name = asn_to_org_map[value[0][0]][2]

            if org_name != '':
                org_name = re.split('\s|-|,',asn_to_org_map[value[0][0]][2])[0]

            as_list.append(value[0][0])
            country_list.append(country_name)
            organization_list.append(org_name)

            value[0]= value[0] + [country_name, org_name]
            # compare country and org names    
            counter = 1
            for origin_as in value[1:]:
                if origin_as[0] in asn_to_org_map:
                    as_list.append(origin_as[0])
                    #check if the countries are the same 
                    country_name = asn_to_org_map[origin_as[0]][3]
                    org_name = re.split('\s|-|,',asn_to_org_map[origin_as[0]][2])[0]
                    country_list.append(country_name)
                    organization_list.append(org_name)
                    value[counter]= value[counter] + [country_name, org_name]
                counter +=1
                    #if asn_to_org_map[origin_as[0]][3] == country_name:
                
            #print ("Prefix %s is announced by ASes %s in %s"%(key, as_list,zip(country_list,organization_list)))
            #check if organization names are the same
            cdns = check_if_cdn(organization_list)
            is_same_organization = check_same_org(organization_list)
            peer_nonpeer = check_if_peers(as_list)
            if is_same_organization:
                duplicate_type_count['same_org'].append({key:value})
            #check if cdn 
            elif len(cdns) > 0: 
                print ("%s are cdns" %cdns) 
                duplicate_type_count['cdns'].append({key:value})
            #check peering relation 
            elif len(peer_nonpeer[0]) > 0:
                relevant_peers = [ org_as for org_as in value if org_as[0] in reduce(lambda x,y:x+y,peer_nonpeer[0])] 
                relevent_nonpeers = [ org_as for org_as in value if org_as[0] not in reduce(lambda x,y:x+y,peer_nonpeer[0])]
                duplicate_type_count['peer_asns'].append({key:relevant_peers})
                # if non-peers then flag 
                duplicate_type_count['hijack_or_misconfig'].append({key:relevent_nonpeers})
            else:
                duplicate_type_count['hijack_or_misconfig'].append({key:value})
    pdb.set_trace()

#check id same organization 
def check_same_org(org_list):
    cur_org = org_list[0]
    for org in org_list[1:]:
        if org != cur_org:
            return False 
    return True

def check_if_peers(as_list):
    peer_nonpeer = [[],[]]
    compare_list = list(itertools.combinations(as_list, 2))
    for pair in compare_list:
        #pdb.set_trace()
        if pair[0] in peering_relations and pair[1] in peering_relations: 
            if pair[0] in (peering_relations[pair[1]]['peer']+ peering_relations[pair[1]]['provider']+ peering_relations[pair[1]]['customer']):
                peer_nonpeer[0].append(pair)
            else:
                peer_nonpeer[1].append(pair)
    return peer_nonpeer

def check_if_cdn(org_list):
    cdns =[]
    for org in org_list:
        if org.lower() in cdn_list:
            cdns.append(org)
    return cdns

def get_plot(classification_count):
    ax.set_ylabel('Type of Conflict')
    ax.set_title('Charecterization of AS conflict')

if __name__ == "__main__":
    get_duplicate_origins()