#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2017 GEM Foundation and G. Weatherill
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
from openquake.hazardlib.scalerel.peer import PeerMSR

"""
Strong motion utilities
"""
import os
import sys
import numpy as np
from scipy.integrate import cumtrapz
from scipy.constants import g
from collections import OrderedDict
from openquake.hazardlib.geo import (PlanarSurface, SimpleFaultSurface,
                                     ComplexFaultSurface, MultiSurface,
                                     Point, Line)
import matplotlib.pyplot as plt

if sys.version_info[0] >= 3:
    import pickle
else:
    import cPickle as pickle  # pylint: disable=import-error


def get_time_vector(time_step, number_steps):
    """
    General SMTK utils
    """
    return np.cumsum(time_step * np.ones(number_steps, dtype=float)) -\
        time_step


def nextpow2(nval):
    m_f = np.log2(nval)
    m_i = np.ceil(m_f)
    return int(2.0 ** m_i)


def convert_accel_units(acceleration, from_, to_='cm/s/s'):  # pylint: disable=too-many-return-statements
    """
    Converts acceleration from/to different units

    :param acceleration: the acceleration (numeric or numpy array)
    :param from_: unit of `acceleration`: string in "g", "m/s/s", "m/s**2",
        "m/s^2", "cm/s/s", "cm/s**2" or "cm/s^2"
    :param to_: new unit of `acceleration`: string in "g", "m/s/s", "m/s**2",
        "m/s^2", "cm/s/s", "cm/s**2" or "cm/s^2". When missing, it defaults
        to "cm/s/s"

    :return: acceleration converted to the given units (by default, 'cm/s/s')
    """
    m_sec_square = ("m/s/s", "m/s**2", "m/s^2")
    cm_sec_square = ("cm/s/s", "cm/s**2", "cm/s^2")
    acceleration = np.asarray(acceleration)
    if from_ == 'g':
        if to_ == 'g':
            return acceleration
        if to_ in m_sec_square:
            return acceleration * g
        if to_ in cm_sec_square:
            return acceleration * (100 * g)
    elif from_ in m_sec_square:
        if to_ == 'g':
            return acceleration / g
        if to_ in m_sec_square:
            return acceleration
        if to_ in cm_sec_square:
            return acceleration * 100
    elif from_ in cm_sec_square:
        if to_ == 'g':
            return acceleration / (100 * g)
        if to_ in m_sec_square:
            return acceleration / 100
        if to_ in cm_sec_square:
            return acceleration

    raise ValueError("Unrecognised time history units. "
                     "Should take either ''g'', ''m/s/s'' or ''cm/s/s''")


def get_velocity_displacement(time_step, acceleration, units="cm/s/s",
                              velocity=None, displacement=None):
    '''
    Returns the velocity and displacment time series using simple integration
    :param float time_step:
        Time-series time-step (s)
    :param numpy.ndarray acceleration:
        Acceleration time-history
    :returns:
        velocity - Velocity Time series (cm/s)
        displacement - Displacement Time series (cm)
    '''
    acceleration = convert_accel_units(acceleration, units)
    if velocity is None:
        velocity = time_step * cumtrapz(acceleration, initial=0.)
    if displacement is None:
        displacement = time_step * cumtrapz(velocity, initial=0.)
    return velocity, displacement


def build_filename(filename, filetype='png', resolution=300):
    """
    Uses the input properties to create the string of the filename
    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    filevals = os.path.splitext(filename)
    if filevals[1]:
        filetype = filevals[1][1:]
    if not filetype:
        filetype = 'png'

    filename = filevals[0] + '.' + filetype

    if not resolution:
        resolution = 300
    return filename, filetype, resolution


def _save_image(filename, filetype='png', resolution=300):
    """
    If filename is specified, saves the image
    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    if filename:
        filename, filetype, resolution = build_filename(filename,
                                                        filetype,
                                                        resolution)
        plt.savefig(filename, dpi=resolution, format=filetype)
    else:
        pass
    return


def _save_image_tight(fig, lgd, filename, filetype='png', resolution=300):
    """
    If filename is specified, saves the image
    :param str filename:
        Name of the file
    :param str filetype:
        Type of file
    :param int resolution:
        DPI resolution of the output figure
    """
    if filename:
        filename, filetype, resolution = build_filename(filename,
                                                        filetype,
                                                        resolution)
        fig.savefig(filename, bbox_extra_artists=(lgd,),
                    bbox_inches="tight", dpi=resolution, format=filetype)
    else:
        pass
    return


