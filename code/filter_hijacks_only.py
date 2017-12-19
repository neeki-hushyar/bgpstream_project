import pdb, collections, re , itertools
import time
from _pybgpstream import BGPStream, BGPRecord, BGPElem
from combine_id_asn import combine_id_asn
from collections import defaultdict
from get_peering_relations import get_peering_relations
from functools import reduce
import collections

import matplotlib.pyplot as plt;
import numpy as np

cdn_list = ['maxcdn','cloudfare','incapsula','edgecast','cachefly','amazon','cdn77','google','akamai','cdnetworks','limelight']
#cdn_list = ['maxcdn','cloudfare','incapsula','edgecast','cachefly','amazon','cdn77','akamai','cdnetworks','limelight']
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
    #stream.add_filter('collector','rrc00')# in Japan
    #stream.add_filter('collector','rrc06')# in SanJose
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
    # for time in range(1,7):
    # 	#print(start_apl)
    #     stream.add_interval_filter(start_apl,start_apl+3600)
    #     start_apl += 86400
    #1491609600
    stream.add_interval_filter(start_apl,start_apl+ (3600*9))
    stream.start()

    # multiple ASes announcing a prefix a prefix
    record_prefix_and_origin_ASes = collections.defaultdict(list)
    #lowest_time = 0
    # Get next record
    while(stream.get_next_record(rec)):
        # Print the record information only if it is not a valid record
        if rec.status != "valid":
            print (rec.project, rec.collector, rec.type, rec.time, rec.status)
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
                    #elif (prefix_address in record_prefix_and_origin_ASes):

                    else :
                        # path can be a set or a sequence
                        origin_AS = path_list[-1]

                        if origin_AS != '' and isinstance(eval(origin_AS), (list, tuple, set )):
                            origin_AS = list(eval(origin_AS))[-1]
                            #print (origin_AS)
                        record_prefix_and_origin_ASes[prefix_address].append([origin_AS,1,network_mask,[rec.collector], [rec.time]])

                elem = rec.get_next_elem()

    
    # filter prefixes from the dictionary that have more than 1 Origin Ases
    record_prefix_and_origin_ASes_suspect = {k: v for k, v in record_prefix_and_origin_ASes.items() if len(v) > 1}
    check_if_same_organization(record_prefix_and_origin_ASes_suspect)

def check_if_same_organization(record_prefix_and_origin_ASes_suspect):
    prefix_country_org= dict()
    duplicate_type_count= {'same_org':[],'same_cntry': [],'cdns':[],'peer_asns':[],'hijack_or_misconfig':[],'traffic_eng':[] ,'not_in_caida': [] } # count of each type of duplicate 
    # compare origins
    for key, value in record_prefix_and_origin_ASes_suspect.items(): 
        #as list
        as_list = []
        #country list 
        country_list = []
        #organization name
        organization_list = []
        if value[0][0] not in asn_to_org_map:
            country_name = "N/A"
            org_name  = "N/A"
        else: 
            country_name = asn_to_org_map[value[0][0]][3] 
            #consider the first part of the orgname only 
            org_name = asn_to_org_map[value[0][0]][2]

        # if org_name != '' and org_name != "N/A":
        #     org_name = re.split('\s|-|,',asn_to_org_map[value[0][0]][2])[0]


        as_list.append(value[0][0])
        country_list.append(country_name)
        organization_list.append(org_name)

        value[0]= value[0] + [country_name, org_name]
        # compare country and org names    
        counter = 1
        for origin_as in value[1:]:
            if origin_as[0] in asn_to_org_map:
                country_name = asn_to_org_map[origin_as[0]][3]
                org_name = asn_to_org_map[origin_as[0]][2]
                #org_name = re.split('\s|-|,',asn_to_org_map[origin_as[0]][2])[0]
             
            else: 
                country_name = "N/A"
                org_name = "N/A"
            as_list.append(origin_as[0])
            country_list.append(country_name)
            organization_list.append(org_name)
            value[counter]= value[counter] + [country_name, org_name]
            counter +=1
            
        #print ("Prefix %s is announced by ASes %s in %s"%(key, as_list,zip(country_list,organization_list)))
        #check if organization names are the same
        cdns = check_if_cdn(organization_list)
        is_same_organization = check_same_org(organization_list)
        is_same_country = check_same_country(country_list)
        peer_nonpeer = check_if_peers(as_list)
        #check if cdn 
        if len(cdns) > 0: 
            #print ("%s are cdns" %cdns) 
            duplicate_type_count['cdns'].append({key:value})

        #check same organization
        elif is_same_organization:
            duplicate_type_count['same_org'].append({key:value})

        #check if same country
        elif is_same_country:
            duplicate_type_count['same_cntry'].append({key:value})

        #check peering relation 
        elif len(peer_nonpeer[0]) > 0:
            relevant_peers = [ org_as for org_as in value if org_as[0] in reduce(lambda x,y:x+y,peer_nonpeer[0])] 
            duplicate_type_count['peer_asns'].append({key:relevant_peers}) 
        #discount traffic engineering based on duration less than an hour of announcement  
        elif is_traffic_eng(value):
            duplicate_type_count['traffic_eng'].append({key:value})
        elif len(peer_nonpeer[1]) > 0:
             # relevent_nonpeers = [ org_as for org_as in value if org_as[0] not in reduce(lambda x,y:x+y,peer_nonpeer[0])]
            duplicate_type_count['hijack_or_misconfig'].append({key:value})
        elif len(value) >= 2: 
            duplicate_type_count['hijack_or_misconfig'].append({key:value})
        else:
            #record not found in CAIDA
            duplicate_type_count['not_in_caida'].append({key:value})
    #pdb.set_trace()
    get_plot_type(duplicate_type_count)
    get_plot_duration(duplicate_type_count['hijack_or_misconfig'])
    #pdb.set_trace()

