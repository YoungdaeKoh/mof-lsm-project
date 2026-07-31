"""Greenland outline, so the ice-sheet cut follows the coast instead of a box.

A lat/lon box (lat>59, 73W-11W) was used first and it reached across Baffin Bay:
87 of the 170 points it removed were Canadian Arctic land (Baffin, Ellesmere,
Devon), 0.25 %% of the averaged land area.  These vertices are Natural Earth 50m
Greenland, dilated by 0.6 deg so that a C96 cell centre sitting just off the
coast still counts, then simplified to 0.25 deg.  Iceland needs no special case
any more -- it is simply outside the polygon.

Pure numpy ray casting so the server needs no cartopy or shapely.
"""
import numpy as np

GREENLAND = np.array([
    [ -73.4049, 78.0696], [ -72.5183, 79.0917], [ -67.5344, 79.7138], [ -67.7757, 80.4238],
    [ -67.2221, 80.9687], [ -61.8331, 81.7428], [ -60.9364, 82.4480], [ -54.7234, 82.9514],
    [ -51.5558, 82.6574], [ -50.8684, 83.0721], [ -47.8900, 82.8628], [ -46.2699, 83.6553],
    [ -43.0399, 83.8638], [ -32.9828, 84.1996], [ -26.9864, 83.9750], [ -21.4992, 83.2508],
    [ -20.5360, 82.0209], [ -19.2709, 82.7216], [ -17.4636, 82.0027], [ -15.5748, 82.4333],
    [ -12.1107, 82.2435], [ -11.1545, 82.0159], [ -10.8280, 81.5351], [ -11.3386, 80.8550],
    [ -18.3789, 79.1160], [ -18.3189, 78.3192], [ -17.5522, 78.4445], [ -17.0861, 78.0099],
    [ -18.0416, 76.3762], [ -16.8108, 74.8880], [ -17.2589, 74.4519], [ -18.6305, 74.4025],
    [ -20.2634, 72.9457], [ -21.4300, 72.8412], [ -20.9254, 70.5835], [ -21.1803, 70.0335],
    [ -26.2321, 68.1122], [ -31.7161, 67.5928], [ -33.9015, 66.1336], [ -36.8574, 64.9577],
    [ -39.0779, 65.0102], [ -39.6050, 64.6420], [ -40.1184, 63.3089], [ -41.5853, 62.2326],
    [ -41.5676, 61.6011], [ -42.6669, 59.6712], [ -43.8867, 59.2158], [ -46.2896, 60.0674],
    [ -48.4423, 60.2292], [ -51.9122, 63.2380], [ -52.7234, 64.6729], [ -54.1733, 65.9355],
    [ -54.4821, 67.1882], [ -53.8547, 68.6674], [ -55.4046, 69.3610], [ -55.1198, 70.8115],
    [ -56.1638, 71.2891], [ -56.2410, 72.0776], [ -56.7930, 72.5589], [ -56.7077, 73.5512],
    [ -57.6052, 73.6567], [ -57.7559, 74.4147], [ -59.1635, 75.1700], [ -61.4171, 75.5808],
    [ -66.8706, 75.3704], [ -69.5546, 75.7600], [ -70.1184, 76.2636], [ -72.8481, 76.9005],
    [ -73.4049, 78.0696],
])


def in_greenland(lat, lon):
    """Ray casting; lon in -180..180.  Returns a boolean array."""
    lon = np.where(np.asarray(lon) > 180, np.asarray(lon) - 360.0, np.asarray(lon))
    lat = np.asarray(lat)
    x, y = GREENLAND[:, 0], GREENLAND[:, 1]
    inside = np.zeros(lat.shape, bool)
    for k in range(len(x) - 1):
        x1, y1, x2, y2 = x[k], y[k], x[k + 1], y[k + 1]
        if y1 == y2:
            continue
        crosses = (y1 > lat) != (y2 > lat)
        with np.errstate(invalid="ignore", divide="ignore"):
            xint = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
        inside ^= crosses & (lon < xint)
    return inside
