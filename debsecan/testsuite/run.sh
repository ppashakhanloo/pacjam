#!/bin/bash

set -e

export LC_ALL=C

url="file://$(pwd)"
debsecan="python ../src/debsecan"

# Check that python-apt is installed.
python -c "import apt_pkg"

for testcase in [0-9][0-9][0-9] ; do
    for format in summary packages bugs detail report ; do
	for suite in sid ; do
	    if test -e $testcase/$suite ; then
		if test -e $testcase/options ; then
		    options="$(cat $testcase/options)"
		else
		    options=""
		fi
		if test -e $testcase/whitelist ; then
		    options="$options --whitelist $testcase/whitelist"
		else
		    options="$options --whitelist ''"
		fi

		if $debsecan $options \
		    --config /dev/null \
		    --suite $suite \
		    --source "$url/$testcase" \
		    --history $testcase/history \
		    --status $testcase/status \
		    --format $format > $testcase/out.$format 2>&1 ; then
		    if test $format = summary ; then
			sort $testcase/out.$format > $testcase/out.$format.1
			mv $testcase/out.$format.1 $testcase/out.$format
		    fi
		    diff -u $testcase/exp.$format $testcase/out.$format
		else
		    echo "FAIL: debsecan failed.  Output follows:"
		    cat $testcase/out.$format
		    exit 1
	        fi
	    fi
	done
    done
done

# Test the whitelist editing functionality.

rm -f whitelist.test
$debsecan --whitelist whitelist.test --add-whitelist CAN-2006-0001
cat > whitelist.exp <<EOF
VERSION 0
CAN-2006-0001,
EOF
diff -u whitelist.test whitelist.exp

$debsecan --whitelist whitelist.test --add-whitelist CAN-2006-0001 CAN-2006-0002
cat > whitelist.exp <<EOF
VERSION 0
CAN-2006-0001,
CAN-2006-0002,
EOF
diff -u whitelist.test whitelist.exp

$debsecan --whitelist whitelist.test --add-whitelist CAN-2006-0001 pkg1 CAN-2006-0003 pkg2 pkg3
cat > whitelist.exp <<EOF
VERSION 0
CAN-2006-0001,
CAN-2006-0002,
CAN-2006-0001,pkg1
CAN-2006-0003,pkg2
CAN-2006-0003,pkg3
EOF
diff -u whitelist.test whitelist.exp

$debsecan --whitelist whitelist.test --remove-whitelist CAN-2006-0003 pkg2
cat > whitelist.exp <<EOF
VERSION 0
CAN-2006-0001,
CAN-2006-0002,
CAN-2006-0001,pkg1
CAN-2006-0003,pkg3
EOF
diff -u whitelist.test whitelist.exp

$debsecan --whitelist whitelist.test --show-whitelist > whitelist.out
cat > whitelist.exp <<EOF
CAN-2006-0001 (all packages)
CAN-2006-0002 (all packages)
CAN-2006-0001 pkg1
CAN-2006-0003 pkg3
EOF
diff -u whitelist.out whitelist.exp

if $debsecan --whitelist whitelist.test \
    --remove-whitelist CAN-2006-0003 pkg4 2>whitelist.out ; then
    echo "FAILURE: --remove-whitelist on unknown package"
    exit 1
else
    cat > whitelist.exp <<EOF
error: no matching whitelist entry for CAN-2006-0003 pkg4
EOF
    diff -u whitelist.out whitelist.exp
fi

if $debsecan --whitelist whitelist.test \
    --remove-whitelist CAN-2006-9999 2>whitelist.out ; then
    echo "FAILURE: --remove-whitelist on unknown bug"
    exit 1
else
    cat > whitelist.exp <<EOF
error: no matching whitelist entry for CAN-2006-9999
EOF
    diff -u whitelist.out whitelist.exp
fi

$debsecan --whitelist whitelist.test --remove-whitelist CAN-2006-0003 CAN-2006-0001
cat > whitelist.exp <<EOF
VERSION 0
CAN-2006-0002,
EOF
diff -u whitelist.test whitelist.exp
