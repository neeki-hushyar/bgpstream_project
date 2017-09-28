# Using BGPStream to Identify BGP Hijack and Other BGP routing-table trends 

## Motivation

In this project we will use BGPStream to identify cases in which an entity has corrupted routing tables by advertising false routes. In this case, two or more autonomous systems would be announcing the same IP address as their own. We will look for cases where a longer prefix is announced by an AS that is in a different country and is registered with a different email domain. We can examine whois record for the ASes involved to spot differences and identify a hijack. In our paper, we will also investigate and include ways to prevent such hijack. Our motivation is to understand weaknesses in the BGP interdomain routing and study possible solutions.

## Resources and Methodology

BGPStream contains measurement data from the Border Gateway Protocol (BGP). It provides an easy to use API for studying BGP. 
* We will automate a python program which will analyze historical data in search of conflicts.
* We will take into consideration, cases in which two autonomous systems advertise the same IP address and the ASes belong to the same organization. 
* We will look at whois record for the ASes with same the prefix to spot hijacking. 
* We will identify any disruptions caused by malicious or accidental conflicting network advertisements. 

## Timeline
The below dates are deadlines.
* 10/15: Familiarize with API
* 10/15: Problem framing
* 11/1: Parse historical data
* 11/1: Find conflicting IP advertisements
* 11/1: Midterm project report
* 11/15: Further analysis and interpretation
* 12/1: Complete final report

## Outcome 
A case of multiple autonomous systems which very different whois records announcing the same IP address can happen as a result of malicious actions or genuine mistake. We will identify these and other possible reasons for this corruption. We will analyze the cases we identify and point out any trends that we see in the way a BGP hijack occurs. In addition, we will also try to link these hijacking events to the socio-political situations during the hijack. We will study and propose ways to prevent such hijacking. The outcome will be paper that identifies BGP hijacks, studies statistical and socio-political trends in such hijacks and proposes ways to prevent them.

### Contributors
Angela Upreti
Neeki Hushyar
