# BGPStream

## Motiviation

In this project we will use BGPStream to identify cases in which a entity has corrupted routing tables by adveritising false routes. In this case, two or more autonomous systems would be announcing the same IP address as their own. To identify weaknesses in the inter-domain routing, the reasons for these conflicts must be identified.

## Resources and Methodology

BGPStream contains measurement data from the Border Gateway Protocol (BGP).
* We will automate a program which will analyze historical data in search of conflicts.
* We will take into consideration, cases in which two automous systems advertise the same IP address at different times, which would not conflict.
* We will identify any disruptions caused by malciious or accidental conflicting network advertisements. 

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

A case of multiple autonomous systems announcing the same IP address can happen as a result of malcious actions or genuine mistakes. We will identify these and other possible reasons for this corruption.

### Contributors
Angela Upreti
Neeki Hushyar