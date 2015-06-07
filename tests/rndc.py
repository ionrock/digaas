import subprocess

def run_cmd(*cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    if p.returncode != 0:
        raise Exception("cmd `{0}` failed:\n\t{1}".format(" ".join(cmd), err))
    return (out.decode('utf-8'), err.decode('utf-8'), p.returncode)

def addzone(zone_name, zone_file):
    assert zone_name and zone_name[-1] == '.'
    return run_cmd('rndc', 'addzone', zone_name, '{ type master; file "%s"; };' % zone_file)

def reload(zone_name):
    assert zone_name and zone_name[-1] == '.'
    return run_cmd('rndc', 'reload', zone_name)

def delzone(zone_name):
    assert zone_name and zone_name[-1] == '.'
    # in my version of rndc (9.9.5-3ubuntu0.2-Ubuntu), rndc only works without the trailing '.'
    # otherwise it fails silently.
    return run_cmd('rndc', 'delzone', zone_name.strip('.'))
