# -*- coding: utf-8 -*-
"""
Created on Tue Jul  6 10:52:07 2021

@author: DarrenLynch
"""

import pathlib
from datetime import datetime

import ladybug.epw as epw
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import pandas as pd
from scipy.stats import weibull_min


class HourlyContinuous():

    def __init__(self):
        self.weather_period = WeatherPeriod()
        self.period_name = None
        self._hourly_wind_speed = []
        self._hourly_direction = []
        self._hourly_timestamp = []

        self._original_data = None
        self._original_df = None

        self.hourly_continuous_df = None

    def import_epw(self, epw_file):
        self._original_data = epw.EPW(epw_file)

        self._hourly_wind_speed = self._original_data.wind_speed.values
        self._hourly_direction = self._original_data.wind_direction.values
        self._hourly_timestamp = self._original_data.wind_speed.datetimes

        frames = [pd.DataFrame(self._hourly_timestamp, columns=["datetime"]),
                  pd.DataFrame(self._hourly_direction, columns=["direction"]),
                  pd.DataFrame(self._hourly_wind_speed, columns=["speed"])]
        df = pd.concat(frames, axis=1)
        self.hourly_continuous_df = df.set_index("datetime")
        self._original_df = self.hourly_continuous_df
        self._remove_zero_speeds()

    def import_wrplot_view(self, file):
        pass

    def _remove_zero_speeds(self):
        df = self.hourly_continuous_df
        df = df[df['speed'] != 0]
        self.hourly_continuous_df = df

 
    def import_hourly_wind_data_from_excel(self, file):
    
        df = pd.read_excel(file, index_col='dateAndTime')
        df = df.get([ 'Speed (m/s)', 'WindDirection(degrees)' ])
        df.columns = ["speed", "direction"]
        df.index = pd.to_datetime(df.index, format='%Y-%m-%d_%H:%M')
        
        self.hourly_continuous_df = df
        self._original_df = self.hourly_continuous_df
        
        self._remove_zero_speeds()
        if "VRB" in df['direction'].values :
            self._remove_VRB_from_directions()
    
    def _remove_VRB_from_directions(self):
        df = self.hourly_continuous_df
        df = df[df['direction'] != "VRB"]
        self.hourly_continuous_df = df


    def import_city_of_london_historic(self, file):
        df = pd.read_excel(file, index_col='dateAndTime')
        df = df.get(['windSpeed(km/h)', 'windDirection(degEofN)'])
        df.columns = ["speed", "direction"]
        df.index = pd.to_datetime(df.index, format='%Y-%m-%d_%H:%M')

        # Convert km/h to m/s
        df['speed'] = df['speed'] * (1000 / 3600)
        
        self.hourly_continuous_df = df
        self._original_df = self.hourly_continuous_df

    def set_period(self, period):
        self.weather_period = period
        self.apply_period()

    def apply_period(self):
        self.period_name = self.weather_period.period_name

        df = self.hourly_continuous_df
        period = self.weather_period
        dates = pd.Series(pd.date_range(period.start, period.end))
        no_year = dates.map(lambda x: x.strftime("%m-%d"))
        df["no_year"] = df.index.map(lambda x: x.strftime("%m-%d"))
        mask = df["no_year"].isin(no_year)

        df = df.loc[mask]
        df = df.between_time('{}:00'.format(period.get_start_hour()),
                             '{}:00'.format(period.get_end_hour()),
                             include_start=True, include_end=True)
        self.hourly_continuous_df = df


class WeatherPeriod():

    def __init__(self):
        self.period_name = None
        self.start = None
        self.end = None

    def set_end_datetime(self, end_hour, end_day, end_month):
        self.end = datetime(year=2005,
                            month=end_month,
                            day=end_day,
                            hour=end_hour)

    def set_start_datetime(self, start_hour, start_day, start_month):
        self.start = datetime(year=2005,
                              month=start_month,
                              day=start_day,
                              hour=start_hour)

    def set_name(self, period_name):
        self.period_name = period_name

    def get_start_day(self):
        return self.start.day

    def get_start_hour(self):
        return self.start.hour

    def get_start_month(self):
        return self.start.month

    def get_end_day(self):
        return self.end.day

    def get_end_hour(self):
        return self.end.hour

    def get_end_month(self):
        return self.end.month


def add_mid_angle(angle1, angle2):
    return ((angle1 + angle2) / 2)


# def minus_mid_angle(angle1, angle2):
# return ((((angle1 - angle2))/2)%360

def angle_to_vectors(angle):
    u = np.cos(np.radians(angle))
    v = np.sin(np.radians(angle))
    return u, v


