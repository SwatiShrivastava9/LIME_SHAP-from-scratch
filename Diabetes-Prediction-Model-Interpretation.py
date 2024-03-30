# -*- coding: utf-8 -*-
"""DAI Assignment 1-Task 1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1jlD5Ph5bs3_1INgzxUtyVLX74EzGiaXz
"""

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LinearRegression

# Load the dataset
from google.colab import drive

drive.mount('/content/drive')

file_path = '/content/drive/My Drive/DAI_Assign1/diabetes.csv'
#column_names = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age", "Outcome"]

df = pd.read_csv(file_path)

# Split the data into features (X) and target variable (y)
X = df.drop('Outcome', axis=1).values
y = df['Outcome'].values

df.head()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

rf_classifier = RandomForestClassifier(n_estimators=20,random_state=42)
rf_classifier.fit(X_train, y_train)

from sklearn.metrics import accuracy_score, f1_score

predictions = rf_classifier.predict(X_test)
#Evaluation
accuracy = accuracy_score(y_test, predictions)
f1 = f1_score(y_test, predictions, average='binary')

print(f"Accuracy: {accuracy}")
print(f"F1 Score: {f1}")

"""# **SHAP**"""

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from itertools import combinations


feature_means = X_train.mean(axis=0)


from itertools import combinations
import numpy as np

def generate_subsets(n_features):
    return [set(combo) for i in range(n_features + 1) for combo in combinations(range(n_features), i)]

def model_predict_subset(model, instance, subset_indices, feature_means):
    modified_instance = np.array([feature_means[i] if i not in subset_indices else instance[i] for i in range(len(instance))])
    return model.predict_proba(modified_instance.reshape(1, -1))[0]

def calculate_marginal_contributions(model, instance, feature_index, feature_means):
    subsets = generate_subsets(len(instance))
    marginal_contributions = []
    for subset in subsets:
        if feature_index in subset:
            continue
        with_feature = subset | {feature_index}
        without_feature = subset
        with_feature_value = model_predict_subset(model, instance, with_feature, feature_means).max()
        without_feature_value = model_predict_subset(model, instance, without_feature, feature_means).max()
        marginal_contributions.append(with_feature_value - without_feature_value)
    return marginal_contributions

def compute_shapley_values(model, instance, feature_means):
    shapley_values = []
    for i in range(len(instance)):
        marginal_contributions = calculate_marginal_contributions(model, instance, i, feature_means)
        shapley_value = sum(marginal_contributions) / len(marginal_contributions)
        shapley_values.append(shapley_value)
    return shapley_values


def compute_shapley_values_for_dataset(model, dataset, feature_means):
    all_shapley_values = []
    for instance in dataset:
        shapley_values = compute_shapley_values(model, instance, feature_means)
        all_shapley_values.append(shapley_values)
    return np.array(all_shapley_values)

column_names = df.drop('Outcome', axis=1).columns.tolist()

test_instance = X_test[0]
shapley_values = compute_shapley_values(rf_classifier, test_instance, feature_means)
print("Shapley values for the selected instance:", shapley_values)

print("Feature Importances from SHAP for a single Instance:")
for feature_name, shap_value in zip(column_names, shapley_values):
    print(f"{feature_name}: {shap_value:.4f}")

# Compute for whole dataset
all_shapley_values = compute_shapley_values_for_dataset(rf_classifier, X_test, feature_means)

average_shapley_values = np.mean(all_shapley_values, axis=0)
print("Average Shapley values for all features:", average_shapley_values)

print("Feature Importances from SHAP Explanation:")
for feature_name, shap_value in zip(column_names, average_shapley_values):
    print(f"{feature_name}: {shap_value:.4f}")

"""Plot graphs"""

import matplotlib.pyplot as plt
import numpy as np

