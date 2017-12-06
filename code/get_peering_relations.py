import os, pdb
from collections import defaultdict
def get_peering_relations():
    as_peering_map = defaultdict()
    add_pre = "../data/relationships/"
    #files = os.listdir("../data/relationships")
    files = ["20171001.as-rel2.txt"]
    for file in files:
        if not file.endswith("txt"):
            continue
        op = open(add_pre + file, "r").readlines()
        for line in op:
            if line.startswith("#"):
                continue            
            # if len(line.split("|")) > 4 :
            # pdb.set_trace()
            as1,as2,rel_type,source = line.split("|") # as,as, relation, source
            if as1 not in as_peering_map:
                as_peering_map[as1] = {'peer':[], 'provider':[], 'customer':[]}
            if as2 not in as_peering_map:
                as_peering_map[as2] = {'peer':[], 'provider':[], 'customer':[]}        
                    
            if rel_type == "0":
                #pdb.set_trace()
                if as2 not in as_peering_map[as1]['peer']:
                    as_peering_map[as1]['peer'].append(as2)

                if as1 not in as_peering_map[as2]['peer']:
                    as_peering_map[as2]['peer'].append(as1)

            elif rel_type == "-1":
            	if as1 not in as_peering_map[as2]['provider']:
                     as_peering_map[as2]['customer'].append(as1)
            	if as2 not in as_peering_map[as1]['customer']:
                    as_peering_map[as1]['customer'].append(as2)
                # if as1 not in as_peering_map[as2]['provider']:
                #      as_peering_map[as2]['customer'].append(as1)
                # if as1 not in as_peering_map[as2]['provider']:
                #     as_peering_map[as2]['provider'].append(as1)
    #pdb.set_trace()
    return as_peering_map
if __name__=="__main__":
    get_peering_relations()