def check_same_country(country_list):
    cur_country = country_list[0]
    for cntry in country_list[1:]:
        # see a single occurence of different country 
        if cntry != "N/A" and cntry!= cur_country: 
            return False 
    return True


#check for traffic engineering 
def is_traffic_eng(as_records):
    
    origin_announcement_times = collections.defaultdict(list)
    for as_orig in as_records:
        origin_announcement_times[as_orig[6]].extend(as_orig[4])
    #assuming hijack doesnt last for more than an hour 
    #both present at start and at end and the length greater than an hour TODO 60 s right now 
    if (origin_announcement_times[origin_announcement_times.keys()[0]][0] - origin_announcement_times[origin_announcement_times.keys()[0]][-1] )> 3600:
    	pdb.set_trace()#sanity check
    if abs((origin_announcement_times[origin_announcement_times.keys()[0]][-1] - origin_announcement_times[origin_announcement_times.keys()[-1]][-1])) > 180:
        return False

    return True 

#check id same organization 
def check_same_org(org_list):
    cur_org = re.split('\s|-|,',org_list[0])[0]
    #cur_org = org_list[0]
    for org in org_list[1:]:
        if re.split('\s|-|,',org)[0] != "N/A" and re.split('\s|-|,',org)[0]!= cur_org:
            return False 
    return True

def check_if_peers(as_list):
    peer_nonpeer = [[],[]]
    compare_list = list(itertools.combinations(as_list, 2))
    for pair in compare_list:
        if pair[0] in peering_relations and pair[1] in peering_relations and pair[0]!=pair[1]: 
            if pair[0] in (peering_relations[pair[1]]['peer']+ peering_relations[pair[1]]['provider']+ peering_relations[pair[1]]['customer']):
                peer_nonpeer[0].append(pair)
            else:
                peer_nonpeer[1].append(pair)
    return peer_nonpeer

def check_if_cdn(org_list):
    cdns =[]
    for org in org_list:
        if org.lower() in cdn_list or 'cloud' in org.lower():
            cdns.append(org)
    return cdns

def get_plot_type(duplicate_type_count):
    plot_name = {'same_org': "Same Organization",'same_cntry': "Same Country",'cdns':"CDN",'peer_asns':"Peer ASN",'hijack_or_misconfig':"Hijack or Misconfig", 'traffic_eng' : "Traffic Engineering"}
    #'not_in_caida': "Not in CAIDA"
    y_pos_short_name = list(duplicate_type_count.keys())
    y_pos = []
    for shrt_name in y_pos_short_name:
        if shrt_name != 'not_in_caida':
            y_pos.append(plot_name[shrt_name])

    performance = []
    for conflict_type in y_pos_short_name:
         if conflict_type != 'not_in_caida':
            performance.append(len(duplicate_type_count[conflict_type]))
    #pdb.set_trace()
    fig, ax = plt.subplots()
    rects = ax.bar(y_pos, performance, align = 'center', alpha = 0.5)
    ax.set_xlabel('Number of Occurences', fontsize = 10)
    ax.set_ylabel('Type of Conflict',fontsize = 10)
    ax.set_title('Charecterization of AS conflict')
    
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.01*height,
                '%d' % int(height),
                ha='center', va='bottom')

    plt.tick_params(labelsize = 5.5)
    plt.savefig('../figure/AS_Origin_Conflict_Types.png')
    plt.close()

def get_plot_duration(duration_list):
     #get a list of duration 
    durations = []
    country_list = []
    for prefix in duration_list:
        announcement_start = 0 
        first_origin = prefix.values()[0][0][0]
        origin_reappeared = False
        diff_origin_detected = False
        for origin_as in prefix.values()[0]:
            if origin_as[0] != first_origin and (not diff_origin_detected):
                diff_origin_detected = True 
                announcement_start = origin_as[4][-1]

            elif origin_as[0] == first_origin and diff_origin_detected and origin_as[4][-1]!= announcement_start :
                durations.append( origin_as[4][-1]- announcement_start)
                origin_reappeared = True
                break
            if origin_as[5] != 'N/A' and origin_as[5] != '' and origin_as[5] != ' ':
                country_list.append(origin_as[5])
        if not origin_reappeared:
            durations.append(float('inf'))      
    # Use the histogram function to bin the data
    durations_curated = np.sort([dur for dur in durations if dur != float('inf')])
    
    #counts, bin_edges = np.histogram(durations_curated, bins=len(durations_curated), normed=True)

     # Now find the cdf
    #cdf = np.cumsum(counts)/len()
    cdf = 1. * np.arange(len(durations_curated)) / (len(durations_curated) - 1)
     # And finally plot the cdf
    plt.plot(durations_curated, cdf)
    plt.xlabel('Duration of hijack in seconds (s)', fontsize = 10)
    plt.ylabel('CDF',fontsize = 10)
    plt.title('CDF of the Duration of Hijack in seconds')
    plt.savefig('../figure/Duration_of_hijack.png')
    plt.close()
    plot_country(country_list)
    pdb.set_trace()

def plot_country(country_list):
    counter =collections.Counter(country_list)
    counter = counter.most_common(10)
    plt.bar([country for country, count  in counter], [count for country, count  in counter])
    plt.xlabel('Country', fontsize = 10)
    plt.ylabel('Number of occurences',fontsize = 10)
    plt.title('Number of hijack and/or misconfig by country')
    plt.savefig('../figure/Occurences_by_country.png')
    plt.close()

if __name__ == "__main__":
    get_duplicate_origins()