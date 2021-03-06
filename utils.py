import pandas
import sys


def get_path(key):
    path_config = pandas.read_csv("path_config.csv", index_col=0)
    return path_config.loc[key]["path"]


def welcome():
    print("Welcome!\nThis program is part of the research study")
    print("\"The Impact of Release-based Training on Software Vulnerability Prediction Models\"")
    print("by Giulia Sellitto and Filomena Ferrucci (University of Salerno, Italy) April 2021")


def bye():
    print("Bye!")
    sys.exit()


def space():
    print("--------------------------------")