def load_pickle(pickle_file):
    """
    Python 2 & 3 compatible way of loading a Python Pickle file
    """
    try:
        with open(pickle_file, 'rb') as f:
            pickle_data = pickle.load(f)
    except UnicodeDecodeError as e:
        with open(pickle_file, 'rb') as f:
            pickle_data = pickle.load(f, encoding='latin1')
    except Exception as e:
        print('Unable to load data ', pickle_file, ':', e)
        raise
    return pickle_data


# Set of modules for converting OpenQuake surface classes to dictionaries
def planar_fault_surface_to_dict(surface):
    """
    Parses a PlanarSurface object to a dictionary formatted for json export
    """
    output = OrderedDict([("type", "PlanarSurface")])
    # Top left
    for i, key in zip([0, 1, 3, 2],
        ["top_left", "top_right", "bottom_right", "bottom_left"]):
        output[key] = [surface.corner_lons[i],
                       surface.corner_lats[i],
                       surface.corner_depths[i]]
    return output


def simple_fault_surface_to_dict(surface):
    """
    Parsers a SimpleFaultSurface object ot a dictionary formatted for
    json export

    More complicated here as we need to use the surface nodes
    """
    output = OrderedDict([("type", "SimpleFaultSurface")])
    for node in surface.surface_nodes[0]:
        if "LineString" in node.tag:
            trace = node[0].text
            output["trace"] = [[trace[i], trace[i + 1]]
                                for i in range(0, len(trace), 2)]
        else:
            output[node.tag] = node.text
    return output


def complex_fault_surface_to_dict(surface):
    """
    Parses a ComplexFaultSurface object ot a dictionary formatted for json
    export
    """
    output = OrderedDict([("type", "ComplexFaultSurface")])
    intermediate_edges = []
    for node in surface.surface_nodes[0]:
        edge = node[0].nodes[0].text
        edge = [[edge[i], edge[i + 1], edge[i + 2]]
                for i in range(0, len(edge), 3)]
        if "intermediateEdge" in node.tag:
            intermediate_edges.append(edge)
        else:
            output[node.tag] = edge
    output["intermediateEdges"] = intermediate_edges
    return output


surfaces_to_dict = {
    "PlanarSurface": planar_fault_surface_to_dict,
    "SimpleFaultSurface": simple_fault_surface_to_dict,
    "ComplexFaultSurface": complex_fault_surface_to_dict,
    }


def multi_surface_to_dict(surface):
    """
    Parses a multi
    """
    output = OrderedDict([("type", "MultiSurface"), ("surfaces", [])])
    for sfc in surface.surfaces:
        output["surfaces"].append(
            surfaces_to_dict[sfc.__class__.__name__](sfc))
    return output


surfaces_to_dict["MultiSurface"] = multi_surface_to_dict


# Surfaces from json dict
def planar_fault_surface_from_dict(data, mesh_spacing=1.):
    """
    Builds a planar fault surface from the json load
    """
    assert "PlanarSurface" in data
    top_left = Point(data["top_left"][0],
                     data["top_left"][1],
                     data["top_left"][2])
    top_right = Point(data["top_right"][0],
                      data["top_right"][1],
                      data["top_right"][2])
    bottom_left = Point(data["bottom_left"][0],
                        data["bottom_left"][1],
                        data["bottom_left"][2])
    bottom_right = Point(data["bottom_right"][0],
                         data["bottom_right"][1],
                         data["bottom_right"][2])
    return PlanarSurface.from_corner_points(mesh_spacing, top_left, top_right,
                                            bottom_right, bottom_left)


def simple_fault_surface_from_dict(data, mesh_spacing=1.):
    """
    Builds a simple fault surface from the json load
    """
    assert "SimpleFaultSurface" in data
    trace = []
    for lon, lat in data["trace"]:
        trace.append(Point(lon, lat, 0.0))
    trace = Line(trace)
    return SimpleFaultSurface.from_fault_data(trace, data["upperSeismoDepth"],
                                              data["lowerSeismoDepth"],
                                              data["dip"], mesh_spacing)

