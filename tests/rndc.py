import subprocess
import re

def run_cmd(*cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise Exception("cmd `{0}` failed:\n\t{1}".format(" ".join(cmd), err))
    return (out.decode('utf-8'), err.decode('utf-8'), p.returncode)

def version():
    """Return a tuple like (9, 9, 5)"""
    # rndc doesn't have a version flag
    out, _, _ = run_cmd('rndc', 'status')
    version_line = out.split('\n')[0]
    assert version_line.startswith('version')
    parts = re.findall("\w+[.]\w+[.]\w+", version_line)[0].split('.')
    return tuple(map(int, parts))

def addzone(zone_name, zone_file):
    assert zone_name and zone_name[-1] == '.'
    return run_cmd('rndc', 'addzone', zone_name, '{ type master; file "%s"; };' % zone_file)

def reload(zone_name):
    assert zone_name and zone_name[-1] == '.'
    return run_cmd('rndc', 'reload', zone_name)

def delzone(zone_name):
    assert zone_name and zone_name[-1] == '.'
    # on Ubuntu 14.04 (rndc 9.9.5-3ubuntu0.2-Ubuntu), rndc delzone cannot have the trailing '.'
    # on Ubuntu 12.04 (rndc 9.8.1-P1), rndc delzone MUST have the trailing '.'
    #
    # I'm not sure the specific version where this changed, but this makes it work on these
    # two versions of Ubuntu
    if version() >= (9, 9, 0):
        return run_cmd('rndc', 'delzone', zone_name.strip('.'))
    else:
        return run_cmd('rndc', 'delzone', zone_name)