def plot_feature_importance_bar_graph(shapley_values, feature_names):
    """
    Plots a bar graph of feature importance based on Shapley values.

    Parameters:
    - shapley_values: List or array of Shapley values for a single instance.
    - feature_names: List of feature names in the same order as the Shapley values.
    """
    shapley_values = np.array(shapley_values)
    feature_names = np.array(feature_names)

    sorted_indices = np.argsort(np.abs(shapley_values))[::-1]
    sorted_shapley_values = shapley_values[sorted_indices]
    sorted_feature_names = feature_names[sorted_indices]

    plt.figure(figsize=(10, 6))
    plt.barh(sorted_feature_names, sorted_shapley_values, color='skyblue')
    plt.xlabel('SHAP Value')
    plt.ylabel('Features')
    plt.title('Feature Importance for the Selected Instance')
    plt.gca().invert_yaxis()
    plt.show()

shapley_values_example = [0.0047, 0.189, -0.0437, -0.0047, -0.0719, -0.0328, -0.0016, -0.039]
feature_names_example = ['Feature 1', 'Feature 2', 'Feature 3', 'Feature 4', 'Feature 5', 'Feature 6', 'Feature 7', 'Feature 8']

plot_feature_importance_bar_graph(shapley_values, column_names)

plot_feature_importance_bar_graph(average_shapley_values, column_names)

"""# **LIME**"""

from sklearn.linear_model import LinearRegression
from sklearn.metrics.pairwise import euclidean_distances

def perturb_instance(instance, num_samples=1000, std_dev=0.5):
    perturbed_instances = np.random.normal(loc=instance, scale=std_dev, size=(num_samples, instance.shape[0]))
    return perturbed_instances

selected_instance = X_test[0]


# Function to compute LIME values for a single instance
def compute_lime_values(instance, model, num_perturbations=1000, std_dev=0.5):

    perturbed_instances = perturb_instance(instance, num_samples=num_perturbations, std_dev=std_dev)
    perturbed_instances_df = pd.DataFrame(perturbed_instances, columns=column_names)
    original_prediction = rf_classifier.predict([selected_instance])[0]
    perturbed_predictions = model.predict(perturbed_instances_df)

    kernel_width = 0.25 * perturbed_instances.shape[1]**0.5
    distances = euclidean_distances([instance], perturbed_instances)[0]
    weights = np.exp(-(distances**2) / kernel_width**2)

    local_model = LinearRegression()
    local_model.fit(perturbed_instances, perturbed_predictions, sample_weight=weights)
    feature_importances = local_model.coef_
    return feature_importances

# Function to compute LIME values for entire test data
def compute_lime_values_test_data(test_data, model, num_perturbations=1000, std_dev=0.5):
    lime_values = []
    for instance in test_data:
        lime_values.append(compute_lime_values(instance, model, num_perturbations, std_dev))
    return np.mean(lime_values, axis=0)

# Calculate LIME values for a single instance
single_instance = X_test[0]
lime_values_single_instance = compute_lime_values(single_instance, rf_classifier)

print("Feature Importances from LIME Explanation for Single Instance:")
for feature, importance in zip(column_names, lime_values_single_instance):
    print(f"{feature}: {importance:.4f}")

# Calculate LIME values for entire test data
lime_values_test_data = compute_lime_values_test_data(X_test, rf_classifier)

# Print LIME values for each feature
print("\nFeature Importances from LIME Explanation for Entire Test Data:")
for feature, importance in zip(column_names, lime_values_test_data):
    print(f"{feature}: {importance:.4f}")

"""**Visualization**"""

import matplotlib.pyplot as plt
import numpy as np

def plot_lime_values(lime_values, feature_names):
    """
    Plots the LIME values for a single instance as a bar graph.

    Parameters:
    - lime_values: An array-like object containing the LIME values for each feature.
    - feature_names: A list of strings representing the names of the features.
    """
    sorted_idx = np.argsort(lime_values)
    sorted_importances = lime_values[sorted_idx]
    sorted_features = [feature_names[i] for i in sorted_idx]

    plt.figure(figsize=(10, 6))
    plt.barh(range(len(sorted_features)), sorted_importances, align='center', color='skyblue')
    plt.yticks(range(len(sorted_features)), sorted_features)
    plt.xlabel('Feature Importance')
    plt.title('Feature Importances as Determined by LIME for a Single Instance')
    plt.grid(axis='x')
    plt.show()

plot_lime_values(lime_values_single_instance, column_names)

plot_lime_values(lime_values_test_data, column_names)