def _3d_line_from_list(vals):
    """
    """
    vertices = []
    for lon, lat, depth in vals:
        vertices.append(Point(lon, lat, depth))
    return Line(vertices)

def complex_fault_surface_from_dict(data, mesh_spacing=1.):
    """
    Builds a complex fault surface from the json load
    """
    assert "ComplexFaultSurface" in data
    edges = [_3d_line_from_list(data["faultTopEdge"])]
    if len(data["intermediateEdges"]):
        for iedge in data["intermediateEdges"]:
            edges.append(_3d_line_from_list(iedge))
    edges.append(_3d_line_from_list(data["faultBottomEdge"]))
    return ComplexFaultSurface.from_fault_data(edges, mesh_spacing)


surfaces_from_dict = {
    "PlanarSurface": planar_fault_surface_from_dict,
    "SimpleFaultSurface": simple_fault_surface_from_dict,
    "ComplexFaultSurface": complex_fault_surface_from_dict}


def multi_surface_from_dict(data, mesh_spacing=1.):
    """
    Builds a multi-fault surface from the json load
    """
    assert "MultiSurface" in data
    surfaces = []
    for surface in data["surfaces"]:
        surfaces.append(surfaces_from_dict[surface["type"]](surface,
                                                            mesh_spacing))
    return MultiSurface(surfaces)


surfaces_from_dict["MultiSurface"] = multi_surface_from_dict


# Moved from sm_database: Mechanism type to Rake conversion:
MECHANISM_TYPE = {"Normal": -90.0,
                  "Strike-Slip": 0.0,
                  "Reverse": 90.0,
                  "Oblique": 0.0,
                  "Unknown": 0.0,
                  "N": -90.0,  # Flatfile conventions
                  "S": 0.0,
                  "R": 90.0,
                  "U": 0.0,
                  "NF": -90.,  # ESM flatfile conventions
                  "SS": 0.,
                  "TF": 90.,
                  "NS": -45.,  # Normal with strike-slip component
                  "TS": 45.,  # Reverse with strike-slip component
                  "O": 0.0
                  }


DIP_TYPE = {"Normal": 60.0,
            "Strike-Slip": 90.0,
            "Reverse": 35.0,
            "Oblique": 60.0,
            "Unknown": 90.0,
            "N": 60.0, # Flatfile conventions
            "S": 90.0,
            "R": 35.0,
            "U": 90.0,
            "NF": 60., # ESM flatfile conventions
            "SS": 90.,
            "TF": 35.,
            "NS": 70., # Normal with strike-slip component
            "TS": 45., # Reverse with strike-slip component
            "O": 90.0
            }




# mean utilities (geometric, arithmetic, ...):
SCALAR_XY = {"Geometric": lambda x, y: np.sqrt(x * y),
             "Arithmetic": lambda x, y: (x + y) / 2.,
             "Larger": lambda x, y: np.max(np.array([x, y]), axis=0),
             "Vectorial": lambda x, y: np.sqrt(x ** 2. + y ** 2.)}


DEFAULT_MSR = PeerMSR()


def get_interpolated_period(target_period, periods, values):
    """
    Returns the spectra interpolated in loglog space
    :param float target_period:
        Period required for interpolation
    :param np.ndarray periods:
        Spectral Periods
    :param np.ndarray values:
        Ground motion values
    """
    if (target_period < np.min(periods)) or (target_period > np.max(periods)):
        return None, "Period not within calculated range %s"
    lval = np.where(periods <= target_period)[0][-1]
    uval = np.where(periods >= target_period)[0][0]

    if (uval - lval) == 0:
        return values[lval]

    d_y = np.log10(values[uval]) - np.log10(values[lval])
    d_x = np.log10(periods[uval]) - np.log10(periods[lval])
    return 10.0 ** (
        np.log10(values[lval]) +
        (np.log10(target_period) - np.log10(periods[lval])) * d_y / d_x
        )

# surfaces_to_dict = {
#    "PlanarSurface": planar_fault_surface_to_dict,
#    "SimpleFaultSurface": simple_fault_surface_to_dict,
#    "ComplexFaultSurface": complex_fault_surface_to_dict,
#    "MultiSurface": multi_surface_to_dict
#    }

