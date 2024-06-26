from src.automl import AutoML
import pandas as pd
import os
import json
import torch
import argparse


def forward(mode, train_path, test_path, config_path, output_folder, model_path, params_file_path):

    """
    Train or test an AutoML model on the specified dataset.

    This function initializes an AutoML object and either trains or tests a model based on the specified mode.
    If the mode is 'train', the function trains a model on the provided training dataset, saves the model to the output folder,
    and saves the model parameters to an Excel file.
    If the mode is 'test_params' or 'test_model', the function loads the parameters or trained model and parameters
    from the specified output folder and tests the model on the test dataset.

    Args:
        mode (str): The mode of operation: 'train', 'test_params', or 'test_model'.
        train_path (str): The path to the training data file.
        test_path (str): The path to the testing data file.
        config_path (str): The path to the configuration file containing parameters for AutoML.
        output_folder (str): The folder where the model and parameters are saved (for 'train' mode) or loaded (for 'test_params' or 'test_model' mode).
        model_path (str): The path to the trained model file (used in 'test_model' mode).
        params_file_path (str, optional): The path to the file containing the model parameters. If not specified, it will be automatically generated and saved in the `output_folder`.

    Returns:
        float: The evaluation metric (e.g., accuracy) of the trained or tested model.
    """

    with open(config_path, 'r') as file:
        config = json.load(file)

    automl = AutoML(train_path, test_path, **config)
    
    if mode == 'train':
        model, params, metric = automl.forward()
        if params_file_path is None:
            params_file_path = os.path.join(output_folder, str(metric)) + '.xlsx'
        
        torch.save(model.state_dict(), os.path.join(output_folder, 'TSCT_model.pt'))
        pd.Series(params).to_excel(params_file_path)
    
    params = pd.read_excel(params_file_path, index_col=0).to_dict()[0]
    for param, value in params.items():
        if param not in ['lr', 'dropout_ff', 'fourie_mode', 'embedding_mode', 'max_seq_len']:
            params[param] = int(value)
    
    if mode == 'test_model':
        metric = automl.test_model(model_path, **params)
        return metric
    
    metric = automl.test_params(**params)
    return metric

def parse_arguments():

    parser = argparse.ArgumentParser(description='Process some parameters.')
    parser.add_argument('--mode', type=str, help='Mode', choices=['train', 'test_params', 'test_model'], required=True)
    parser.add_argument('--output_folder', type=str, help='Output folder', required=True)
    parser.add_argument('--model_path', type=str, default=None, help='Path to the model')
    parser.add_argument('--params_file_path', type=str, default=None, help='Path to the parameters file')
    parser.add_argument('--config_path', type=str, help='Path to the configuration file', required=True)
    parser.add_argument('--train_path', type=str, help='Train path')
    parser.add_argument('--test_path', type=str, help='Test path', required=True)

    args = parser.parse_args()

    if args.mode == 'train':
        if args.train_path is None:
            parser.error("--train_path is required when mode is 'train'")
    if args.mode == 'test_params':
        if args.params_file_path is None:
            parser.error("--params_file_path is required when mode is 'test_params'")
    if args.mode == 'test_model':
        if args.params_file_path is None:
            parser.error("--params_file_path is required when mode is 'test_model'")
        if args.model_path is None:
            parser.error("--model_path is required when mode is 'model_path'")
    
    return args


if __name__ == '__main__':

    args = parse_arguments()

    mode = args.mode
    output_folder = args.output_folder
    model_path = args.model_path
    params_file_path = args.params_file_path
    config_path = args.config_path
    train_path = args.train_path
    test_path = args.test_path

    metric = forward(mode, train_path, test_path, config_path, output_folder, model_path, params_file_path)

    print(metric)