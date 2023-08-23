#!/usr/bin/env python
# coding: utf-8
import optuna
from xgboost import XGBRegressor

def tune_hyperparameters(config, train_func, X, y, n_trials=100, n_splits=5):
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int(
                'n_estimators', 
                *config.hyperparameters.sample_space.n_estimators,
            ),

            'max_depth': trial.suggest_int(
                'max_depth', 
                *config.hyperparameters.sample_space.max_depth
            ),

            'learning_rate': trial.suggest_float(
                'learning_rate', 
                *config.hyperparameters.sample_space.learning_rate
            ),

            'subsample': trial.suggest_float(
                'subsample', *config.hyperparameters.sample_space.subsample
            ),

            'colsample_bytree': trial.suggest_float(
                'colsample_bytree', 
                *config.hyperparameters.sample_space.colsample_bytree
            ),

            'min_child_weight': trial.suggest_int(
                'min_child_weight', 
                *config.hyperparameters.sample_space.min_child_weight
            ),

            'alpha': trial.suggest_float(
                "alpha", 
                *config.hyperparameters.sample_space.alpha, 
                log=True
            ),

            'gamma': trial.suggest_float(
                "gamma", 
                *config.hyperparameters.sample_space.gamma, 
                log=True
            ),

            'lambda': trial.suggest_float(
                'lambda', 
                *config.hyperparameters.sample_space.lambda_val, 
                log=True
            ),

            'early_stopping_rounds': 
                config.hyperparameters.sample_space.EARLY_STOPPING_ROUNDS
    }

        model = XGBRegressor(**params)
        mae_train_avg, mae_test_avg = train_func(
            config=config, 
            model=model, 
            X=X, y=y, 
            n_splits=config.training.N_SPLITS)
        return mae_test_avg

    sampler = optuna.samplers.TPESampler(config.hyperparameters.SEED)
    study = optuna.create_study(direction='minimize', sampler=sampler)

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