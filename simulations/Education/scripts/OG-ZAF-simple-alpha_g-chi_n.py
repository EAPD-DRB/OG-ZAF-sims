# Need to fix references to Calculator, reform json, and substitute new tax
# function call
import multiprocessing
from distributed import Client
import os
import json
import time
import copy
import importlib.resources
import matplotlib.pyplot as plt
from ogcore.parameters import Specifications
from ogcore import output_tables as ot
from ogcore import output_plots as op
from ogcore.execute import runner
from ogcore.utils import safe_read_pickle, param_dump_json

# Use a custom matplotlib style file for plots
plt.style.use("ogcore.OGcorePlots")


def main():
    # Define parameters to use for multiprocessing
    num_workers = min(multiprocessing.cpu_count(), 7)
    client = Client(n_workers=num_workers, threads_per_worker=1)
    print("Number of workers = ", num_workers)

    # Directories to save data
    CUR_DIR = os.path.dirname(os.path.realpath(__file__))
    save_dir = os.path.join(CUR_DIR, "OG-ZAF-MultipleIndustry-example")
    base_dir = os.path.join(save_dir, "OUTPUT_BASELINE")
    reform_dir = os.path.join(save_dir, "OUTPUT_REFORM")

    """
    ---------------------------------------------------------------------------
    Run baseline policy
    ---------------------------------------------------------------------------
    """
    # Set up baseline parameterization
    p = Specifications(
        baseline=True,
        num_workers=num_workers,
        baseline_dir=base_dir,
        output_base=base_dir,
    )
    # Update parameters for baseline from default json file
    with importlib.resources.open_text(
        "ogzaf", "ogzaf_default_parameters_multisector.json"
    ) as file:
        defaults = json.load(file)
    p.update_specifications(defaults)

    # Run model
    start_time = time.time()
    # runner(p, time_path=True, client=client)
    print("run time = ", time.time() - start_time)

    """
    ---------------------------------------------------------------------------
    Run reform policy
    ---------------------------------------------------------------------------
    """

    # create new Specifications object for reform simulation
    p2 = copy.deepcopy(p)
    p2.baseline = False
    p2.output_base = reform_dir

    p2.alpha_G = p2.alpha_G * 1.071
    # Adjust alpha_G for different periods
    # The factors are chosen to gradually increase alpha_G over time.
    # The first three periods have a small increase of 0.2% each.
    # The next three periods have a larger increase of 3.5% each.
    # The final period has the largest increase of 7.1%.
    # alpha_G_factors = [1.002, 1.002, 1.002, 1.035, 1.035, 1.035, 1.071]
    # p2.alpha_G = [p2.alpha_G * factor for factor in alpha_G_factors]

    # decrease the first 15 values in the matrix chi_n by 5 (ages 20-35)
    p2.chi_n[:15] -= 5

    # Run model
    start_time = time.time()
    runner(p2, time_path=True, client=client)
    print("run time = ", time.time() - start_time)
    client.close()

    """
    ---------------------------------------------------------------------------
    Save some results of simulations
    ---------------------------------------------------------------------------
    """
    base_tpi = safe_read_pickle(os.path.join(base_dir, "TPI", "TPI_vars.pkl"))
    base_params = safe_read_pickle(os.path.join(base_dir, "model_params.pkl"))
    reform_tpi = safe_read_pickle(os.path.join(reform_dir, "TPI", "TPI_vars.pkl"))
    reform_params = safe_read_pickle(os.path.join(reform_dir, "model_params.pkl"))
    ans = ot.macro_table(
        base_tpi,
        base_params,
        reform_tpi=reform_tpi,
        reform_params=reform_params,
        var_list=["Y", "C", "K", "L", "r", "w"],
        output_type="pct_diff",
        num_years=10,
        start_year=base_params.start_year,
    )

    # create plots of output
    op.plot_all(
        base_dir,
        reform_dir,
        os.path.join(save_dir, "OG-ZAF-MultipleIndustry-example_plots"),
    )

    print("Percentage changes in aggregates:", ans)
    # save percentage change output to csv file
    ans.to_csv(os.path.join(save_dir, "OG-ZAF-MultipleIndustry-example_output.csv"))


if __name__ == "__main__":
    # execute only if run as a script
    main()
