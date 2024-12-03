# ipv4genptrs
### create bulk $GENERATE directives for PTRs in BIND from a .xlsx spreadsheet

BC popped up the other day with a block of IPv4 subnets that they're sub-dividing to get more granular with (for geolocation among other things). He provided a simple list with the CIDRs of the new block and the corresponding PTR resolution desired.

It wasn't _difficult_ to assemble the zonefile entries by hand, but it was time-consuming. He provided 29 blocks to add, which took a couple hours to transcribe into an .xlsx (for sorting), do the range lookups with [Subnet Calculator](https://www.subnet-calculator.com/subnet.php?net_class=A), associate those ranges to the CIDR described, and hand-crafting the $GENERATE directives. As a one-off, it wasn't terrible, but he did mention that there'll be around 600 more of these to come in the not-distant future.

Manually assembling the zonefile additions isn't scalable, so this script is the result. It wants a .xlsx arranged with the CIDR in column A, and the PTR resolution template, prepended with '$-$-$-$.', in column B. It'll then output a .txt files with the $GENERATE directives for the provided CIDRs, ready for copy/paste into the target zonefiles.

2023-11-09: Leading/trailing spaces for the CIDR definition (column A) breaks the parsing. Easy fix with .strip()
2024-12-03: add getrange - a simple dump of the IP address range, given a CIDR.
