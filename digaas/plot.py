"""
This module gives us an interface for working with Gnuplot. It's broken up
different classes:

    GnuplotConfig - this defines the plot title, axis labels, etc. You need
        one of these per plot
    GnuplotData - a list of points to be plotted. You may have multiple of
        these on the same plot
    GnuplotStyle - the style for a set of points. You should have one of these
        per GnuplotData
    GnuplotScript - the class that invokes gnuplot. This accepts a
        GnuplotConfig and a list of GnuplotDatas with GnuplotStyles
"""
import logging
import os
import subprocess
import time
import uuid

from digaas.config import cfg

LOG = logging.getLogger(__name__)


def generate_filename(tag, extension):
    """Generate a unique but tagged filename for the datafile"""
    safe_tag = "".join([c for c in tag if c.isalnum()])
    extension = extension.strip('.')
    return "{0}-{1}.{2}".format(safe_tag, uuid.uuid4().hex, extension)


def get_path(filename):
    """We want all our plot files in the configured tmp dir"""
    return os.path.join(cfg.CONF.digaas.tmp_dir, filename)


class GnuplotData(object):

    def __init__(self, label, points):
        self.label = label
        self.points = points
        self.filename = generate_filename(tag=self.label, extension='dat')

    def write_datafile(self):
        path = get_path(self.filename)
        LOG.debug("Writing datafile %s (%s points to be written)",
                  path, len(self.points))
        start = time.time()
        with open(path, 'w') as f:
            for x, y in self.points:
                f.write("{0} {1}\n".format(x, y))
        LOG.debug("Writing datafile %s took %s seconds", path,
                  time.time() - start)


class GnuplotConfig(object):
    """The plot config. You will only need one of these per plot"""

    def __init__(self, xlabel, ylabel, title, width=1920, height=1080,
                 rotate_xtics=True, pointtype=5, linecolor=None):
        """
        :param rotate_xtics: if True, the labels for the ticks on the x-axis
            will be vertical, which is nicer for wide labels.
        """
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.title = title
        self.width = width
        self.height = height
        self.rotate_xtics = rotate_xtics


class GnuplotStyle(object):
    """You will need one style per dataset/datafile rendered"""

    def __init__(self, pointtype=5, rgb_linecolor=None):
        """
        :param pointtype: the shape of the point. gnuplot uses numbers to
            encode these (google images "gnuplot pointtype")
        :param rbg_linecolor: this can be a word ("red") or hex ("#FF0000")
        """
        self.pointtype = pointtype
        self.rgb_linecolor = rgb_linecolor


class GnuplotScript(object):

    def __init__(self, config, plots, output_format='png'):
        """
        :param config: a GnuplotConfig object
        :param plots: A list of (data, style) tuples where the data is a
            GnuplotData and the config is a GnuplotStyle
        """
        self.config = config
        self.plots = plots
        self.output_format = output_format
        self.filename = generate_filename(tag="script", extension="gnuplot")
        self.output_filename = self.filename.replace(
            "gnuplot", self.output_format
        )

    def get_output_plot_path(self):
        return get_path(self.output_filename)

    def generate_plot(self):
        """Generate the plot self.output_filename in self.directory"""
        self._write_datafiles()
        self._write_gnuplot_script()
        self._run_gnuplot()

    def _run_gnuplot(self):
        try:
            cmd = ['gnuplot', get_path(self.filename)]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            out, err = p.communicate()
            if p.returncode == 0:
                LOG.info("Generated plot %s", self.output_filename)
            else:
                raise Exception(
                    "Command '{0}' failed\nstdout: {1}\nstderr: {2}"
                    .format(" ".join(cmd), out, err)
                )
        except Exception as e:
            LOG.exception(e)

    def _write_datafiles(self):
        for gnuplot_data, _ in self.plots:
            gnuplot_data.write_datafile()

    def _write_gnuplot_script(self):
        path = get_path(self.filename)
        content = self.get_script_content()
        LOG.debug("Writing %s (%s bytes)", path, len(content))
        with open(path, 'w') as f:
            f.write(content)

    def get_script_content(self):
        # we need this to look like, where the last does not have a comma
        #   plot <line>, \
        #        <line>, \
        #        <line>
        plot_string = ", \\\n     ".join([
            self._get_plot_string(data, style) for data, style in self.plots
        ])
        return "{0}\n\nplot {1}".format(self._get_header_string(), plot_string)

    def _get_plot_string(self, data, style):
        fmt = '"{file}" title "{title}" with points pointtype {pointtype}'
        if style.rgb_linecolor:
            fmt += ' linecolor rgb "{linecolor}"'
        return fmt.format(
            file=get_path(data.filename),
            title=data.label,
            pointtype=style.pointtype,
            linecolor=style.rgb_linecolor,
        )

    def _get_header_string(self):
        lines = [
            "set term {output_format} size {width},{height}",
            "set output '{output_path}'",
            "set key outside below box",
            'set format x "%0.1f"',
            'set xlabel "{xlabel}"',
            'set ylabel "{ylabel}"',
            'set title "{title}"',
        ]
        if self.config.rotate_xtics:
            lines.append("set xtics rotate")

        return "\n".join(lines).format(
            output_format=self.output_format,
            output_path=get_path(self.output_filename),
            **self.config.__dict__)
