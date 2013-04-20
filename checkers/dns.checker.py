#!/usr/bin/python

import sys
import requests
import random
import dns.resolver
import sha
import re

PORT = 3255

# Error codes
OK = 101
CORRUPT = 102
MUMBLE = 103
DOWN = 104
CHECKER_ERROR = 110


# Helpers
def gen_random_str(str_len, abc=list("abcdefgijklmnopqrstuvwxyz1234567890")):
	ret = []
	for i in range(str_len):
		ret.append(random.choice(abc))
	return "".join(ret)


def gen_secret_hash(s):
	return sha.new("TheMostSecret" + s + "MessageEver").hexdigest()[:20]


def gen_another_secret_hash(s):
	return sha.new("ThisIs" + s + "MysteryArg").hexdigest()[:20]


def register_or_die(host, login, password):
	ans = requests.post("http://{0}/register".format(host),
						data={"login": login, "first_name": login,
							  "last_name": "", "password": password,
							  "language": "ru"})
	if ans.status_code == 500:
		print("Failed to register the user in the user service: %s" % login)
		sys.exit(DOWN)


def get_session_num_or_die(host, login, password):
	ans = requests.post("http://{0}/login".format(host),
						data={"login": login, "password": password})

	if "session" not in ans.cookies:
		print("Failed to login to the user service")
		sys.exit(DOWN)

	return ans.cookies["session"]


def add_record(session, d_type, name, value):
	ans = requests.post("http://{0}:4567/".format(host),
						data = json.dumps({"action": "ADD", "type": d_type, "name": name, "value": value}),
						cookies = {"session": session})
	if ans.status_code != 200:
		print("Failed to add record - service returned not 200: %d" % ans.status_code)
		sys.exit(DOWN)

	answer_hash = ans.json()

	if answer_hash['code'] != "OK":
		print("Failed to add record: {0}".format(answer_hash['why']))
		sys.exit(MUMBLE)

	return answer_hash['id']

def del_record(session, d_id):
	ans = requests.post("http://{0}:4567/".format(host),
						data = json.dumps({"action": "DELETE", "id": d_id}),
						cookies={"session": session})
	if ans.status_code != 200:
		print("Failed to add record - service returned not 200: %d" % ans.status_code)
		sys.exit(DOWN)

	answer_hash = ans.json()

	if answer_hash['code'] != "OK":
		print("Failed to add record: {0}".format(answer_hash['why']))
		sys.exit(MUMBLE)

# not ready
def check(host):
	user = gen_random_str(10)
	password = gen_random_str(10)

	register_or_die(host, user, password)
	session = get_session_num_or_die(host, user, password)
	teamN = host.split('.')[2]
	sub_domain = gen_random_str(random.randint(10, 30))
	record_name = sub_domain + ".team" + teamN + ".ructf"
	ip_value = "{}.{}.{}.{}".format(random.randint(1, 254), random.randint(1, 254), random.randint(1, 254), random.randint(1, 254))
	record_id = add_record(session, "A", record_name, ip_value)

	ans = requests.get("http://{}:4567/show", cookies = {"session": session})
	html = ans.text
	if not re.match(sub_domain, html):
		print "Added record not shown"
		sys.exit(CORRUPT)

	del_record(session, record_id)
	ans = requests.get("http://{}:4567/show", cookies = {"session": session})
	html = ans.text
	if re.match(sub_domain, html):
		print "Deleted record is still shown!"
		sys.exit(CORRUPT)

	sys.exit(OK)


def put(host, flag_id, flag):
	user = flag_id.replace("-", "")
	password = gen_secret_hash(user)

	register_or_die(host, user, password)
	session = get_session_num_or_die(host, user, password)
	teamN = host.split('.')[2]
	add_record(session, "TXT", "{}.team{}.ructf".format(gen_another_secret_hash(flag_id), teamN), flag)
	sys.exit(OK)


def get(host, flag_id, flag):
	resolver = dns.resolver.Resolver()
	resolver.nameservers = [host]
	teamN = host.split('.')[2]
	flag2 = ''
	for rdata in resolver.query("{}.team{}.ructf".format(gen_another_secret_hash(flag_id), teamN), "TXT"):
		flag2 = rdata
		if flag2 != flag:
			sys.exit(CORRUPT)
	sys.exit(OK)


if __name__ == "__main__":
	try:
		args = sys.argv[1:]
		if len(args) == 2 and args[0] == "check":
			check(args[1])
		elif len(args) == 4 and args[0] == "put":
			put(args[1], args[2], args[3])
		elif len(args) == 4 and args[0] == "get":
			get(args[1], args[2], args[3])
		else:
			raise Exception("Wrong arguments")
	except Exception as E:
		sys.stderr.write("{}\n".format(E))
		sys.exit(CHECKER_ERROR)