from datetime import datetime
import json
import numpy
from numpy import unique
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_validate
from sklearn.metrics import confusion_matrix, precision_score, recall_score, accuracy_score
from sklearn.metrics import f1_score, matthews_corrcoef
from statistics import mean
from imblearn.under_sampling import RandomUnderSampler
import os
import pandas
import utils
from experiments_classes import DefaultReplication, Log, Performance, DatasetReleases
from time import time


def execute_experiment(n, approach, validation, custom=True):
    utils.space()
    print("Experiment " + str(n))
    utils.space()
    print("Approach: " + approach)
    print("Validation: " + validation)
    utils.space()
    if validation == "release_based":
        # get names of starting and ending release to use in each set
        dataset_releases = get_train_test_releases(approach, custom)
        X_train, y_train, X_test, y_test = get_release_based_dataset(approach, dataset_releases)
        X_train, y_train = balance(X_train, y_train)
        performance = experiment_release_based(X_train, y_train, X_test, y_test)
    else:  # cross_validation
        dataset_releases = DatasetReleases.perfect()
        X, y = get_cross_validation_dataset(approach)
        X, y = balance(X, y)
        performance = experiment_cross_validation(X, y)
    utils.space()
    print_performance(performance)
    utils.space()
    log = Log.build(approach, validation, dataset_releases, performance)
    return log


def print_performance(performance):
    print("Performance Summary:")
    print("Fit time: " + str(performance.fit_time) + " sec")
    print("Precision: " + str(performance.precision))
    print("Recall: " + str(performance.recall))
    print("Accuracy: " + str(performance.accuracy))
    print("Inspection rate: " + str(performance.inspection_rate))
    print("F1-score: " + str(performance.f1_score))
    print("MCC: " + str(performance.mcc))


def my_scorer(classifier, X, y):
    y_pred = classifier.predict(X)
    cm = confusion_matrix(y, y_pred)
    tn = cm[0, 0]
    fp = cm[0, 1]
    fn = cm[1, 0]
    tp = cm[1, 1]
    inspection_rate = (tp + fp) / (tp + tn + fp + fn)
    precision = precision_score(y, y_pred)
    recall = recall_score(y, y_pred)
    accuracy = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred)
    mcc = matthews_corrcoef(y, y_pred)
    return {"my_precision": precision, "my_recall": recall, "my_accuracy": accuracy,
            "my_inspection_rate": inspection_rate, "my_f1_score": f1, "my_mcc": mcc}


def balance(X, y):
    print_class_distribution(y)
    print("Performing undersampling...")
    # define undersample strategy: the majority class will be undersampled to match the minority
    undersample = RandomUnderSampler(sampling_strategy='majority')
    X, y = undersample.fit_resample(X, y)
    print_class_distribution(y)
    return X, y


def experiment_cross_validation(X, y):
    classifier = RandomForestClassifier()
    print("Starting experiment")
    print("3-fold cross validation...")
    score = cross_validate(classifier, X, y, cv=3, scoring=my_scorer)
    print("Done.")
    performance = Performance(fit_time=mean(score["fit_time"]), precision=mean(score["test_my_precision"]),
                              recall=mean(score["test_my_recall"]), accuracy=mean(score["test_my_accuracy"]),
                              inspection_rate=mean(score["test_my_inspection_rate"]),
                              f1_score=mean(score["test_my_f1_score"]), mcc=mean(score["test_my_mcc"]))
    return performance


def experiment_release_based(X_train, y_train, X_test, y_test):
    classifier = RandomForestClassifier()
    print("Starting experiment")
    print("Training...")
    start = time()
    classifier.fit(X_train, y_train)
    stop = time()
    print("Testing...")
    score = my_scorer(classifier, X_test, y_test)
    print("Done.")
    performance = Performance(fit_time=stop-start, precision=score["my_precision"],
                              recall=score["my_recall"], accuracy=score["my_accuracy"],
                              inspection_rate=score["my_inspection_rate"],
                              f1_score=score["my_f1_score"], mcc=score["my_mcc"])
    return performance


