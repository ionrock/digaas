import os
import textwrap
import time
import traceback
import uuid

import gevent
import gevent.subprocess

from digaas import storage
from digaas.consts import Status


# this module creates various files while generating a plot.
# we want to put these in a subdirectory.
def ensure_dir_exists(d):
    if not os.path.exists(d):
        os.mkdir(d)
# put the stats dir in the same dir as this module
STATS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'stats')
ensure_dir_exists(STATS_DIR)
print "USING STATS_DIR = %s" % STATS_DIR


class GnuplotException(Exception):
    def __init__(self, msg):
        super(GnuplotException, self).__init__(msg)


def receive(stats_req):
    stats_req.status = Status.ACCEPTED
    storage.create_stats_request(stats_req)
    thing = gevent.spawn(_handle_stats_request, stats_req)

def construct_filename(start, end):
    filename = "start{0}-end{1}-create{2}.png".format(
        int(start * 1000), int(end * 1000), int(time.time() * 1000))
    return os.path.join(STATS_DIR, filename)

def plot_data(data, filename):
    # in order to color data points easily, I split up the data files
    # according to three categories:
    #   1. updates - times for serial number updates
    #   2. removes - times for removals of zones/records
    #   3. errors - we enter one datapoint for each poll request that errored out
    # Datapoints contained in the same category/file will be colored the same
    updates_data_file = filename.rstrip('.png') + '.updates.dat'
    removes_data_file = filename.rstrip('.png') + '.removes.dat'
    errors_data_file = filename.rstrip('.png') + '.errors.dat'
    gnuplot_file = filename.rstrip('.png') + '.gnu'
    print("updates_file = {updates_file}\n"
          "removes_file = {removes_file}\n"
          "errors_file = {errors_file}"
          .format(updates_file=updates_data_file,
                  removes_file=removes_data_file,
                  errors_file=errors_data_file))

    # define our gnuplot file. This tells gnuplot which datafiles to use, what
    # file format to spit out, the output filename, and colors/style/formatting
    print "formatting gnuplot script"
    gnuplot_script = textwrap.dedent(
        """
        set term png size 1500,1000
        set output '{output_file}'
        set key outside below box
        set xtics rotate
        set format x "%0.1f"
        set xlabel "Timestamp of API request"
        set ylabel "Propagation time (seconds)"
        set title "API-to-nameserver propagation times"

        file_empty(file) = system("awk '{{x++}}END{{ print x}}' '".file."'") == 0

        # compute
        if (file_empty('{updates_file}')) {{
            print "WARN: file '{updates_file}' is empty."
            UPDATE_mean = -1
        }} else {{
            stats '{updates_file}' using 2 prefix "UPDATE"
        }}

        if (file_empty('{removes_file}')) {{
            print "WARN: file '{removes_file}' is empty."
            DELETE_mean = -1
        }} else {{
            stats '{removes_file}' using 2 prefix "DELETE"
        }}

        plot \\
            "{updates_file}" title "Creates/Updates" with points pointtype 5 linecolor rgb "blue", \\
            "{removes_file}" title "Deletes" with points pointtype 5 linecolor rgb "red", \\
            "{errors_file}" title "Errors" with points pointtype 5 linecolor rgb "black", \\
            UPDATE_mean title sprintf("Avg create/update time (%0.2f s)", UPDATE_mean) linecolor rgb "blue", \\
            DELETE_mean title sprintf("Avg delete time (%0.2f s)", DELETE_mean) linecolor rgb "red"
        """
    ).format(
        updates_file=updates_data_file,
        removes_file=removes_data_file,
        errors_file=errors_data_file,
        output_file=filename)

    with open(gnuplot_file, 'w') as f:
        f.write(gnuplot_script)

    # write out the datafiles
    with open(updates_data_file, 'w') as updates_file, \
         open(removes_data_file, 'w') as removes_file, \
         open(errors_data_file, 'w') as errors_file:

        n_updates, n_removes, n_errors = 0, 0, 0
        for item in data:
            operation, serial, duration = item.split()
            # print "op = %s, serial = %s, duration = %s" % (operation, serial, duration)
            if duration == "None" or duration is None:
                # python redis client saves None as "None"
                # since there is no duration use a default of zero
                errors_file.write("{0} 0\n".format(serial))
                n_errors += 1
                # print " --> error"
            elif operation == "update":
                updates_file.write("{0} {1}\n".format(serial, duration))
                n_updates += 1
                # print " --> update"
            elif operation == "remove":
                removes_file.write("{0} {1}\n".format(serial, duration))
                n_removes += 1
                # print " --> remove"
            else:
                print "ERROR: unknown data '%s'" % item

        print "n_updates = %s" % n_updates
        print "n_removes = %s" % n_removes
        print "n_errors = %s" % n_errors

        # gnuplot will fail if all data files are empty.
        # write a single datapoint to any of the files to avoid this
        if not n_updates and not n_removes and not n_errors:
            print("WARNING: no data found. avoiding gnuplot failure by writing"
                  "a safety point to {0}".format(errors_data_file))
            errors_file.write("0 0")

    # invoke gnuplot to generate the plot
    retcode = gevent.subprocess.call(['gnuplot', gnuplot_file])
    if retcode == 0:
        print "Output plot to %s" % filename
    else:
        raise GnuplotException("ERROR: gnuplot failed")


def _handle_stats_request(stats_req):
    filename = construct_filename(stats_req.start_time, stats_req.end_time)
    data = storage.select_time_range(stats_req.start_time, stats_req.end_time)
    try:
        plot_data(data, filename)
        stats_req.image_id = str(uuid.uuid4())
        # storage.create_image_filename(stats_req.image_id, filename)
        storage.create_image_bytes(stats_req.image_id, open(filename, 'rb').read())
        stats_req.status = Status.COMPLETED
    except GnuplotException as e:
        print traceback.format_exc()
        stats_req.status = Status.ERROR
    except Exception as e:
        print traceback.format_exc()
        stats_req.status = Status.INTERNAL_ERROR

    storage.update_stats_request(stats_req)
