#!/usr/bin/env python
# coding: utf-8
import optuna
from xgboost import XGBRegressor

def tune_hyperparameters(train_func, X, y, n_trials=100, n_splits=5):
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 2, 1000),
            'max_depth': trial.suggest_int('max_depth', 1, 15),
            'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.3),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'alpha': trial.suggest_float("alpha", 1e-5, 10, log=True),  
            'gamma': trial.suggest_float("gamma", 1e-5, 5, log=True),
            'lambda': trial.suggest_float('lambda', 1e-5, 10.0, log=True),
            'early_stopping_rounds': 50
        }

        model = XGBRegressor(**params)
        mae_train_avg, mae_test_avg = train_func(model, X, y, n_splits)
        return mae_test_avg

    study = optuna.create_study(direction='minimize')

    # Optimize the study, the objective function is passed in as the first argument
    study.optimize(objective, n_trials=n_trials)

    # Results
    print('Number of finished trials: ', len(study.trials))
    print('Best trial:')
    trial = study.best_trial
    
    print('Value: ', trial.value)
    print('Params: ')
    for key, value in trial.params.items():
        print(f'    {key}: {value}')
    
    return trial.params