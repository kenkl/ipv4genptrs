#!/usr/bin/env python3

import ipaddress,openpyxl
from sys import argv

def get_range(cidr_notation):
    try:
        # Parse the CIDR notation to get the network object
        network = ipaddress.IPv4Network(cidr_notation, strict=False)
        #first_usable_ip = network.network_address + 1  # this is *usable*, but misses gateway/router in our implementation
        first_usable_ip = network.network_address 
        last_usable_ip = network.broadcast_address - 1

        return str(first_usable_ip), str(last_usable_ip)
    except ValueError as e:
        return str(e)

def build_list(workbook):
    '''Build/return a list with the contents of the entire spreadsheet (first/named tab only)'''
    wb=openpyxl.load_workbook(workbook)
    sheet=wb.worksheets[0] # we're only going to pull from the first sheet in the workbook, regardless of its name
    snrow = [] #empty list to fill with rows/colums from the spreadsheet
    rows = sheet.max_row
    for r in range(1, rows+1):
        sncidr = sheet.cell(r,1).value
        sncidr = sncidr.strip()
        snname = sheet.cell(r,2).value
        snname = snname.strip()
        row = [sncidr, snname]
        snrow.append(row)

    # blank rows return 'None'. Let's clean those up...
    flist = []
    for r in range(len(snrow)):
        if snrow[r][0] is not None:
            flist.append(snrow[r])

    return flist

def make_gens(snlist):
    # snlist is the basic list with CIDR,subnet name. For CIDRs that span multiple /24s (different 3rd octet)
    # generate one $GENERATE line per /24. We append a list of gen-strings (and their 3rd-octet) at index 2.
    for r in range(len(snlist)):
        first, last = get_range(snlist[r][0])
        fparts = str(first).split('.')
        lparts = str(last).split('.')
        f3 = int(fparts[2])
        f4 = int(fparts[3])
        l3 = int(lparts[2])
        l4 = int(lparts[3])

        genlist = []
        # iterate over every 3rd-octet spanned by the range
        for third in range(f3, l3 + 1):
            if third == f3:
                low = f4
            else:
                low = 0
            if third == l3:
                high = l4
            else:
                high = 255
            # Leave the PTR name part out for now; it will be appended in make_copypasta after sanitizing the name
            gen = f'$GENERATE {low}-{high}     $    PTR    '
            genlist.append((third, gen))

        snlist[r].append(genlist)
    return snlist

def sanitize_snname(cidr, snname):
    # using the first 3 octets of the cidr, prepend the standardized wildcard designation for the name.
    #newsnname = '$.'
    octetlist = cidr.split('.')
    # newsnname: e.g. '192-168-0-$.example.com'
    # assume incoming snname includes a leading '$-$-$-$.' prefix; keep the remainder after that prefix
    newsnname = octetlist[0] + '-' + octetlist[1] + '-' + octetlist[2] + '-$.' + snname[8:]
    # the PTR name/directive MUST end with a '.', so...
    if newsnname[-1] != '.':
        newsnname += '.'
    return newsnname

def add_snname(snlist):
    # take the subnet name (element 1) in the list and parse it to build a reasonable wildcard with the last octet as a variable
    # like: $.47.168.192.kenkl.org
    for r in range(len(snlist)):
        snname = snlist[r][1]
        # if make_gens created multiple generate entries, sanitize a name for each third-octet
        if isinstance(snlist[r][2], list):
            names = []
            # each entry in snlist[r][2] is a tuple (third_octet, genstring)
            for third, _gen in snlist[r][2]:
                # construct a /24-like cidr for the specific third octet so sanitize_snname picks the correct octet
                base_cidr = '.'.join(snlist[r][0].split('.')[:2] + [str(third), '0'])
                names.append(sanitize_snname(base_cidr, snname))
            snlist[r].append(names)
        else:
            snlist[r].append(sanitize_snname(snlist[r][0], snname))

    return snlist

def make_copypasta(snlist):
    # take the assembled/calculated $GENERATE bits and dump them to a file, ready to copypasta to the zonefile of interest.
    cp = open(outfile, 'w')
    cp.write('# some tasty copypasta for whichever zonefiles get these.\n\n')
    for r in range(len(snlist)):
        gens = snlist[r][2]
        names = snlist[r][3]
        # gens may be a single string (old style) or a list of (third, gen) tuples
        if isinstance(gens, list):
            # names is a list of sanitized names aligned with gens
            for i, (third, gen) in enumerate(gens):
                line = gen + names[i] + '\n'
                cp.write(line)
        else:
            line = gens + names + '\n'
            cp.write(line)
    cp.close()
    print(f"{outfile} has been assembled for copypasta fun-times. Enjoy!")

def main():
    # tying together all the bits to do A Thing™
    # First, let's build a list of the CIDRs and wildcard assignments, based on the .xlsx named up top
    snlist = build_list(workbook)
    # For each row, let's calculate the IPs for the CIDR, and append a list item for each with the $GENERATE prefix
    snlist = make_gens(snlist)
    # Next, let's spin through the rows again to tack on the subnet name. 
    snlist = add_snname(snlist)
    # Finally, let's take the assembled list (containing the zonefile elements), and dump it to a file (named above) for copypasta goodness.
    make_copypasta(snlist)

if __name__ == "__main__":
    global workbook, outfile
    try:
        workbook = argv[1]
    except:
        print('Useage: ipv4genptrs.py <workbook.xlsx>')
        print('where workbook.xlsx contains the PTR zones to be created\n')
        exit(1)
    outfile = workbook[:len(workbook)-5] + '.txt'
    main()
