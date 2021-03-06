from experiments_classes import Log, Approach, Validation
from experiments_implementation import execute_experiment
import utils
import pandas


utils.welcome()

output_file = utils.get_path("my_replication_csv_file")
header = Log.header
pandas.DataFrame(header).to_csv(output_file, index=False)

n = 0
for a in list(Approach):
    for v in list(Validation):
        n = n + 1
        log = execute_experiment(n, a.name, v.name, custom=False)
        pandas.DataFrame(log).to_csv(output_file, mode='a', index=False, header=False)

utils.space()
print("All done!")
print(str(n) + " experiments saved to file: " + output_file)
utils.bye()
