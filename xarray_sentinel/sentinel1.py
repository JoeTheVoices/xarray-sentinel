import os.path
import typing as T
from xml.etree import ElementTree

import numpy as np
import xarray as xr

from xarray_sentinel import esa_safe


def open_gcp_dataset(filename: str) -> xr.Dataset:
    annotation = ElementTree.parse(filename)
    geolocation_grid_points = esa_safe.parse_geolocation_grid_points(annotation)
    azimuth_time = []
    slant_range_time = []
    line_set = set()
    pixel_set = set()
    for ggp in geolocation_grid_points.values():
        if ggp["line"] not in line_set:
            azimuth_time.append(np.datetime64(ggp["azimuthTime"]))
            line_set.add(ggp["line"])
        if ggp["pixel"] not in pixel_set:
            slant_range_time.append(ggp["slantRangeTime"])
            pixel_set.add(ggp["pixel"])
    shape = (len(azimuth_time), len(slant_range_time))
    data_vars = {
        "latitude": (
            ("azimuth_time", "slant_range_time"),
            np.full(shape, np.nan),
            {"units": "degrees_north"},
        ),
        "longitude": (
            ("azimuth_time", "slant_range_time"),
            np.full(shape, np.nan),
            {"units": "degrees_east"},
        ),
        "height": (
            ("azimuth_time", "slant_range_time"),
            np.full(shape, np.nan),
            {"units": "m"},
        ),
        "incidenceAngle": (
            ("azimuth_time", "slant_range_time"),
            np.full(shape, np.nan),
            {"units": "degrees"},
        ),
        "elevationAngle": (
            ("azimuth_time", "slant_range_time"),
            np.full(shape, np.nan),
            {"units": "degrees"},
        ),
    }
    line = sorted(line_set)
    pixel = sorted(pixel_set)
    for ggp in geolocation_grid_points.values():
        for var in data_vars:
            j = line.index(ggp["line"])
            i = pixel.index(ggp["pixel"])
            data_vars[var][1][j, i] = ggp[var]

    ds = xr.Dataset(
        data_vars=data_vars,  # type: ignore
        coords={
            "azimuth_time": (
                "azimuth_time",
                [np.datetime64(dt) for dt in sorted(azimuth_time)],
                {"standard_name": "time", "long_name": "azimuth time"},
            ),
            "slant_range_time": (
                "slant_range_time",
                sorted(slant_range_time),
                {"units": "s", "long_name": "slant range time / two-way delay"},
            ),
        },
        attrs={"Conventions": "CF-1.7"},
    )
    return ds


def open_root_dataset(filename: str) -> xr.Dataset:
    manifest = esa_safe.open_manifest(filename)
    product_attrs, product_files = esa_safe.parse_manifest_sentinel1(manifest)
    product_attrs["groups"] = ["orbit"] + product_attrs["xs:instrument_mode_swaths"]
    return xr.Dataset(attrs=product_attrs)  # type: ignore


class Sentinel1Backend(xr.backends.common.BackendEntrypoint):
    def open_dataset(  # type: ignore
        self,
        filename_or_obj: str,
        drop_variables: T.Optional[T.Tuple[str]] = None,
        group: T.Optional[str] = None,
    ) -> xr.Dataset:
        if group is None:
            ds = open_root_dataset(filename_or_obj)
        elif group == "gcp":
            ds = open_gcp_dataset(filename_or_obj)
        return ds

    def guess_can_open(self, filename_or_obj: T.Any) -> bool:
        try:
            _, ext = os.path.splitext(filename_or_obj)
        except TypeError:
            return False
        return ext.lower() in {".safe"}
