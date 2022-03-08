import pathlib

import click
import numpy as np
import pandas as pd

'''
path = pathlib.Path("E:\Current Cases\City of LondonThermal Comfort\Results\localSpeedFactor.csv")
direction = 353.2
reference_speed = 5.0
'''


def round_direction(path, direction):
    path = pathlib.Path(path)

    columns = pd.read_csv(path, index_col=0, nrows=0).columns.astype(float).to_numpy()
    columns.sort()
    columns = np.append(columns, columns[0] + 360)

    interval = []
    for i in range(0, len(columns) - 1):
        interval.append((columns[i] + columns[i + 1]) / 2)

    direction_bin = None
    for i in range(0, len(interval)):
        if i == 0:
            if direction < interval[i] or direction > interval[-1]:
                direction_bin = i
                break
        else:
            if direction >= interval[i - 1] and direction < interval[i]:
                direction_bin = i
                break

    rounded_direction = columns[direction_bin]

    return rounded_direction


def round_direction_feather(path, direction):
    path = pathlib.Path(path)

    columns = pd.read_feather(path).columns.astype(float).to_numpy()
    columns.sort()
    columns = np.append(columns, columns[0] + 360)

    interval = []
    for i in range(0, len(columns) - 1):
        interval.append((columns[i] + columns[i + 1]) / 2)

    direction_bin = None
    for i in range(0, len(interval)):
        if i == 0:
            if direction < interval[i] or direction > interval[-1]:
                direction_bin = i
                break
        else:
            if direction >= interval[i - 1] and direction < interval[i]:
                direction_bin = i
                break

    rounded_direction = columns[direction_bin]

    return rounded_direction


def reduce_resolution(points, resolution):
    '''
    Take a fine point cloud, return a coarser one.

    Parameters
    ----------
    points : dataframe
        A dataframe of point locations with 3 columns, X, Y and Z, the 
        number of rows is the number of points.
    resolution : int or float
        int or float, optional
        an integer or float that represents the desired resolution in 
        meters, for example, if we wanted an output sensor grid no 
        finner than 5m then we can input 5.

    Returns
    -------
    grid_candidate_center_id : list
        The ID's of the points in the original points list to KEEP, 
        i.e. if we reduce the resolution from 0.5m to 5m, which points 
        closest represent an evenly spaced grid with spaces of 5m, the 
        resulting grid will not be structured.

    '''
    points = points.to_numpy()

    voxel_size = resolution

    non_empty_voxel_keys, inverse, nb_pts_per_voxel = np.unique(
        ((points - np.min(points, axis=0)) // voxel_size).astype(int),
        axis=0,
        return_inverse=True,
        return_counts=True)

    idx_pts_vox_sorted = np.argsort(inverse)

    voxel_grid = {}
    ids_grid = {}

    grid_barycenter = []
    grid_candidate_center = []
    grid_candidate_center_id = []
    last_seen = 0

    for idx, vox in enumerate(non_empty_voxel_keys):
        voxel_grid[tuple(vox)] = points[
            idx_pts_vox_sorted[last_seen:last_seen + nb_pts_per_voxel[idx]]]

        ids_grid[tuple(vox)] = idx_pts_vox_sorted[
                               last_seen:last_seen + nb_pts_per_voxel[idx]]

        # The geometric centre of a grid space
        grid_barycenter.append(np.mean(voxel_grid[tuple(vox)], axis=0))

        # The point closest to the centre of a grid space
        grid_candidate_center.append(
            voxel_grid[tuple(vox)][np.linalg.norm(voxel_grid[tuple(vox)]
                                                  - np.mean(voxel_grid[tuple(vox)], axis=0), axis=1).argmin()])

        # The ID of the same point
        grid_candidate_center_id.append(
            ids_grid[tuple(vox)][np.linalg.norm(voxel_grid[tuple(vox)]
                                                - np.mean(voxel_grid[tuple(vox)], axis=0), axis=1).argmin()])

        last_seen += nb_pts_per_voxel[idx]

    return grid_candidate_center_id


def reduce_field(data, idx):
    '''
    Take dataframe and ID's, return a datafram with only data at ID's.

    Parameters
    ----------
    data : dataframe
        A dataframe or series of original data.
    idx : list
        A list of ID's we want to keep.

    Returns
    -------
    data_of_reduced_resolution : dataframe

    '''
    data_of_reduced_resolution = data.iloc[idx]
    return data_of_reduced_resolution


@click.command('get-direction')
@click.argument(
    'field-path',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True)
)
@click.argument(
    'point-path',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True)
)
@click.argument(
    'direction',
    type=float
)
@click.argument(
    'reference_speed',
    type=float
)
@click.argument(
    'resolution',
    type=float
)
def return_list(field_path, point_path, direction, reference_speed, resolution):
    if resolution > 0:
        reduce = True
    else:
        reduce = False

    field_path = pathlib.Path(field_path)
    point_path = pathlib.Path(point_path)
    rounded_direction = round_direction(field_path, direction)
    field = pd.read_csv(field_path, usecols=[str(rounded_direction)])
    points = pd.read_csv(point_path, index_col=0)

    if reduce:
        # ID's of 3d points we keep, can be used to filter data.
        keep_ids = reduce_resolution(points, resolution)
        field = reduce_field(field, keep_ids)
        points = reduce_field(points, keep_ids)
        save_path = pathlib.PurePath(point_path)
        save_path = save_path.with_name("reduced_points.csv")
        points.to_csv(save_path)

    speed = (field * reference_speed).values.T.tolist()[0]
    click.echo(speed)
