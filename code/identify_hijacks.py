
# Sample 3 different week's worth of data
# Include in our samples (1) Feb 24 2008 pakistan telecom  (2) More recent dates 
# Collect data with BGP stream 
# Identify instances of multiple ASes announcing the same prefix 
# Rule out prefixes belonging to the same organization  announced in different places
# Identify if peering relation via CAIDA database
# Verify with ground truth, i.e bgpstream twitter account 
# Make this work for pakistan Hijack

#1203878820
#1203878940
#!/usr/bin/env python

import pdb, collections
from _pybgpstream import BGPStream, BGPRecord, BGPElem

# Create a new bgpstream instance and a reusable bgprecord instance
stream = BGPStream()
rec = BGPRecord()
collectors_list= ['rrc10','rrc00','rrc00', 'rrc06', 'route-views.kixp' ]
# Consider Singapore route view collector 
stream.add_filter('collector','rrc10') #Italy Milan 
stream.add_filter('collector','rrc00')# in Amsterdam
stream.add_filter('collector','rrc00')# in Japan
stream.add_filter('collector','rrc06')# in SanJose
stream.add_filter('collector','route-views.kixp')#Nairobi Kenya
stream.add_filter('collector','route-views.sydney')# Sydney Australia
stream.add_filter('collector','route-views.saopaulo')# SaoPaulo

# Consider this time interval:
# Feb  24 18:45:11 UTC 2008 - Feb  24 20:59:11 UTC 2008
#stream.add_interval_filter(1203878700,1203884400) # Pakistan Hijack
stream.add_interval_filter(1270741500,1270742340)  # China Hijack 

# Look at Ribs data 
#stream.add_filter('record-type','ribs')
# Consider /22 prefix announced by youtube or more specific
#stream.add_filter('prefix-more','208.65.152.0/22')# pakistan
#stream.add_filter('prefix-more','66.174.161.0/24')#china

# Start the stream
stream.start()

# multiple ASes announcing a prefix a prefix
record_prefix_and_origin_ASes = collections.defaultdict(list)

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

	            if  (prefix_address in record_prefix_and_origin_ASes) and (record_prefix_and_origin_ASes[prefix_address][-1][0] == path_list[-1]):
	                record_prefix_and_origin_ASes[prefix_address][-1]= [path_list[-1],record_prefix_and_origin_ASes[prefix_address][-1][1]+1,network_mask]
	            else :
	                record_prefix_and_origin_ASes[prefix_address].append([path_list[-1],1,network_mask])

            elem = rec.get_next_elem()

# filter prefixes from the dictionary that have more than 1 Origin Ases
record_prefix_and_origin_ASes_suspec = {k: v for k, v in record_prefix_and_origin_ASes.items() if len(v) > 1}
pdb.set_trace()