def return_quad(u, v):
    if np.sign(u) > 0 and np.sign(v) > 0:
        return 1
    elif np.sign(u) > 0 and np.sign(v) < 0:
        return 4
    elif np.sign(u) < 0 and np.sign(v) < 0:
        return 3
    elif np.sign(u) < 0 and np.sign(v) > 0:
        return 2


def check_within_bounds(upper, lower, angle):
    u_upper, v_upper = angle_to_vectors(upper)
    u_lower, v_lower = angle_to_vectors(lower)
    u, v = angle_to_vectors(angle)

    q_upper = return_quad(u_upper, v_upper)
    q_lower = return_quad(u_lower, v_lower)

    if (q_lower > q_upper) and (((angle > lower) and (angle <= 360)) or ((angle <= upper) and (angle >= 0))):
        return True
    elif (angle <= upper) and (angle > lower):
        return True
    else:
        return False


check = check_within_bounds(270, 5, 0)


def round_dir(df, directions):
    number_directions = len(directions)
    upper_lim = []
    lower_lim = []
    for i in range(number_directions):

        angle1 = (directions[i] + 180) % 360 - 180
        angle2 = (directions[i - 1] + 180) % 360 - 180
        if angle2 != 0 and angle2 / angle2 > 0 and angle1 == -180:
            angle1 = 180
        elif angle2 != 0 and angle2 / angle2 < 0 and angle1 == 180:
            angle1 = -180
        dif = add_mid_angle(angle1, angle2)
        angle = dif
        lower_lim.append(angle % 360)

    for i in range(number_directions):
        upper_lim.append(lower_lim[i - (number_directions - 1)])

    df["old_dir"] = df["direction"]

    for upper, lower, value in zip(upper_lim, lower_lim, directions):
        mask = df["direction"].apply(
            lambda x: check_within_bounds(upper, lower, x))
        df["direction"] = df["direction"].mask(mask, value)
    return df, upper_lim, lower_lim


def round_speed(df, speeds):
    number_speeds = len(speeds)
    for i in range(0, number_speeds):
        upper = speeds[i + 1]
        lower = speeds[i]

        mask = df["speed"].between(lower, upper)
        df["speed"] = df["speed"].mask(mask, (upper + lower) / 2)

    return df


def get_weibull(group):
    ws = group[1]["speed"]
    drop_zero = (ws != 0)
    ws = ws.loc[drop_zero]
    shape, loc, scale = weibull_min.fit(ws, floc=0)
    return shape, scale


def find_group(groups, direction):
    for group in groups:
        if group[0] == direction:
            return group
            break


# Create a file format that is identical to the SimScale Stat file requirements
def createData(data):
    '''
    A pre-processing step called in exportSTAT()
    
    Parameters
    ----------
    data : DataFrame
        This data frame contains a 2D matrix of frequencies, where the column 
        name is..

    Returns
    -------
    output : DataFrame
        A reformated DataFrame with format specific index and headers.
    nDir : int
        An integer with the number of directions, required for formating purposes.
    '''
    table = data.to_numpy()

    # assume the index contains the directions
    direction = data.index
    # assume the column headers contain the speeds
    speed = data.columns.to_series().astype(float).to_numpy()

    # make a string label for a stat file
    directionLabel = []
    for directions in direction:
        directionLabel.append('    N (' + str(directions) + ')')

    # make a speed label for a stat file
    speedLabel = []
    for speeds in speed:
        speedLabel.append('   <=' + str(speeds))

    output = pd.DataFrame(data=table, index=directionLabel, columns=speedLabel)
    nDir = len(direction)
    return output.round(4), nDir


def exportSTAT(data, file):
    '''
    Parameters
    ----------
    data : DataFrame
        This data frame contains a 2D matrix of frequencies, where the column 
        name is.

    Returns
    -------
    success: Bool.
        True if successful
    
    NOTE:
        to call this function use a command similar to
        file = 'data_export.stat'
        export = exportSTAT(df, file)
    '''
    success = False

    try:
        output, nDirections = createData(data)

        output.to_csv(file, sep='\t')

        with open(file, 'r') as original:
            output = original.read()
        with open(file, 'w') as modified:
            modified.write(' - Wind Frequency (m/s) by Direction {Interval ' + str(
                360 / nDirections) + 'deg from displayed deg) [%]\n' + output)
        success = True
    except:
        print('Failed to export')
    return success