def print_class_distribution(y):
    print("Dataset Summary: (0 is neutral, 1 is vulnerable)")
    classes = unique(y)
    total = len(y)
    for c in classes:
        n_examples = len(y[y == c])
        percent = n_examples / total * 100
        print('Class %d: %d/%d (%.1f%%)' % (c, n_examples, total, percent))


def get_train_test_releases(approach, custom):
    if custom:
        all_df_dir = utils.get_path("my_" + approach + "_csv_phpmyadmin")
        all_df_file_names = os.listdir(all_df_dir)
        num_files = len(all_df_file_names)
        to_choose = ["Training set starting release", "Training set ending release", "Test set starting release",
                     "Test set ending release"]
        chosen = []
        start_list_from = 0
        for x in range(4):
            print("Please choose " + to_choose[x])
            for i in range(num_files):
                if i >= start_list_from:
                    print(str(i) + ": " + all_df_file_names[i][:-4])
            loop = True
            while loop:
                selection = input("Selection: ")
                if selection.isnumeric():
                    chosen.append(all_df_file_names[int(selection)][:-4])
                    print(chosen[x])
                    utils.space()
                    start_list_from = int(selection) 
                    loop = False
                else:
                    print("Invalid selection!")
        dataset_releases = DatasetReleases(training_set_from=chosen[0], training_set_to=chosen[1],
                                           test_set_from=chosen[2], test_set_to=chosen[3])
    else:
        dataset_releases = DatasetReleases(training_set_from=DefaultReplication.__getitem__("phpmyadmin_" + approach + "_training_from").value,
                                           training_set_to=DefaultReplication.__getitem__("phpmyadmin_" + approach + "_training_to").value,
                                           test_set_from=DefaultReplication.__getitem__("phpmyadmin_" + approach + "_test_from").value,
                                           test_set_to=DefaultReplication.__getitem__("phpmyadmin_" + approach + "_test_to").value)
    return dataset_releases


def get_release_based_dataset(approach, dataset_releases):
    all_df_dir = utils.get_path("my_" + approach + "_csv_phpmyadmin")
    all_df_file_names = os.listdir(all_df_dir)

    # retrieve training set
    train_from_i = all_df_file_names.index(dataset_releases.training_set_from + ".csv")
    train_to_i = all_df_file_names.index(dataset_releases.training_set_to + ".csv")
    train = all_df_file_names[train_from_i:train_to_i+1]
    print("Training set: ")
    print(train)
    train_df = pandas.read_csv(os.path.join(all_df_dir, train[0]), index_col=0)
    for single_df_file in train[1:]:
        single_df = pandas.read_csv(os.path.join(all_df_dir, single_df_file), index_col=0)
        train_df = train_df.append(single_df)

    # retrieve test set
    test_from_i = all_df_file_names.index(dataset_releases.test_set_from + ".csv")
    test_to_i = all_df_file_names.index(dataset_releases.test_set_to + ".csv")
    test = all_df_file_names[test_from_i:test_to_i + 1]
    print("Test set: ")
    print(test)
    test_df = pandas.read_csv(os.path.join(all_df_dir, test[0]), index_col=0)
    for single_df_file in test[1:]:
        single_df = pandas.read_csv(os.path.join(all_df_dir, single_df_file), index_col=0)
        test_df = test_df.append(single_df)

    # data preparation
    train_df.IsVulnerable.replace(('yes', 'no'), (1, 0), inplace=True)
    train_df.dropna(inplace=True)
    test_df.IsVulnerable.replace(('yes', 'no'), (1, 0), inplace=True)
    test_df.dropna(inplace=True)

    if approach == "metrics":
        # datasets ready to use
        X_train = train_df.iloc[:, 0:13].values
        y_train = train_df.iloc[:, 13].values
        X_test = test_df.iloc[:, 0:13].values
        y_test = test_df.iloc[:, 13].values
    else:  # BAG OF WORDS
        print("Working on training set...")
        y_train = train_df.iloc[:, 1].values
        train_tokens_text = train_df.iloc[:, 0].values
        train_tokens_text = clean(train_tokens_text)
        vocabulary = build_vocabulary(train_tokens_text)
        X_train = build_frequency_vectors(train_tokens_text, vocabulary)
        print("Working on test set...")
        y_test = test_df.iloc[:, 1].values
        test_tokens_text = test_df.iloc[:, 0].values
        test_tokens_text = clean(test_tokens_text)
        X_test = build_frequency_vectors(test_tokens_text, vocabulary)
    return X_train, y_train, X_test, y_test


