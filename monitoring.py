import common
import settings
import subprocess

def start(directory, cluster):
    nodes = settings.getnodes('clients', 'osds', 'mons', 'rgws')
    collectl_dir = '%s/collectl' % directory
    perf_dir = '%s/perf' % directory
    blktrace_dir = '%s/blktrace' % directory

    print "====== start monitoring ======"
    # collectl
    common.pdsh(nodes, 'mkdir -p -m0755 -- %s' % collectl_dir)
    common.pdsh(nodes, 'collectl -s+mYZ -D -i 1:10 -F0 -f %s' % collectl_dir, True)
    print "collectl started on %s" % str(nodes)

    # perf
    common.pdsh(nodes, 'mkdir -p -m0755 -- %s' % perf_dir)
    common.pdsh(nodes, 'cd %s;sudo perf record -g -a -F 100 -o perf.data > /dev/null &' % perf_dir, True)
    print "perf started on %s" % str(nodes)

    # blktrace
    sc = settings.cluster
    osds = sc.get('osds')
    nodes = settings.getnodes('osds')
    user = sc.get('user')
    common.pdsh(nodes, 'mkdir -p -m0755 -- %s' % blktrace_dir)
    for osd in osds:
        device_id = 0
        for device in cluster.get_osd_device_by_host(osd):
            common.pdsh("%s@%s" % (user, osd), 'cd %s;sudo blktrace -o device%d -d %s > /dev/null &' % (blktrace_dir, device_id, device), True)
            device_id += 1
    print "blktrace started on %s" % str(nodes)



def stop(directory=None):
    nodes = settings.getnodes('clients', 'osds', 'mons', 'rgws')
    print "====== stop monitoring ======"

    #common.pdsh(nodes, 'pkill -SIGINT -f collectl', True)
    #common.pdsh(nodes, 'sudo pkill -SIGINT -f perf', True)
    #common.pdsh(settings.getnodes('osds'), 'sudo pkill -SIGINT -f blktrace', True)
    common.pdsh(nodes, 'sudo killall -9 collectl', True)
    common.pdsh(nodes, 'sudo killall -9 perf', True)
    common.pdsh(settings.getnodes('osds'), 'sudo killall -9 blktrace', True)
    if directory:
        sc = settings.cluster
        common.pdsh(nodes, 'cd %s/perf;sudo chown %s.%s perf.data' % (directory, sc.get('user'), sc.get('user')))
        make_movies(directory)

def make_movies(directory):
    sc = settings.cluster
    seekwatcher = '/usr/bin/seekwatcher'
    blktrace_dir = '%s/blktrace' % directory
    nodes = settings.getnodes('osds')

    print "start seekwatcher on %s:%s" % (str(nodes), blktrace_dir)
    for device in xrange (0,sc.get('osds_per_node')):
        common.pdsh(nodes, 'cd %s;%s -t device%s -o device%s.mpg --movie > device%s.seekwatcher.log &' % (blktrace_dir, seekwatcher, device, device, device), True)

