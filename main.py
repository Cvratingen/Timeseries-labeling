import math
import pandas as pd
import matplotlib.pyplot as plt

from label import MatplotlibAssist


if __name__ == '__main__':
    # This example variable is a sine wave with a different frequency from the halfway point

    date_range = pd.date_range(start="2020-01-01", periods=1000, freq="1min")
    example_df = pd.DataFrame({
        "Independent_var": (
                [math.sin(x / (2 * math.pi)) * 4 + 5.5 for x in range(500)] +
                [math.sin(x / (10 * math.pi)) * 4 + 5.5 for x in range(500, 1000)]),
        "Dependent_var_1": [int(x < 500) for x in range(1000)],
        "Dependent_var_2": [int(x > 550) - 2 for x in range(1000)],
        "time_stamp": date_range}).set_index("time_stamp")

    update_dict = {
        "1": {"Dependent_var_1": 1.0},
        "0": {"Dependent_var_2": -2.0, "Dependent_var_1": 0.0},  # Can update multiple columns
        "2": {"Dependent_var_2": -1.0},
    }
    fig = example_df.plot(title=f"Time series labeling example")
    handler_instance = MatplotlibAssist(
        ax=fig,
        df=example_df,
        update_dict=update_dict,
        exit_function=lambda df: df.to_csv("labeled_data.csv")
    )
    handler_instance.connect()
    plt.show(block=True)