def get_cross_validation_dataset(approach):
    # retrieve all dataframes
    all_df_dir = utils.get_path("my_" + approach + "_csv_phpmyadmin")
    all_df_file_names = os.listdir(all_df_dir)
    df = pandas.read_csv(os.path.join(all_df_dir, all_df_file_names[0]), index_col=0)
    for single_df_file in all_df_file_names:
        single_df = pandas.read_csv(os.path.join(all_df_dir, single_df_file), index_col=0)
        df = df.append(single_df)

    # data preparation
    df.IsVulnerable.replace(('yes', 'no'), (1, 0), inplace=True)
    df.dropna(inplace=True)

    if approach == "metrics":
        # dataset ready to use
        X = df.iloc[:, 0:13].values
        y = df.iloc[:, 13].values
    else:  # BAG OF WORDS
        y = df.iloc[:, 1].values
        tokens_text = df.iloc[:, 0].values

        print("Cleaning text tokens...")
        for i in range(len(tokens_text)):
            tokens_text[i] = clean_tokens_row(tokens_text[i])

        print("Building vocabulary...")
        start = time()
        # vocabulary also stores frequencies
        vocabulary = {}
        for row in tokens_text:
            words = row.split()
            for w in words:
                if w not in vocabulary.keys():
                    vocabulary[w] = 1
                else:
                    vocabulary[w] += 1
        stop = time()
        print("Vocabulary building time: " + str(stop - start))
        print("Vocabulary contains " + str(len(vocabulary.keys())) + " words")
        # uncomment to use only the 200 most frequent words in the vocabulary
        # most_freq = heapq.nlargest(200, vocabulary, key=vocabulary.get)

        print("Building frequency vectors...")
        start = time()
        all_frequency_vectors = []
        for row in tokens_text:
            splitted = row.split()
            single_row_frequency_vector = []
            for word in vocabulary:
                c = splitted.count(word)
                single_row_frequency_vector.append(c)
            all_frequency_vectors.append(single_row_frequency_vector)
        stop = time()
        print("Frequency vectors building time: " + str(stop - start))
        all_frequency_vectors = numpy.asarray(all_frequency_vectors)
        X = all_frequency_vectors

        #tokens_text = clean(tokens_text)
        #vocabulary = build_vocabulary(a, tokens_text, save=True)
        #X = build_frequency_vectors(a, tokens_text, vocabulary, save=True)

    return X, y


def build_vocabulary(tokens_text, save=False):
    print("Building vocabulary...")
    start = time()
    # vocabulary also stores frequencies
    vocabulary = {}
    for row in tokens_text:
        words = row.split()
        for w in words:
            if w not in vocabulary.keys():
                vocabulary[w] = 1
            else:
                vocabulary[w] += 1
    stop = time()
    print("Vocabulary building time: " + str(stop - start))
    print("Vocabulary contains " + str(len(vocabulary.keys())) + " words")
    if save:
        vocabulary_filename = "vocabulary_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
        with open(vocabulary_filename, 'w') as file:
            file.write(json.dumps(vocabulary))
        print("Vocabulary saved to file: " + vocabulary_filename)
    # uncomment to use only the 200 most frequent words in the vocabulary
    # most_freq = heapq.nlargest(200, vocabulary, key=vocabulary.get)
    return vocabulary


