# The Impact of Release-based Training on Software Vulnerability Prediction Models
Giulia Sellitto and Filomena Ferrucci \
University of Salerno, Italy \
April 2021 

[Extended Abstract](https://github.com/giuliasellitto7/womencourage2021/blob/main/extended%20abstract.pdf) and [Poster](https://github.com/giuliasellitto7/womencourage2021/blob/main/poster.pdf) accepted at [womENcourage 2021](https://womencourage.acm.org/2021/)

___

Software vulnerability prediction models have been an object of study for several years. The ability to predict which portions of code are more prone to contain vulnerabilities leads to focus testing efforts, potentially increasing code quality and reducing security threats [[2]](https://doi.org/10.1109/ISSRE.2014.32). Most of the proposed models have been evaluated with cross-validation, which consists in splitting the dataset in k equal-sized folds and computing the average performance obtained in k rounds of validation, in such a way that each fold is part of the training set k - 1 times and composes the test set once. However, in a real-case scenario, one is interested in training the model by using information related to prior releases of software, and obtaining predictions on the current version to be released. So there is a gap between the performance observed in research studies and those that would be obtained in a real environment. We want to start working to bridge this gap, by following the indications given by Jimenez et al. [[1]](https://doi.org/10.1145/3338906.3338941). To ensure robust scientific findings, they solicited the community to employ the experimental and empirical methodology they proposed, which takes into account the time constraints of the real-world context. Seizing this suggestion, we start taking small steps in this direction, by performing a preliminary study on Walden et al.’s dataset [[3]](https://seam.cs.umd.edu/webvuldata/). We aim to analyze how differently vulnerability prediction models would perform if evaluated with
a release-based approach rather than with cross-validation. We hence formulate the following research questions:

>**RQ1**: *What is the performance of vulnerability prediction models trained using a release-based approach when compared to models trained using cross-validation?*

>**RQ2**: *Which modelling approach is more sensitive to the use of a different validation method?*

We perform our research by taking as a baseline the Walden et al.'s work [[2]](https://doi.org/10.1109/ISSRE.2014.32), in which the authors compared the performance of the Random Forest classifier when training using two different sets of features: one based on code metrics and the other based on textual tokens. We first replicate the original study by Walden et al., by performing 3-fold cross-validation to evaluate the models' performance. Afterwards, we apply a release-based training approach to analyze the differences in the performance. Our release-based training approach consists in training the model on files from prior releases and testing it on later releases. In this preliminary study, we only use the vulnerability data of PHPMyAdmin contained in the Walden et al.s' dataset [[3]](https://seam.cs.umd.edu/webvuldata/). 


### Replication
To replicate our study, you will need Python 3. \
Download this repository and run *execute\_custom\_experiments*. You will be asked to choose experiments settings, i.e., if you want to work with software metrics or text tokens, by applying cross-validation or a release-based approach. In the latter, you will also be asked to choose which releases to use in training and testing phases, respectively. A new file *experiments.csv* will be created to store the results of the experiments.
