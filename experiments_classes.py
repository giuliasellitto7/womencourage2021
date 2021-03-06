from enum import Enum, IntEnum
from datetime import datetime


class DefaultReplication(Enum):
    phpmyadmin_metrics_training_from = "RELEASE_2_02_1"
    phpmyadmin_metrics_training_to = "RELEASE_3_5_8"
    phpmyadmin_metrics_test_from = "RELEASE_4_0_0"
    phpmyadmin_metrics_test_to = "RELEASE_4_0_9"
    phpmyadmin_text_training_from = "RELEASE_2_02_0"
    phpmyadmin_text_training_to = "RELEASE_3_5_8"
    phpmyadmin_text_test_from = "RELEASE_4_0_0"
    phpmyadmin_text_test_to = "RELEASE_4_0_9"


class Performance:
    def __init__(self, fit_time, precision, recall, accuracy, inspection_rate, f1_score, mcc):
        self.fit_time = fit_time
        self.precision = precision
        self.recall = recall
        self.accuracy = accuracy
        self.inspection_rate = inspection_rate
        self.f1_score = f1_score
        self.mcc = mcc


class DatasetReleases:
    def __init__(self, training_set_from, training_set_to, test_set_from, test_set_to):
        self.training_set_from = training_set_from
        self.training_set_to = training_set_to
        self.test_set_from = test_set_from
        self.test_set_to = test_set_to

    @staticmethod
    def perfect():
        return DatasetReleases("ALL", "ALL", "ALL", "ALL")


class Log:
    header = {"date_time": [], "approach": [], "validation": [],
              "training_set_from": [], "training_set_to": [], "test_set_from": [], "test_set_to": [],
              "fit_time": [], "precision": [], "recall": [], "accuracy": [], "inspection_rate": [],
              "f1_score": [], "mcc": []}

    @staticmethod
    def build(approach, validation, dataset_releases, performance):
        # dd/mm/YY H:M:S
        now_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        return {"date_time": [now_string], "approach": [approach], "validation": [validation],
                "training_set_from": [dataset_releases.training_set_from], "training_set_to": [dataset_releases.training_set_to],
                "test_set_from": [dataset_releases.test_set_from], "test_set_to": [dataset_releases.test_set_to],
                "fit_time": [performance.fit_time], "precision": [performance.precision], "recall": [performance.recall],
                "accuracy": [performance.accuracy], "inspection_rate": [performance.inspection_rate],
                "f1_score": [performance.f1_score], "mcc": [performance.mcc]}

    dummy = {"date_time": ["now"], "approach": ["approach"], "validation": ["validation"],
             "training_set_from": ["trainf"], "training_set_to": ["traint"],
             "test_set_from": ["testf"], "test_set_to": ["testt"],
             "fit_time": [10], "precision": [1], "recall": [1], "accuracy": [3], "inspection_rate": [4],
             "f1_score": [5], "mcc": [6]}


class Approach(IntEnum):
    metrics = 1
    text = 2


class Validation(IntEnum):
    cross_validation = 1
    release_based = 2