def build_frequency_vectors(tokens_text, vocabulary, save=False):
    print("Building frequency vectors...")
    start = time()
    all_frequency_vectors = []
    for row in tokens_text:
        splitted = row.split()
        single_row_frequency_vector = []
        for word in vocabulary:
            c = splitted.count(word)
            single_row_frequency_vector.append(c)
        all_frequency_vectors.append(single_row_frequency_vector)
    stop = time()
    print("Frequency vectors building time: " + str(stop - start))
    all_frequency_vectors = numpy.asarray(all_frequency_vectors)
    if save:
        frequency_vectors_filename = "frequency_vectors_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".csv"
        frequency_df = pandas.DataFrame(data=numpy.int_(all_frequency_vectors),
                                        index=range(len(tokens_text)), columns=vocabulary.keys())
        frequency_df.to_csv(frequency_vectors_filename)
        print("Frequency vectors saved to file: " + frequency_vectors_filename)
    return all_frequency_vectors


def clean(tokens_text):
    print("Cleaning text tokens...")
    for i in range(len(tokens_text)):
        tokens_text[i] = clean_tokens_row(tokens_text[i])
    return tokens_text


def clean_tokens_row(tokens_row):
    # only retain tokens (starting with t_)
    cleaned = " "
    splitted = tokens_row.lower().split()
    for t in splitted:
        if t.startswith("t_"):
            cleaned = cleaned + t + " "
    return cleaned




















