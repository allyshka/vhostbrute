Virtual hosts bruteforcer (vhostbrute)
=====================
Virtual host multi-threading bruteforcer with BJ and other stuff.

Installation
=====================
Python 2.7 or 3 with Requests library >=2.7 needed.

`pip install -r requirements.txt`

Usage
=====================
```
    usage: vhostbrute.py [-h] [-u URL] [-s SCHEME] [-r REMOTEIP] [-b BASE]
                         [-n NOTFOUND] [-m METHOD] [-t THREADS] [-d VHOSTS]
                         [-z ZONES] [-v VERBOSE] [-e EASY] [-o OUTFILE]
    optional arguments:
      -h, --help            show this help message and exit
      -u URL, --url URL     URL to bruteforce
      -s SCHEME, --scheme SCHEME
                            Scheme to bruteforce
      -r REMOTEIP, --remoteip REMOTEIP
                            Remote IP for bruteforce
      -b BASE, --base BASE  Domain to base request
      -n NOTFOUND, --notfound NOTFOUND
                            Wrong vhost for not found request
      -m METHOD, --method METHOD
                            Method of bruteforce see readme
      -t THREADS, --threads THREADS
                            Count of threads (default: maxcpu)
      -d VHOSTS, --vhosts VHOSTS
                            Domain dictionary file
      -z ZONES, --zones ZONES
                            Zones dictionary file
      -v VERBOSE, --verbose VERBOSE
                            Show debug information
      -e EASY, --easy EASY  Easy method to find virtual hosts (default: true)
      -o OUTFILE, --outfile OUTFILE
                            File to save finded virtual host
```
If you have many false-positive detection try to turn off easy option *--easy 0*
First, you need to select method for brute (-m/--method [1-2]).

### Method 1 (default)
This method working like subdomain bruteforce. For example you have *example.com* site and you want brute some virtual hosts like: *test.example.com*, *dev.example.com*

Why vhosts? Because subdomains *test*, *dev* etc may not be resolve by *example.com* DNS servers. In this case **vhostbrute** can rock!

We need file with vhosts, IP of remote server (ex.: 10.1.1.15), we need host for **base** request to server. Base request is request to main site **www.example.com** for valid vhost determination.

**v.txt**:
```
test
dev
beta
alpha
etc
```

`vhostbrute.py --url="example.com" --remoteip="10.1.1.15" --base="www.example.com" --vhosts="v.txt"`
```
Starting bruteforce with 8 threads
Virutal host dev.example.com is found!
Virutal host test.example.com is found!
Brute successfully completed. Found 2 virtual host
```

### Method 2
This method working like **Cluster bomb** in Burp. You need to use two dictionary files. First with domain name, second with zone name. Example (use **verbose** option for detail output).

**d.txt**:
```
admin
services
mail
```
**z.txt**:
```
test
dev
```

`vhostbrute.py --url="example.com" --method 2 --vhosts="v.txt" --zone="z.txt" -v 1 --easy 0`
```
Starting bruteforce with 8 threads
Trying admin.test...
admin.test response: baselen - 19108 | nflen - 3773 | curr - 3956
Trying mail.test...
Trying mail.dev...
Trying services.test...
mail.test response: baselen - 19108 | nflen - 3773 | curr - 3953
mail.dev response: baselen - 19108 | nflen - 3773 | curr - 3950
services.test response: baselen - 19108 | nflen - 3773 | curr - 3965
Trying admin.dev...
Trying services.dev...
admin.dev response: baselen - 19108 | nflen - 3773 | curr - 3953
services.dev response: baselen - 19108 | nflen - 3773 | curr - 3962
admin.dev not found
admin.test not found
mail.dev not found
mail.test not found
services.test not found
services.dev not found
Brute successfully completed. Found 0 virtual host
```

TODO:

 - ~~Add write to outfile~~
 - ~~Add XFF checks~~
 - Add progress bar
 - Add many commentaries to source code
 - OOP rewrite(?)
 - Add template vhost generator like [a-zz].example.com will try a.example.com, b.example.com ... zy.example.com, zz.example.com
 - Test, test and test again


History
=====================
10.12.2015: First release. Basic functional.

Credits
=====================
Thanks TheRook for subbrute (https://github.com/TheRook/subbrute) names.txt file.