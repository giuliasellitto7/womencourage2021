import utils
import pandas
import os
from experiments_classes import Log, Approach, Validation
from experiments_implementation import execute_experiment


def choose(enumeration):
    choosen = []
    print("Please choose " + enumeration.__name__)
    items = list(enumeration)
    for x in items:
        print(str(x.value) + ": " + x.name)
    print("You can do multiple choices separated by space")
    selection = input("Selection:")
    choices = selection.split(" ")
    for c in choices:
        if c.isnumeric():
            if int(c) <= len(items):
                choosen.append(items[int(c)-1].name)
    if len(choosen) == 0:
        print("Invalid selection!")
        choose(enumeration)
    print(choosen)
    return choosen


utils.welcome()

output_file = utils.get_path("my_experiments_csv_file")
if not os.path.exists(output_file):
    # prepare csv file for experiments output
    header = Log.header
    pandas.DataFrame(header).to_csv(output_file, index=False)

utils.space()
approaches = choose(Approach)
utils.space()
validations = choose(Validation)
utils.space()
n = 0
for a in approaches:
    for v in validations:
        n = n + 1
        log = execute_experiment(n, a, v)
        pandas.DataFrame(log).to_csv(output_file, mode='a', index=False, header=False)

utils.space()
print("All done!")
print(str(n) + " experiments saved to file: " + output_file)
utils.bye()