"""

from datetime import datetime
import json
import numpy
from numpy import unique
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_validate
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import confusion_matrix, precision_score, recall_score, accuracy_score
from sklearn.metrics import f1_score, matthews_corrcoef
from statistics import mean
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import SMOTE
import os
import pandas
import utils
from experiments_classes import DefaultReplication, Log, Performance, DatasetReleases
from time import time


save_vocabulary = True
save_frequency_vectors = True


def execute_experiment(n, a, m, l, b, c, custom=True):
    utils.space()
    print("Experiment " + str(n))
    utils.space()
    print("App: " + a)
    print("Method: " + m)
    print("Labelling: " + l)
    print("Balancing: " + b)
    print("Classifier: " + c)
    utils.space()
    if l == "real":
        # get names of starting and ending release to use in each set
        dataset_releases = get_train_test_releases(a, m, custom)
        X_train, y_train, X_test, y_test = get_real_labelling_dataset(a, m, dataset_releases)
        X_train, y_train = balance(X_train, y_train, b)
        performance = experiment_real(c, X_train, y_train, X_test, y_test)
    else:  # cross validation
        dataset_releases = DatasetReleases.perfect()
        X, y = get_cross_validation_dataset(a, m)
        X, y = balance(X, y, b)
        performance = experiment_perfect(c, X, y)
    utils.space()
    print_performance(performance)
    utils.space()
    log = Log.build(a, m, l, b, c, dataset_releases, performance)
    return log


def print_performance(performance):
    print("Performance Summary:")
    print("Fit time: " + str(performance.fit_time) + " sec")
    print("Precision: " + str(performance.precision))
    print("Recall: " + str(performance.recall))
    print("Accuracy: " + str(performance.accuracy))
    print("Inspection rate: " + str(performance.inspection_rate))
    print("F1-score: " + str(performance.f1_score))
    print("MCC: " + str(performance.mcc))


def my_scorer(classifier, X, y):
    y_pred = classifier.predict(X)
    cm = confusion_matrix(y, y_pred)
    tn = cm[0, 0]
    fp = cm[0, 1]
    fn = cm[1, 0]
    tp = cm[1, 1]
    inspection_rate = (tp + fp) / (tp + tn + fp + fn)
    precision = precision_score(y, y_pred)
    recall = recall_score(y, y_pred)
    accuracy = accuracy_score(y, y_pred)
    f1 = f1_score(y, y_pred)
    mcc = matthews_corrcoef(y, y_pred)
    return {"my_precision": precision, "my_recall": recall, "my_accuracy": accuracy,
            "my_inspection_rate": inspection_rate, "my_f1_score": f1, "my_mcc": mcc}


def balance(X, y, b):
    print_class_distribution(y)
    if b == "undersampling":
        print("Performing undersampling...")
        # define undersample strategy: the majority class will be undersampled to match the minority
        undersample = RandomUnderSampler(sampling_strategy='majority')
        X, y = undersample.fit_resample(X, y)
        print_class_distribution(y)
        return X, y
    elif b == "oversampling":
        print("Performing oversampling...")
        # define oversample strategy: Synthetic Minority Oversampling Technique
        # the minority class will be oversampled to match the majority
        oversample = SMOTE()
        X, y = oversample.fit_resample(X, y)
        print_class_distribution(y)
        return X, y
    else:
        print("No data balancing technique applied.")
        return X, y


def experiment_perfect(c, X, y):
    if c == "random_forest":
        classifier = RandomForestClassifier()
    elif c == "logistic_regression":
        classifier = LogisticRegression(max_iter=10000)
    elif c == "naive_bayes":
        classifier = GaussianNB()
    else:
        classifier = RandomForestClassifier()
    print("Starting experiment")
    print("3-fold cross validation...")
    score = cross_validate(classifier, X, y, cv=3, scoring=my_scorer)
    print("Done.")
    performance = Performance(fit_time=mean(score["fit_time"]), precision=mean(score["test_my_precision"]),
                              recall=mean(score["test_my_recall"]), accuracy=mean(score["test_my_accuracy"]),
                              inspection_rate=mean(score["test_my_inspection_rate"]),
                              f1_score=mean(score["test_my_f1_score"]), mcc=mean(score["test_my_mcc"]))
    return performance


def experiment_real(c, X_train, y_train, X_test, y_test):
    if c == "random_forest":
        classifier = RandomForestClassifier()
    elif c == "logistic_regression":
        classifier = LogisticRegression(max_iter=10000)
    elif c == "naive_bayes":
        classifier = GaussianNB()
    else:
        classifier = RandomForestClassifier()
    print("Starting experiment")
    print("Training...")
    start = time()
    classifier.fit(X_train, y_train)
    stop = time()
    print("Testing...")
    score = my_scorer(classifier, X_test, y_test)
    print("Done.")
    performance = Performance(fit_time=stop-start, precision=score["my_precision"],
                              recall=score["my_recall"], accuracy=score["my_accuracy"],
                              inspection_rate=score["my_inspection_rate"],
                              f1_score=score["my_f1_score"], mcc=score["my_mcc"])
    return performance


def print_class_distribution(y):
    print("Dataset Summary: (0 is neutral, 1 is vulnerable)")
    classes = unique(y)
    total = len(y)
    for c in classes:
        n_examples = len(y[y == c])
        percent = n_examples / total * 100
        print('Class %d: %d/%d (%.1f%%)' % (c, n_examples, total, percent))


def get_train_test_releases(a, m, custom):
    if custom:
        all_df_dir = utils.get_path("my_" + m + "_csv_" + a)
        all_df_file_names = os.listdir(all_df_dir)
        num_files = len(all_df_file_names)
        to_choose = ["Training set starting release", "Training set ending release", "Test set starting release",
                     "Test set ending release"]
        chosen = []
        start_list_from = 0
        for x in range(4):
            print("Please choose " + to_choose[x])
            for i in range(num_files):
                if i >= start_list_from:
                    print(str(i) + ": " + all_df_file_names[i][:-4])
            loop = True
            while loop:
                selection = input("Selection: ")
                if selection.isnumeric():
                    chosen.append(all_df_file_names[int(selection)][:-4])
                    print(chosen[x])
                    utils.space()
                    start_list_from = int(selection) + 1
                    loop = False
                else:
                    print("Invalid selection!")
        dataset_releases = DatasetReleases(training_set_from=chosen[0], training_set_to=chosen[1],
                                           test_set_from=chosen[2], test_set_to=chosen[3])
    else:
        dataset_releases = DatasetReleases(training_set_from=DefaultReplication.__getitem__(a + "_" + m + "_training_from").value,
                                           training_set_to=DefaultReplication.__getitem__(a + "_" + m + "_training_to").value,
                                           test_set_from=DefaultReplication.__getitem__(a + "_" + m + "_test_from").value,
                                           test_set_to=DefaultReplication.__getitem__(a + "_" + m + "_test_to").value)
    return dataset_releases


def get_real_labelling_dataset(a, m, dataset_releases):
    all_df_dir = utils.get_path("my_" + m + "_csv_" + a)
    all_df_file_names = os.listdir(all_df_dir)

    # retrieve training set
    train_from_i = all_df_file_names.index(dataset_releases.training_set_from + ".csv")
    train_to_i = all_df_file_names.index(dataset_releases.training_set_to + ".csv")
    train = all_df_file_names[train_from_i:train_to_i+1]
    print("Training set: ")
    print(train)
    train_df = pandas.read_csv(os.path.join(all_df_dir, train[0]), index_col=0)
    for single_df_file in train[1:]:
        single_df = pandas.read_csv(os.path.join(all_df_dir, single_df_file), index_col=0)
        train_df = train_df.append(single_df)

    # retrieve test set
    test_from_i = all_df_file_names.index(dataset_releases.test_set_from + ".csv")
    test_to_i = all_df_file_names.index(dataset_releases.test_set_to + ".csv")
    test = all_df_file_names[test_from_i:test_to_i + 1]
    print("Test set: ")
    print(test)
    test_df = pandas.read_csv(os.path.join(all_df_dir, test[0]), index_col=0)
    for single_df_file in test[1:]:
        single_df = pandas.read_csv(os.path.join(all_df_dir, single_df_file), index_col=0)
        test_df = test_df.append(single_df)

    # data preparation
    train_df.IsVulnerable.replace(('yes', 'no'), (1, 0), inplace=True)
    train_df.dropna(inplace=True)
    test_df.IsVulnerable.replace(('yes', 'no'), (1, 0), inplace=True)
    test_df.dropna(inplace=True)

    if m == "filemetrics":
        # datasets ready to use
        X_train = train_df.iloc[:, 0:13].values
        y_train = train_df.iloc[:, 13].values
        X_test = test_df.iloc[:, 0:13].values
        y_test = test_df.iloc[:, 13].values
    else:  # BAG OF WORDS
        print("Working on training set...")
        y_train = train_df.iloc[:, 1].values
        train_tokens_text = train_df.iloc[:, 0].values
        train_tokens_text = clean(train_tokens_text)
        vocabulary = build_vocabulary(a, train_tokens_text)
        X_train = build_frequency_vectors(a, train_tokens_text, vocabulary)
        print("Working on test set...")
        y_test = test_df.iloc[:, 1].values
        test_tokens_text = test_df.iloc[:, 0].values
        test_tokens_text = clean(test_tokens_text)
        X_test = build_frequency_vectors(a, test_tokens_text, vocabulary)

    return X_train, y_train, X_test, y_test


def get_cross_validation_dataset(a, m):
    # retrieve all dataframes
    all_df_dir = utils.get_path("my_" + m + "_csv_" + a)
    all_df_file_names = os.listdir(all_df_dir)
    df = pandas.read_csv(os.path.join(all_df_dir, all_df_file_names[0]), index_col=0)
    for single_df_file in all_df_file_names:
        single_df = pandas.read_csv(os.path.join(all_df_dir, single_df_file), index_col=0)
        df = df.append(single_df)

    # data preparation
    df.IsVulnerable.replace(('yes', 'no'), (1, 0), inplace=True)
    df.dropna(inplace=True)

    if m == "filemetrics":
        # dataset ready to use
        X = df.iloc[:, 0:13].values
        y = df.iloc[:, 13].values
    else:  # BAG OF WORDS
        y = df.iloc[:, 1].values
        tokens_text = df.iloc[:, 0].values

        print("Cleaning text tokens...")
        for i in range(len(tokens_text)):
            tokens_text[i] = clean_tokens_row(tokens_text[i])

        print("Building vocabulary...")
        start = time()
        # vocabulary also stores frequencies
        vocabulary = {}
        for row in tokens_text:
            words = row.split()
            for w in words:
                if w not in vocabulary.keys():
                    vocabulary[w] = 1
                else:
                    vocabulary[w] += 1
        stop = time()
        print("Vocabulary building time: " + str(stop - start))
        print("Vocabulary contains " + str(len(vocabulary.keys())) + " words")
        if save_vocabulary:
            vocabulary_filename = "vocabulary_" + a + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
            with open(vocabulary_filename, 'w') as file:
                file.write(json.dumps(vocabulary))
            print("Vocabulary saved to file: " + vocabulary_filename)
        # uncomment to use only the 200 most frequent words in the vocabulary
        # most_freq = heapq.nlargest(200, vocabulary, key=vocabulary.get)

        print("Building frequency vectors...")
        start = time()
        all_frequency_vectors = []
        for row in tokens_text:
            splitted = row.split()
            single_row_frequency_vector = []
            for word in vocabulary:
                c = splitted.count(word)
                single_row_frequency_vector.append(c)
            all_frequency_vectors.append(single_row_frequency_vector)
        stop = time()
        print("Frequency vectors building time: " + str(stop - start))
        all_frequency_vectors = numpy.asarray(all_frequency_vectors)
        if save_frequency_vectors:
            frequency_vectors_filename = "frequency_vectors_" + a + "_" + datetime.now().strftime(
                "%Y%m%d%H%M%S") + ".csv"
            frequency_df = pandas.DataFrame(data=numpy.int_(all_frequency_vectors),
                                            index=range(len(tokens_text)), columns=vocabulary.keys())
            frequency_df.to_csv(frequency_vectors_filename)
            print("Frequency vectors saved to file: " + frequency_vectors_filename)
        X = all_frequency_vectors

        #tokens_text = clean(tokens_text)
        #vocabulary = build_vocabulary(a, tokens_text, save=True)
        #X = build_frequency_vectors(a, tokens_text, vocabulary, save=True)

    return X, y


def build_vocabulary(a, tokens_text, save=False):
    print("Building vocabulary...")
    start = time()
    # vocabulary also stores frequencies
    vocabulary = {}
    for row in tokens_text:
        words = row.split()
        for w in words:
            if w not in vocabulary.keys():
                vocabulary[w] = 1
            else:
                vocabulary[w] += 1
    stop = time()
    print("Vocabulary building time: " + str(stop - start))
    print("Vocabulary contains " + str(len(vocabulary.keys())) + " words")
    if save:
        vocabulary_filename = "vocabulary_" + a + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
        with open(vocabulary_filename, 'w') as file:
            file.write(json.dumps(vocabulary))
        print("Vocabulary saved to file: " + vocabulary_filename)
    # uncomment to use only the 200 most frequent words in the vocabulary
    # most_freq = heapq.nlargest(200, vocabulary, key=vocabulary.get)
    return vocabulary


def build_frequency_vectors(a, tokens_text, vocabulary, save=False):
    print("Building frequency vectors...")
    start = time()
    all_frequency_vectors = []
    for row in tokens_text:
        splitted = row.split()
        single_row_frequency_vector = []
        for word in vocabulary:
            c = splitted.count(word)
            single_row_frequency_vector.append(c)
        all_frequency_vectors.append(single_row_frequency_vector)
    stop = time()
    print("Frequency vectors building time: " + str(stop - start))
    all_frequency_vectors = numpy.asarray(all_frequency_vectors)
    if save:
        frequency_vectors_filename = "frequency_vectors_" + a + "_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".csv"
        frequency_df = pandas.DataFrame(data=numpy.int_(all_frequency_vectors),
                                        index=range(len(tokens_text)), columns=vocabulary.keys())
        frequency_df.to_csv(frequency_vectors_filename)
        print("Frequency vectors saved to file: " + frequency_vectors_filename)
    return all_frequency_vectors


def clean(tokens_text):
    print("Cleaning text tokens...")
    for i in range(len(tokens_text)):
        tokens_text[i] = clean_tokens_row(tokens_text[i])
    return tokens_text


def clean_tokens_row(tokens_row):
    # only retain tokens (starting with t_)
    cleaned = " "
    splitted = tokens_row.lower().split()
    for t in splitted:
        if t.startswith("t_"):
            cleaned = cleaned + t + " "
    return cleaned


"""
