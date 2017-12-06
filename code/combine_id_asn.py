import os
from collections import defaultdict
import pdb
def  combine_id_asn():
    add_pre = "../data/as_maps/"
    files = os.listdir("../data/as_maps")
    asn_to_org_map  = defaultdict()
    at_org = False
    at_asn = False
    start_data = False 

    for file in files:
        if not file.endswith("txt"):
            continue
        op = open(add_pre + file, "r").readlines()
        for line in op:

            if line.startswith("#") and not ( line.startswith("# format:aut") or  line.startswith("# format:org_id")) and not start_data :
                continue
            elif line.startswith("# format:aut") and line.startswith("# format:org_id"):
            	start_data = True 

            if line.startswith("# format:aut"):
                at_asn = True
                at_org = False
                continue
            elif line.startswith("# format:org_id"):
                at_org = True
                at_asn = False
                continue

            parts = line.split("|")
            #print (parts)
            # if parts == ['# name: AS Org\n']:
            #     pdb.set_trace()

            if at_org:
               #{'org_id': [changed, org_name, country, source, aut, name, source]}
                if parts[0] in asn_to_org_map:
                   # if parts[0] == '@aut-17557-APNIC':
                   #     pdb.set_trace()
                   asn_to_org_map[parts[0]][0]= parts[1]
                   asn_to_org_map[parts[0]][1]= parts[2]
                   asn_to_org_map[parts[0]][2]= parts[3]
                   asn_to_org_map[parts[0]][3]= parts[4]
                else:
                   asn_to_org_map[parts[0]]=[parts[1],parts[2],parts[3],parts[4],[0],0,0]

            elif at_asn:
                if parts[3] in asn_to_org_map:
                   # if parts[3] == '@aut-17557-APNIC' and asn_to_org_map[parts[3]][4] == '45595':
                   #     pdb.set_trace()
                   asn_to_org_map[parts[3]][4].append(parts[0])
                   asn_to_org_map[parts[3]][5]= parts[2]
                   asn_to_org_map[parts[3]][6]= parts[4]
                else:
                   asn_to_org_map[parts[0]]=[0,0,0,0,[parts[0]],parts[2],parts[4]]
    
    asn_to_org_map_new = dict()
    for k,v in asn_to_org_map.items():
        for val in v[4]:
            asn_to_org_map_new[val] = [k]+ v[:4] + v[5:]
    #pdb.set_trace()
    return asn_to_org_map_new

if __name__ == "__main__":
    combine_id_asn()