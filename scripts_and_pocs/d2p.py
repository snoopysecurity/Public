from sys import argv, exit
from random import randint, shuffle
from socket import gethostbyname_ex
from collections import defaultdict

def usage():
	print "Usage: %s <file>" % argv[0]
	exit(0)

if len(argv) < 2:
	usage()

mapped_domains = defaultdict(list)

try:
	for domain in open(argv[1]):
		domain = domain.strip()
		try:
			ip_addresses = gethostbyname_ex(domain)[2:] # skip domain + []
			ip_addresses = list(ip_addresses)[0]
			for ip_address in list(ip_addresses):
				mapped_domains[ip_address].append(domain)
		except:
			print "[-] Error while performing whois for: %s" % domain

except:
	print "[-] Error while parsing the domain file."
	exit(1)

fp = open("output.txt", "w")

while len(mapped_domains) > 1:
	ip_addresses = list(mapped_domains.keys())
	shuffle(ip_addresses)


	for ip_address in ip_addresses:

		if ip_address in mapped_domains:

			shuffle(mapped_domains[ip_address])

			choice = randint(0, len(mapped_domains[ip_address]) - 1)
			domain = mapped_domains[ip_address][choice]
			fp.write("%s,\n" % domain)


			del mapped_domains[ip_address][choice]


			if len(mapped_domains[ip_address]) < 1:
				del mapped_domains[ip_address]


			for k, v in mapped_domains.iteritems():
				if domain in v: 
					del v[v.index(domain)]
					if len(mapped_domains[k]) < 1:
						del mapped_domains[k]
					break
fp.close()
