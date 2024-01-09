import logging
import pandas as pd
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


class MatplotlibAssist:
    """
    Class to assist in labeling time series data
    Assumes that the index is a datetime index
    """
    def __init__(self,
                 ax: plt.Axes,
                 df: pd.DataFrame,
                 update_dict: dict = None,
                 index_timestamp_unit: str = None,
                 exit_function: callable = None):
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("Index must be a datetime index")
        if update_dict is None:
            raise ValueError("Update dict must be provided"
                             "\nExample: {'keyname': {'label_name': 123}}"
                             "\nKeyname is the key pressed and label_name is the column to update to value 123")
        if "start" in update_dict.keys() or "end" in update_dict.keys():
            raise ValueError("Start and end are reserved keywords, please use something else")

        self.ax = ax
        self.df = df
        self.save = False
        self.update_dict = update_dict
        self.temp_event = {}
        self.key_dict = {}
        self.index_timestamp_unit = index_timestamp_unit
        self.exit_function = exit_function

        self.temp_start_line = None
        self.temp_end_line = None

        # Used to save selected range
        self._global_start = self.df.index[0]
        self._global_end = self.df.index[-1]

    def connect(self):
        # Mouse buttons
        self.ax.figure.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.ax.figure.canvas.mpl_connect('button_release_event', self.on_mouse_release)

        # Keyboard keys
        self.ax.figure.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.ax.figure.canvas.mpl_connect('key_release_event', self.on_key_release)

        # On close
        self.ax.figure.canvas.mpl_connect('close_event', self.disconnect)

        # setup references to different lines with their label name for easy update
        self.lines = {line.properties()["label"]: line for line in self.ax.get_lines()}

        # Add a vertical line to indicate the start and end of the selected range
        self.temp_start_line = self.ax.axvline(self._global_start, color='grey', linestyle="--", label='start')
        self.temp_end_line = self.ax.axvline(self._global_end, color='grey', linestyle="--", label='end')

    def update_plot_line(self,
                         label_to_update,
                         offset=0):
        # When the data has been updated in the dataframe, we update the specific lines here
        self.lines[label_to_update].set_ydata(self.df[label_to_update] + offset)

        # Redraw canvas
        self.ax.figure.canvas.draw()
        self.ax.figure.canvas.flush_events()
        # time.sleep(0.1)

    def on_mouse_press(self, event):
        if event.inaxes == self.ax:
            if event.button == 1:
                self.temp_event["start"] = event.xdata
                self.temp_start_line.set_xdata([event.xdata])
                self.temp_start_line.set_visible(True)
                self.ax.figure.canvas.flush_events()
                self.ax.figure.canvas.draw()
            elif event.button == 3:
                self.temp_event["end"] = event.xdata
                self.temp_end_line.set_xdata([event.xdata])
                self.temp_end_line.set_visible(True)
                self.ax.figure.canvas.flush_events()
                self.ax.figure.canvas.draw()

    def on_mouse_release(self, event):
        pass

    def on_key_release(self, event):
        self.key_dict[event.key] = False

        if self.temp_event.get("start") is None or self.temp_event.get("end") is None:
            log.debug(f"Start or end not set, S: {self.temp_event.get('start')}, E: {self.temp_event.get('end')}")
            return

        # Order doesn't matter, so we sort them
        tempstart = min(self.temp_event.get("start"), self.temp_event.get("end"))
        tempend = max(self.temp_event.get("start"), self.temp_event.get("end"))

        if event.key in self.update_dict.keys():
            # Update the dataframe
            for label, value in self.update_dict[event.key].items():
                self.overwrite_value(self.update_dict[event.key][label],
                                     tempstart,
                                     tempend,
                                     label)
        else:
            # Dont reset
            return
        self.temp_start_line.set_visible(False)
        self.temp_end_line.set_visible(False)
        # And reset the temp event
        self.temp_event = {}
        self.ax.figure.canvas.draw()
        self.ax.figure.canvas.flush_events()

    def update_full_plot(self):
        """
        Updates the full plot
        :return:
        """
        for label, line in self.lines.items():
            line.set_xdata(self.df.index)
            line.set_ydata(self.df[label])

        self.ax.relim()
        self.ax.autoscale()
        self.ax.figure.canvas.flush_events()
        self.ax.figure.canvas.draw()

    def on_key_press(self, event):
        self.key_dict[event.key] = True
        if event.key == "left":
            if self.index_timestamp_unit is None:
                self.guess_timestamp_unit(event.xdata,
                                          index_start=self.df.index[0],
                                          index_end=self.df.index[-1])
            self.df = self.df.loc[pd.Timestamp(event.xdata, unit=self.index_timestamp_unit):]
            self.update_full_plot()
        if event.key == "right":
            if self.index_timestamp_unit is None:
                self.guess_timestamp_unit(event.xdata,
                                          index_start=self.df.index[0],
                                          index_end=self.df.index[-1])

            self.df = self.df.loc[:pd.Timestamp(event.xdata, unit=self.index_timestamp_unit)]
            self.update_full_plot()

    def guess_timestamp_unit(self,
                             timestamp,
                             index_start,
                             index_end):
        """
        Guesses the timestamp based on comparing a clicked datetime stamp, and the index of the dataframe
        :param start:
        :param end:
        :return:
        """
        possible_units = ["D", "h", "m", "s", "ms", "us", "ns"]
        possible_list = []
        for test_unit in possible_units:
            try:
                test_timestamp = pd.Timestamp(timestamp, unit=test_unit)
                if (test_timestamp > index_start) & (test_timestamp < index_end):
                    possible_list.append(test_unit)
            except ValueError:
                pass
        if len(possible_list) == 1:
            self.index_timestamp_unit = possible_list[0]
        elif len(possible_list) > 1:
            raise ValueError(f"Could not intuit in which units pandas has put the timestamps for the plot. "
                             f"Multiple possible units found: {possible_list}, please specify manually.")

    def overwrite_value(self,
                        new_value: float,
                        start: float,
                        end: float,
                        label: str):
        log.debug(f"Overwriting {label} from {start} to {end} with {new_value}")
        if self.index_timestamp_unit is None:
            self.guess_timestamp_unit(start,
                                      index_start=self.df.index[0],
                                      index_end=self.df.index[-1])

        after_start = (self.df.index >= pd.Timestamp(start, unit=self.index_timestamp_unit))
        before_end = (self.df.index <= pd.Timestamp(end, unit=self.index_timestamp_unit))
        self.df.loc[(after_start & before_end), label] = new_value
        self.update_plot_line(label)

    def disconnect(self, event):
        """
        Disconnects the matplotlib canvas, and closes the figure.
        You can supply an exit function to be called after the figure has been closed.
        For instance to save the dataframe to a file/cloud.
        :return:
        """
        plt.close(self.ax.figure)
        if self.exit_function is not None:
            self.exit_function(df = self.df)