class WeatherStatistics():

    def __init__(self):
        self.period_name = None

        self.hourly_continuous = HourlyContinuous()

        self.directions = []
        self.speeds = []
        self.direction_upper_bound = []
        self.direction_lower_bound = []
        self.meteo_correctors = {}

        self.group_names = None
        self.groups = None
        self.weibull_parameters = None
        self.total_probability = None
        self.maximum_values = None
        self.minimum_values = None
        self.standard_table = None

        self.gumbel_block_period = None
        self.gumbel_dispersion = None
        self.gumbel_mode = None
        self.gumbel_data = None

        self.extreeme_speed = None

    def set_wind_conditions(self, wind_conditions):
        self.directions = wind_conditions.directions
        self.meteo_correctors = wind_conditions.meteo_correctors

    def set_directions(self, directions_list):
        self.directions = directions_list

    def set_speeds(self, speed_list):
        '''
        

        Parameters
        ----------
        speed_list : np.array
            An array of speeds, this should not include 0, a recomendation 
            is would be to use np.array(0.5, 30, 2).

        Returns
        -------
        None.

        '''

        if np.min(speed_list) == 0:
            raise Exception('List should not contain 0 as a bin, is will',
                            'always be empty')

        self.speeds = speed_list

    def set_hourly_continuous(self, hourly_continuous):

        self.period_name = hourly_continuous.period_name

        df = hourly_continuous.hourly_continuous_df

        df, upper, lower = round_dir(df, self.directions)

        hourly_continuous.hourly_continuous_df = df

        self.hourly_continuous = hourly_continuous
        self.direction_upper_bound = upper
        self.direction_lower_bound = lower

        self.sort_directions()
        self.set_weibull_parameters()
        self.set_standard_table()

    def sort_directions(self):
        df = self.hourly_continuous.hourly_continuous_df
        drop_zero = (df["speed"] != 0)
        df = df.loc[drop_zero].copy()
        _list = df.groupby(["direction"])
        self.group_names = list(_list.groups)
        self.groups = list(_list)

    def set_weibull_parameters(self):
        df = pd.DataFrame(
            np.zeros((3, len(self.group_names))),
            index=["shape", "scale", "probability"],
            columns=self.group_names
        )

        for group in self.groups:
            df.loc["shape", group[0]], df.loc["scale", group[0]] = get_weibull(group)

        df.loc["probability", :] = self.get_directional_occurances().values
        self.weibull_parameters = df

    def plot_weibull(self, direction):
        group = find_group(self.groups, direction)
        ws = group[1]["speed"]
        plt.hist(ws, density=True, alpha=0.5)
        support = np.linspace(ws.min(), ws.max(), 100)

        shape = self.weibull_parameters.loc["shape", direction]
        scale = self.weibull_parameters.loc["scale", direction]
        plt.plot(support, weibull_min.pdf(support, shape, 0, scale), "r-", lw=3)
        plt.xlabel('Wind Speed (m/s)')
        plt.ylabel('Probability')
        plt.show()

    def set_standard_table(self):
        df = pd.DataFrame(
            np.zeros((len(self.speeds), len(self.directions))),
            index=self.speeds,
            columns=self.directions
        )

        directional_occurances = self.get_directional_occurances()

        for group in self.groups:
            direction = group[0]
            shape = self.weibull_parameters.loc["shape", direction]
            scale = self.weibull_parameters.loc["scale", direction]

            cum_probability = weibull_min.cdf(self.speeds, shape, 0, scale)
            probability_next = np.roll(cum_probability, 1)
            probability_next[0] = 0

            range_probability = cum_probability - probability_next
            df[direction] = range_probability * float(directional_occurances[direction])

        self.standard_table = df.transpose()
        
    def standard_table_from_weibull(self):
        df = pd.DataFrame(
            np.zeros((len(self.speeds), len(self.directions))),
            index=self.speeds,
            columns=self.directions
        )
        
        for direction in self.directions:
            shape = self.weibull_parameters.loc["shape", direction]
            scale = self.weibull_parameters.loc["scale", direction]
            probability = self.weibull_parameters.loc["probability", direction]

            cum_probability = weibull_min.cdf(self.speeds, shape, 0, scale)
            probability_next = np.roll(cum_probability, 1)
            probability_next[0] = 0

            range_probability = cum_probability - probability_next
            
            df[direction] = range_probability * probability
            
        self.total_probability = np.sum(self.weibull_parameters.loc["probability"])
        error = (1 - self.total_probability)
        
        if error > 0.01:
            distribution = self.weibull_parameters.loc["probability"]\
                           * 1/self.total_probability
                           
            missing_probablity = distribution * error
            
            df.iloc[0, :] = df.iloc[0, :] + missing_probablity
            
            self.total_probability = np.sum(df.values)
            
        self.standard_table = df.transpose()

    def check_sum_probability(self):
        df = self.standard_table
        tot = df.to_numpy().sum()
        return tot

    def get_directional_occurances(self):
        df = pd.DataFrame(
            np.zeros((1, len(self.group_names))),
            index=["size"],
            columns=self.group_names
        )
        peried_size = 0
        for group in self.groups:
            size = group[1].shape[0]
            df[group[0]] = size
            peried_size += size

        df = df / peried_size
        return df

    def to_stat(self):
        df = self.standard_table
        if self.period_name == None:
            self.period_name = "annual"
        name = self.period_name + ".stat"
        file = pathlib.Path.cwd() / name
        exportSTAT(df, file)

    def plot_cumulative_distributions(self, max_speed=10):
        weibull = self.weibull_parameters
        speeds = np.arange(0, max_speed, 0.1)

        mpl.rcParams['figure.dpi'] = 2400
        fig, axs = plt.subplots(1, 2, )  # sharey=True)

        labels = weibull.columns
        freqs = np.ones([len(speeds), len(labels)])
        freqs = pd.DataFrame(data=freqs, columns=weibull.columns, index=speeds)
        l1 = []

        legend_labels = []
        for label in labels:
            legend_labels.append("Directional Probabillity {}°".format(label))

        for direction in weibull.columns:
            shape = weibull.loc["shape", direction]
            scale = weibull.loc["scale", direction]
            P = weibull.loc["probability", direction]
            frq = (weibull_min.sf(speeds, shape, 0, scale)) * P
            freqs[direction] = frq
            l1.append(axs[0].plot(speeds, frq)[0])

        axs[0].set_ylabel("Probability", fontsize=10)
        axs[0].set_xlabel("Speed (m/s)", fontsize=10)
        axs[1].set_xlabel("Speed (m/s)", fontsize=10)

        total_freqs = freqs.sum(axis=1)
        l2 = axs[1].plot(speeds, total_freqs)[0]
        fig.legend(l1,
                   legend_labels,
                   loc='lower center',
                   bbox_to_anchor=(0.35, 0.55),
                   fontsize=5,
                   frameon=False
                   )

        fig.legend([l2],
                   ["Total Probability"],
                   loc='lower center',
                   bbox_to_anchor=(0.75, 0.75),
                   fontsize=5,
                   frameon=False
                   )
        fig.suptitle("Directional and Total Probabilities of Exceedance")
        plt.savefig('probability_of_exceedance.png')
        plt.show()

    def plot_probability_distributions(self, max_speed=10):
        weibull = self.weibull_parameters
        speeds = np.arange(0, max_speed, 0.1)

        mpl.rcParams['figure.dpi'] = 2400
        fig, axs = plt.subplots(1, 2, )  # sharey=True)

        labels = weibull.columns
        freqs = np.ones([len(speeds), len(labels)])
        freqs = pd.DataFrame(data=freqs, columns=weibull.columns, index=speeds)
        l1 = []

        legend_labels = []
        for label in labels:
            legend_labels.append("Directional Probabillity {}°".format(label))

        for direction in weibull.columns:
            shape = weibull.loc["shape", direction]
            scale = weibull.loc["scale", direction]
            P = weibull.loc["probability", direction]
            frq = (weibull_min.pdf(speeds, shape, 0, scale)) * P
            freqs[direction] = frq
            l1.append(axs[0].plot(speeds, frq)[0])

        axs[0].set_ylabel("Probability", fontsize=10)
        axs[0].set_xlabel("Speed (m/s)", fontsize=10)
        axs[1].set_xlabel("Speed (m/s)", fontsize=10)

        total_freqs = freqs.sum(axis=1)
        l2 = axs[1].plot(speeds, total_freqs)[0]
        fig.legend(l1,
                   legend_labels,
                   loc='lower center',
                   bbox_to_anchor=(0.35, 0.55),
                   fontsize=5,
                   frameon=False
                   )

        fig.legend([l2],
                   ["Total Probability"],
                   loc='lower center',
                   bbox_to_anchor=(0.75, 0.75),
                   fontsize=5,
                   frameon=False
                   )
        fig.suptitle("Directional and Total Probabilities of occurance")
        plt.savefig('probability_of_occurance.png')
        plt.show()

    def get_highest_speeds(self, periods='year'):
        df = self.hourly_continuous.hourly_continuous_df
        df = df['speed']

        if periods == 'year':
            groups = df.groupby([df.index.year])
            self.gumbel_block_period = 1
        elif periods == 'quarter':
            per = df.index.to_period("Q")
            groups = df.groupby(per)
            self.gumbel_block_period = 1 * 4
        elif periods == 'month':
            per = df.index.to_period("M")
            groups = df.groupby(per)
            self.gumbel_block_period = 1 * 12
        elif periods == 'day':
            per = df.index.to_period("D")
            groups = df.groupby(per)
            self.gumbel_block_period = 1 * 365

        dataframes = []
        columns = []

        for group in groups:
            columns.append(group[0])
            dataframes.append(group[1])

        dataframes = pd.concat(dataframes, axis=1)
        dataframes.columns = columns

        maximum_speeds = dataframes.max(axis=0)
        self.maximum_values = maximum_speeds

    def get_gumbel_extreeme_speed(self, in_years=10):

        max_speeds = self.maximum_values

        max_speeds_sorted = np.sort(max_speeds.values)

        max_rank = len(max_speeds_sorted)

        rank = np.arange(1, max_rank + 1)

        gumbel_prob_non_exceeding = rank / (max_rank + 1)
        gumbel_reduced_variate = -np.log(-np.log(gumbel_prob_non_exceeding))

        [gumbel_dispersion, gumbel_mode] = np.polyfit(gumbel_reduced_variate,
                                                      max_speeds_sorted, 1)

        self.gumbel_dispersion = gumbel_dispersion
        self.gumbel_mode = gumbel_mode
        self.gumbel_data = pd.DataFrame(
            np.array([max_speeds_sorted, gumbel_reduced_variate]).T,
            columns=["Max Speeds (m/s)", "Reduced Variate"])

        self.extreeme_speed = (self.gumbel_mode
                               + self.gumbel_dispersion
                               * (-np.log(-np.log(1 - 1 / (in_years * self.gumbel_block_period)))))

    def plot_gumbel_correlation(self):
        gumbel_reduced_variate = self.gumbel_data["Reduced Variate"]

        plt.figure(num=3, figsize=(8, 6))
        plt.scatter(gumbel_reduced_variate, self.gumbel_data["Max Speeds (m/s)"])

        x = np.linspace(min(gumbel_reduced_variate),
                        max(gumbel_reduced_variate),
                        50)

        plt.plot(x, self.gumbel_mode + self.gumbel_dispersion * x)
        plt.text(0.1, 0.8, 'Mode = ' + str(round(self.gumbel_mode, 2)) +
                 '\nSlope = ' + str(round(self.gumbel_dispersion, 2)),
                 transform=plt.gca().transAxes)
        plt.ylabel('Maximum annual gust wind speed m/s')
        plt.xlabel('Reduced variate')
        plt.title('Gumbel Method')
        plt.grid(True)

    def plot_windrose(self):
        table = self.standard_table.T
        cum_table = np.cumsum(table.to_numpy(), axis=0)

        fig, ax = plt.subplots(subplot_kw={"projection": "polar"})

        labels = []
        for i in range(0, len(self.speeds)):
            if i == 0:
                labels.append('U < {} m/s'.format(self.speeds[i]))
            else:
                labels.append('{} m/s >= U > {} m/s'.format(
                    self.speeds[i-1], self.speeds[i]))

        offset = np.pi / 2
        width = (2 * np.pi / table.shape[1])
        # Specify offset
        ax.set_theta_offset(offset)
        ax.set_theta_direction(-1)

        # Set limits for radial (y) axis. The negative lower bound creates the whole in the middle.
        #ax.set_ylim(0)

        # Remove all spines
        ax.set_frame_on(False)

        # Remove grid and tick marks
        ax.xaxis.grid(False)
        ax.yaxis.grid(False)

        print(type(table.columns.to_numpy()))
        angles = np.radians(table.columns)

        colors = cm.winter(self.speeds / 10)

        bars = []
        for i in range(0, table.shape[0]):
            if i == 0:
                bar = ax.bar(angles, table.iloc[i, :],
                              width=width, linewidth=1,
                              color=colors[i, :], edgecolor="black"
                              )
            else:
                bar = ax.bar(angles, table.iloc[i, :],
                             width=width, linewidth=1,
                             color=colors[i, :], edgecolor="black",
                             bottom=cum_table[i-1, :]
                             )
            bars.append(bar)

        ax.legend(bars, labels, loc=5, bbox_to_anchor=(2, 0.5), frameon=False)
        fig.suptitle('Windrose for period: {}'.format(self.period_name), fontsize=16, y=1.1, ha='center')