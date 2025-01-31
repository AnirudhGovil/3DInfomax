import argparse
from ast import Not
from asyncio.windows_events import NULL
import concurrent.futures
import copy
import os
import re
import dgl
import numpy as np
import random
import torch

from icecream import install
from ogb.lsc import DglPCQM4MDataset, PCQM4MEvaluator
from ogb.utils import smiles2graph

from commons.utils import seed_all, get_random_indices, TENSORBOARD_FUNCTIONS, move_to_device
from datasets.ZINC_dataset import ZINCDataset
from datasets.bace_geomol_feat import BACEGeomol
from datasets.bace_geomol_featurization_of_qm9 import BACEGeomolQM9Featurization
from datasets.bace_geomol_random_split import BACEGeomolRandom
from datasets.bbbp_geomol_feat import BBBPGeomol
from datasets.bbbp_geomol_featurization_of_qm9 import BBBPGeomolQM9Featurization
from datasets.bbbp_geomol_random_split import BBBPGeomolRandom
from datasets.esol_geomol_feat import ESOLGeomol
from datasets.esol_geomol_featurization_of_qm9 import ESOLGeomolQM9Featurization
from datasets.file_loader_drugs import FileLoaderDrugs
from datasets.file_loader_qm9 import FileLoaderQM9
from datasets.geom_drugs_dataset import GEOMDrugs
from datasets.geom_qm9_dataset import GEOMqm9
from datasets.geomol_geom_qm9_dataset import QM9GeomolFeatDataset
from datasets.inference_dataset import InferenceDataset
from datasets.lipo_geomol_feat import LIPOGeomol
from datasets.lipo_geomol_featurization_of_qm9 import LIPOGeomolQM9Featurization
from datasets.ogbg_dataset_extension import OGBGDatasetExtension
from datasets.qm9_dataset_geomol_conformers import QM9DatasetGeomolConformers
from datasets.qm9_dataset_rdkit_conformers import QM9DatasetRDKITConformers

from datasets.qm9_geomol_featurization import QM9GeomolFeaturization
from datasets.qmugs_dataset import QMugsDataset
from models.geomol_mpnn import GeomolGNNWrapper
from train import load_model
from trainer.byol_trainer import BYOLTrainer
from trainer.byol_wrapper import BYOLwrapper

import seaborn

from trainer.graphcl_trainer import GraphCLTrainer
from trainer.optimal_transport_trainer import OptimalTransportTrainer
from trainer.philosophy_trainer import PhilosophyTrainer
from trainer.self_supervised_ae_trainer import SelfSupervisedAETrainer

from trainer.self_supervised_alternating_trainer import SelfSupervisedAlternatingTrainer

from trainer.self_supervised_trainer import SelfSupervisedTrainer

import yaml
from datasets.custom_collate import *  # do not remove
from models import *  # do not remove
from torch.nn import *  # do not remove
from torch.optim import *  # do not remove
from commons.losses import *  # do not remove
from torch.optim.lr_scheduler import *  # do not remove
from datasets.samplers import *  # do not remove

from datasets.qm9_dataset import QM9Dataset
from torch.utils.data import DataLoader, Subset

from trainer.metrics import QM9DenormalizedL1, QM9DenormalizedL2, \
    QM9SingleTargetDenormalizedL1, Rsquared, NegativeSimilarity, MeanPredictorLoss, \
    PositiveSimilarity, ContrastiveAccuracy, TrueNegativeRate, TruePositiveRate, Alignment, Uniformity, \
    BatchVariance, DimensionCovariance, MAE, PositiveSimilarityMultiplePositivesSeparate2d, \
    NegativeSimilarityMultiplePositivesSeparate2d, OGBEvaluator, PearsonR, PositiveProb, NegativeProb, \
    Conformer2DVariance, Conformer3DVariance, PCQM4MEvaluatorWrapper
from trainer.trainer import Trainer

# turn on for debugging C code like Segmentation Faults
import faulthandler
faulthandler.enable()
install()
seaborn.set_theme()

import argparse
import concurrent.futures
import copy
import os
import re


from icecream import install
from ogb.lsc import DglPCQM4MDataset
from ogb.lsc import PCQM4MEvaluator
from ogb.utils import smiles2graph

from commons.utils import seed_all, get_random_indices, TENSORBOARD_FUNCTIONS
from datasets.ZINC_dataset import ZINCDataset
from datasets.bace_geomol_feat import BACEGeomol
from datasets.bace_geomol_featurization_of_qm9 import BACEGeomolQM9Featurization
from datasets.bace_geomol_random_split import BACEGeomolRandom
from datasets.bbbp_geomol_feat import BBBPGeomol
from datasets.bbbp_geomol_featurization_of_qm9 import BBBPGeomolQM9Featurization
from datasets.bbbp_geomol_random_split import BBBPGeomolRandom
from datasets.esol_geomol_feat import ESOLGeomol
from datasets.esol_geomol_featurization_of_qm9 import ESOLGeomolQM9Featurization
from datasets.file_loader_drugs import FileLoaderDrugs
from datasets.file_loader_qm9 import FileLoaderQM9
from datasets.geom_drugs_dataset import GEOMDrugs
from datasets.geom_qm9_dataset import GEOMqm9
from datasets.geomol_geom_qm9_dataset import QM9GeomolFeatDataset
from datasets.lipo_geomol_feat import LIPOGeomol
from datasets.lipo_geomol_featurization_of_qm9 import LIPOGeomolQM9Featurization
from datasets.ogbg_dataset_extension import OGBGDatasetExtension
from datasets.qm9_dataset_geomol_conformers import QM9DatasetGeomolConformers
from datasets.qm9_dataset_rdkit_conformers import QM9DatasetRDKITConformers

from datasets.qm9_geomol_featurization import QM9GeomolFeaturization
from datasets.qmugs_dataset import QMugsDataset
from models.geomol_mpnn import GeomolGNNWrapper
from trainer.byol_trainer import BYOLTrainer
from trainer.byol_wrapper import BYOLwrapper

import seaborn

from trainer.graphcl_trainer import GraphCLTrainer
from trainer.optimal_transport_trainer import OptimalTransportTrainer
from trainer.philosophy_trainer import PhilosophyTrainer
from trainer.self_supervised_ae_trainer import SelfSupervisedAETrainer

from trainer.self_supervised_alternating_trainer import SelfSupervisedAlternatingTrainer

from trainer.self_supervised_trainer import SelfSupervisedTrainer

import yaml
from datasets.custom_collate import *  # do not remove
from models import *  # do not remove
from torch.nn import *  # do not remove
from torch.optim import *  # do not remove
from commons.losses import *  # do not remove
from torch.optim.lr_scheduler import *  # do not remove
from datasets.samplers import *  # do not remove

from datasets.qm9_dataset import QM9Dataset
from torch.utils.data import DataLoader, Subset

from trainer.metrics import QM9DenormalizedL1, QM9DenormalizedL2, \
    QM9SingleTargetDenormalizedL1, Rsquared, NegativeSimilarity, MeanPredictorLoss, \
    PositiveSimilarity, ContrastiveAccuracy, TrueNegativeRate, TruePositiveRate, Alignment, Uniformity, \
    BatchVariance, DimensionCovariance, MAE, PositiveSimilarityMultiplePositivesSeparate2d, \
    NegativeSimilarityMultiplePositivesSeparate2d, OGBEvaluator, PearsonR, PositiveProb, NegativeProb, \
    Conformer2DVariance, Conformer3DVariance, PCQM4MEvaluatorWrapper
from trainer.trainer import Trainer

# turn on for debugging C code like Segmentation Faults
import faulthandler
faulthandler.enable()
install()
seaborn.set_theme()

import pytest

from train import get_trainer,load_model,train,train_geomol,train_qm9_geomol_featurization,train_pcqm4m,train_ogbg,train_zinc,train_geom,train_qm9
from inference import inference

def parse_arguments_1():
    """Interprets the many argumneants that are provided to the model class"""
    p = argparse.ArgumentParser()
    p.add_argument(
        '--config',
        type=argparse.FileType(
            mode='r'),
        default='configs_clean\pre-train_QM9.yml')
    p.add_argument(
        '--experiment_name',
        type=str,
        help='name that will be added to the runs folder output')
    p.add_argument(
        '--logdir',
        type=str,
        default='runs',
        help='tensorboard logdirectory')
    p.add_argument('--num_epochs', type=int, default=2500,
                   help='number of times to iterate through all samples')
    p.add_argument('--batch_size', type=int, default=1024,
                   help='samples that will be processed in parallel')
    p.add_argument(
        '--patience',
        type=int,
        default=20,
        help='stop training after no improvement in this many epochs')
    p.add_argument('--minimum_epochs', type=int, default=0,
                   help='minimum numer of epochs to run')
    p.add_argument('--dataset', type=str, default='qm9',
                   help='[qm9, zinc, drugs, geom_qm9, molhiv]')
    p.add_argument('--num_train', type=int, default=-
                   1, help='n samples of the model samples to use for train')
    p.add_argument('--seed', type=int, default=123,
                   help='seed for reproducibility')
    p.add_argument(
        '--num_val',
        type=int,
        default=None,
        help='n samples of the model samples to use for validation')
    p.add_argument(
        '--multithreaded_seeds',
        type=list,
        default=[],
        help='if this is non empty, multiple threads will be started, training the same model but with the different seeds')
    p.add_argument(
        '--seed_data',
        type=int,
        default=123,
        help='if you want to use a different seed for the datasplit')
    p.add_argument('--loss_func', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--critic_loss', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--critic_loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--optimizer', type=str, default='Adam',
                   help='Class name of torch.optim like [Adam, SGD, AdamW]')
    p.add_argument(
        '--optimizer_params',
        type=dict,
        help='parameters with keywords of the chosen optimizer like lr')
    p.add_argument(
        '--lr_scheduler',
        type=str,
        help='Class name of torch.optim.lr_scheduler like [CosineAnnealingLR, ExponentialLR, LambdaLR]')
    p.add_argument(
        '--lr_scheduler_params',
        type=dict,
        help='parameters with keywords of the chosen lr_scheduler')
    p.add_argument('--scheduler_step_per_batch', default=True, type=bool,
                   help='step every batch if true step every epoch otherwise')
    p.add_argument(
        '--log_iterations',
        type=int,
        default=-
        1,
        help='log every log_iterations iterations (-1 for only logging after each epoch)')
    p.add_argument(
        '--expensive_log_iterations',
        type=int,
        default=100,
        help='frequency with which to do expensive logging operations')
    p.add_argument(
        '--eval_per_epochs',
        type=int,
        default=0,
        help='frequency with which to do run the function run_eval_per_epoch that can do some expensive calculations on the val set or sth like that. If this is zero, then the function will never be called')
    p.add_argument(
        '--linear_probing_samples',
        type=int,
        default=500,
        help='number of samples to use for linear probing in the run_eval_per_epoch function of the self supervised trainer')
    p.add_argument(
        '--num_conformers',
        type=int,
        default=3,
        help='number of conformers to use if we are using multiple conformers on the 3d side')
    p.add_argument(
        '--metrics',
        default=[],
        help='tensorboard metrics [mae, mae_denormalized, qm9_properties ...]')
    p.add_argument(
        '--main_metric',
        default='mae_denormalized',
        help='for early stopping etc.')
    p.add_argument('--main_metric_goal', type=str, default='min',
                   help='controls early stopping. [max, min]')
    p.add_argument(
        '--val_per_batch',
        type=bool,
        default=True,
        help='run evaluation every batch and then average over the eval results. When running the molhiv benchmark for example, this needs to be Fale because we need to evaluate on all val data at once since the metric is rocauc')
    p.add_argument('--tensorboard_functions', default=[],
                   help='choices of the TENSORBOARD_FUNCTIONS in utils')
    p.add_argument(
        '--checkpoint',
        type=str,
        help='path to directory that contains a checkpoint to continue training')
    p.add_argument(
        '--pretrain_checkpoint',
        type=str,
        help='Specify path to finetune from a pretrained checkpoint')
    p.add_argument(
        '--transfer_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--frozen_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--exclude_from_transfer',
        default=[],
        help='parameters that usually should not be transferred like batchnorm params')
    p.add_argument('--transferred_lr', type=float, default=None,
                   help='set to use a different LR for transfer layers')
    p.add_argument(
        '--num_epochs_local_only',
        type=int,
        default=1,
        help='when training with OptimalTransportTrainer, this specifies for how many epochs only the local predictions will get a loss')

    p.add_argument(
        '--required_data',
        default=[],
        help='what will be included in a batch like [dgl_graph, targets, dgl_graph3d]')
    p.add_argument('--collate_function', default='graph_collate',
                   help='the collate function to use for DataLoader')
    p.add_argument(
        '--collate_params',
        type=dict,
        default={},
        help='parameters with keywords of the chosen collate function')
    p.add_argument('--use_e_features', default=True, type=bool,
                   help='ignore edge features if set to False')
    p.add_argument(
        '--targets',
        default=[],
        help='properties that should be predicted')
    p.add_argument('--device', type=str, default='cuda',
                   help='What device to train on: cuda or cpu')

    p.add_argument('--dist_embedding', type=bool, default=False,
                   help='add dist embedding to complete graphs edges')
    p.add_argument(
        '--num_radial',
        type=int,
        default=6,
        help='number of frequencies for distance embedding')
    p.add_argument(
        '--models_to_save',
        type=list,
        default=[],
        help='specify after which epochs to remember the best model')

    p.add_argument('--model_type', type=str, default='MPNN',
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model_parameters',
        type=dict,
        help='dictionary of model parameters')

    p.add_argument('--model3d_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model3d_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--critic_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--critic_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--trainer', type=str, default='contrastive',
                   help='[contrastive, byol, alternating, philosophy]')
    p.add_argument('--train_sampler', type=str, default=None,
                   help='any of pytorchs samplers or a custom sampler')

    p.add_argument('--eval_on_test', type=bool, default=True,
                   help='runs evaluation on test set if true')
    p.add_argument(
        '--force_random_split',
        type=bool,
        default=False,
        help='use random split for ogb')
    p.add_argument(
        '--reuse_pre_train_data',
        type=bool,
        default=False,
        help='use all data instead of ignoring that used during pre-training')
    p.add_argument(
        '--transfer_3d',
        type=bool,
        default=False,
        help='set true to load the 3d network instead of the 2d network')
    p.add_argument(
        '--smiles_txt_path',
        type=str,
        default='dataset/inference_smiles.txt',
        help='')
    return p.parse_args()

def parse_arguments_2():
    """Interprets the many argumneants that are provided to the model class"""
    p = argparse.ArgumentParser()
    p.add_argument(
        '--config',
        type=argparse.FileType(
            mode='r'),
        default='configs_clean/fingerprint_inference.yml')
    p.add_argument(
        '--experiment_name',
        type=str,
        help='name that will be added to the runs folder output')
    p.add_argument(
        '--logdir',
        type=str,
        default='runs',
        help='tensorboard logdirectory')
    p.add_argument('--num_epochs', type=int, default=2500,
                   help='number of times to iterate through all samples')
    p.add_argument('--batch_size', type=int, default=1024,
                   help='samples that will be processed in parallel')
    p.add_argument(
        '--patience',
        type=int,
        default=20,
        help='stop training after no improvement in this many epochs')
    p.add_argument('--minimum_epochs', type=int, default=0,
                   help='minimum numer of epochs to run')
    p.add_argument('--dataset', type=str, default='qm9',
                   help='[qm9, zinc, drugs, geom_qm9, molhiv]')
    p.add_argument('--num_train', type=int, default=-
                   1, help='n samples of the model samples to use for train')
    p.add_argument('--seed', type=int, default=123,
                   help='seed for reproducibility')
    p.add_argument(
        '--num_val',
        type=int,
        default=None,
        help='n samples of the model samples to use for validation')
    p.add_argument(
        '--multithreaded_seeds',
        type=list,
        default=[],
        help='if this is non empty, multiple threads will be started, training the same model but with the different seeds')
    p.add_argument(
        '--seed_data',
        type=int,
        default=123,
        help='if you want to use a different seed for the datasplit')
    p.add_argument('--loss_func', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--critic_loss', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--critic_loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--optimizer', type=str, default='Adam',
                   help='Class name of torch.optim like [Adam, SGD, AdamW]')
    p.add_argument(
        '--optimizer_params',
        type=dict,
        help='parameters with keywords of the chosen optimizer like lr')
    p.add_argument(
        '--lr_scheduler',
        type=str,
        help='Class name of torch.optim.lr_scheduler like [CosineAnnealingLR, ExponentialLR, LambdaLR]')
    p.add_argument(
        '--lr_scheduler_params',
        type=dict,
        help='parameters with keywords of the chosen lr_scheduler')
    p.add_argument('--scheduler_step_per_batch', default=True, type=bool,
                   help='step every batch if true step every epoch otherwise')
    p.add_argument(
        '--log_iterations',
        type=int,
        default=-
        1,
        help='log every log_iterations iterations (-1 for only logging after each epoch)')
    p.add_argument(
        '--expensive_log_iterations',
        type=int,
        default=100,
        help='frequency with which to do expensive logging operations')
    p.add_argument(
        '--eval_per_epochs',
        type=int,
        default=0,
        help='frequency with which to do run the function run_eval_per_epoch that can do some expensive calculations on the val set or sth like that. If this is zero, then the function will never be called')
    p.add_argument(
        '--linear_probing_samples',
        type=int,
        default=500,
        help='number of samples to use for linear probing in the run_eval_per_epoch function of the self supervised trainer')
    p.add_argument(
        '--num_conformers',
        type=int,
        default=3,
        help='number of conformers to use if we are using multiple conformers on the 3d side')
    p.add_argument(
        '--metrics',
        default=[],
        help='tensorboard metrics [mae, mae_denormalized, qm9_properties ...]')
    p.add_argument(
        '--main_metric',
        default='mae_denormalized',
        help='for early stopping etc.')
    p.add_argument('--main_metric_goal', type=str, default='min',
                   help='controls early stopping. [max, min]')
    p.add_argument(
        '--val_per_batch',
        type=bool,
        default=True,
        help='run evaluation every batch and then average over the eval results. When running the molhiv benchmark for example, this needs to be Fale because we need to evaluate on all val data at once since the metric is rocauc')
    p.add_argument('--tensorboard_functions', default=[],
                   help='choices of the TENSORBOARD_FUNCTIONS in utils')
    p.add_argument(
        '--checkpoint',
        type=str,
        help='path to directory that contains a checkpoint to continue training')
    p.add_argument(
        '--pretrain_checkpoint',
        type=str,
        help='Specify path to finetune from a pretrained checkpoint')
    p.add_argument(
        '--transfer_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--frozen_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--exclude_from_transfer',
        default=[],
        help='parameters that usually should not be transferred like batchnorm params')
    p.add_argument('--transferred_lr', type=float, default=None,
                   help='set to use a different LR for transfer layers')
    p.add_argument(
        '--num_epochs_local_only',
        type=int,
        default=1,
        help='when training with OptimalTransportTrainer, this specifies for how many epochs only the local predictions will get a loss')

    p.add_argument(
        '--required_data',
        default=[],
        help='what will be included in a batch like [dgl_graph, targets, dgl_graph3d]')
    p.add_argument('--collate_function', default='graph_collate',
                   help='the collate function to use for DataLoader')
    p.add_argument(
        '--collate_params',
        type=dict,
        default={},
        help='parameters with keywords of the chosen collate function')
    p.add_argument('--use_e_features', default=True, type=bool,
                   help='ignore edge features if set to False')
    p.add_argument(
        '--targets',
        default=[],
        help='properties that should be predicted')
    p.add_argument('--device', type=str, default='cuda',
                   help='What device to train on: cuda or cpu')

    p.add_argument('--dist_embedding', type=bool, default=False,
                   help='add dist embedding to complete graphs edges')
    p.add_argument(
        '--num_radial',
        type=int,
        default=6,
        help='number of frequencies for distance embedding')
    p.add_argument(
        '--models_to_save',
        type=list,
        default=[],
        help='specify after which epochs to remember the best model')

    p.add_argument('--model_type', type=str, default='MPNN',
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model_parameters',
        type=dict,
        help='dictionary of model parameters')

    p.add_argument('--model3d_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model3d_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--critic_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--critic_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--trainer', type=str, default='contrastive',
                   help='[contrastive, byol, alternating, philosophy]')
    p.add_argument('--train_sampler', type=str, default=None,
                   help='any of pytorchs samplers or a custom sampler')

    p.add_argument('--eval_on_test', type=bool, default=True,
                   help='runs evaluation on test set if true')
    p.add_argument(
        '--force_random_split',
        type=bool,
        default=False,
        help='use random split for ogb')
    p.add_argument(
        '--reuse_pre_train_data',
        type=bool,
        default=False,
        help='use all data instead of ignoring that used during pre-training')
    p.add_argument(
        '--transfer_3d',
        type=bool,
        default=True,
        help='set true to load the 3d network instead of the 2d network')
    p.add_argument(
        '--smiles_txt_path',
        type=str,
        default='dataset/inference_smiles.txt',
        help='')
    return p.parse_args()

def parse_arguments_3():
    """Interprets the many argumneants that are provided to the model class"""
    p = argparse.ArgumentParser()
    p.add_argument(
        '--config',
        type=argparse.FileType(
            mode='r'),
        default='configs_clean/pre-train_distance_predictor_baseline.yml')
    p.add_argument(
        '--experiment_name',
        type=str,
        help='name that will be added to the runs folder output')
    p.add_argument(
        '--logdir',
        type=str,
        default='runs',
        help='tensorboard logdirectory')
    p.add_argument('--num_epochs', type=int, default=2500,
                   help='number of times to iterate through all samples')
    p.add_argument('--batch_size', type=int, default=1024,
                   help='samples that will be processed in parallel')
    p.add_argument(
        '--patience',
        type=int,
        default=20,
        help='stop training after no improvement in this many epochs')
    p.add_argument('--minimum_epochs', type=int, default=0,
                   help='minimum numer of epochs to run')
    p.add_argument('--dataset', type=str, default='qm9',
                   help='[qm9, zinc, drugs, geom_qm9, molhiv]')
    p.add_argument('--num_train', type=int, default=-
                   1, help='n samples of the model samples to use for train')
    p.add_argument('--seed', type=int, default=123,
                   help='seed for reproducibility')
    p.add_argument(
        '--num_val',
        type=int,
        default=None,
        help='n samples of the model samples to use for validation')
    p.add_argument(
        '--multithreaded_seeds',
        type=list,
        default=[],
        help='if this is non empty, multiple threads will be started, training the same model but with the different seeds')
    p.add_argument(
        '--seed_data',
        type=int,
        default=123,
        help='if you want to use a different seed for the datasplit')
    p.add_argument('--loss_func', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--critic_loss', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--critic_loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--optimizer', type=str, default='Adam',
                   help='Class name of torch.optim like [Adam, SGD, AdamW]')
    p.add_argument(
        '--optimizer_params',
        type=dict,
        help='parameters with keywords of the chosen optimizer like lr')
    p.add_argument(
        '--lr_scheduler',
        type=str,
        help='Class name of torch.optim.lr_scheduler like [CosineAnnealingLR, ExponentialLR, LambdaLR]')
    p.add_argument(
        '--lr_scheduler_params',
        type=dict,
        help='parameters with keywords of the chosen lr_scheduler')
    p.add_argument('--scheduler_step_per_batch', default=True, type=bool,
                   help='step every batch if true step every epoch otherwise')
    p.add_argument(
        '--log_iterations',
        type=int,
        default=-
        1,
        help='log every log_iterations iterations (-1 for only logging after each epoch)')
    p.add_argument(
        '--expensive_log_iterations',
        type=int,
        default=100,
        help='frequency with which to do expensive logging operations')
    p.add_argument(
        '--eval_per_epochs',
        type=int,
        default=0,
        help='frequency with which to do run the function run_eval_per_epoch that can do some expensive calculations on the val set or sth like that. If this is zero, then the function will never be called')
    p.add_argument(
        '--linear_probing_samples',
        type=int,
        default=500,
        help='number of samples to use for linear probing in the run_eval_per_epoch function of the self supervised trainer')
    p.add_argument(
        '--num_conformers',
        type=int,
        default=3,
        help='number of conformers to use if we are using multiple conformers on the 3d side')
    p.add_argument(
        '--metrics',
        default=[],
        help='tensorboard metrics [mae, mae_denormalized, qm9_properties ...]')
    p.add_argument(
        '--main_metric',
        default='mae_denormalized',
        help='for early stopping etc.')
    p.add_argument('--main_metric_goal', type=str, default='min',
                   help='controls early stopping. [max, min]')
    p.add_argument(
        '--val_per_batch',
        type=bool,
        default=True,
        help='run evaluation every batch and then average over the eval results. When running the molhiv benchmark for example, this needs to be Fale because we need to evaluate on all val data at once since the metric is rocauc')
    p.add_argument('--tensorboard_functions', default=[],
                   help='choices of the TENSORBOARD_FUNCTIONS in utils')
    p.add_argument(
        '--checkpoint',
        type=str,
        help='path to directory that contains a checkpoint to continue training')
    p.add_argument(
        '--pretrain_checkpoint',
        type=str,
        help='Specify path to finetune from a pretrained checkpoint')
    p.add_argument(
        '--transfer_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--frozen_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--exclude_from_transfer',
        default=[],
        help='parameters that usually should not be transferred like batchnorm params')
    p.add_argument('--transferred_lr', type=float, default=None,
                   help='set to use a different LR for transfer layers')
    p.add_argument(
        '--num_epochs_local_only',
        type=int,
        default=1,
        help='when training with OptimalTransportTrainer, this specifies for how many epochs only the local predictions will get a loss')

    p.add_argument(
        '--required_data',
        default=[],
        help='what will be included in a batch like [dgl_graph, targets, dgl_graph3d]')
    p.add_argument('--collate_function', default='graph_collate',
                   help='the collate function to use for DataLoader')
    p.add_argument(
        '--collate_params',
        type=dict,
        default={},
        help='parameters with keywords of the chosen collate function')
    p.add_argument('--use_e_features', default=True, type=bool,
                   help='ignore edge features if set to False')
    p.add_argument(
        '--targets',
        default=[],
        help='properties that should be predicted')
    p.add_argument('--device', type=str, default='cuda',
                   help='What device to train on: cuda or cpu')

    p.add_argument('--dist_embedding', type=bool, default=False,
                   help='add dist embedding to complete graphs edges')
    p.add_argument(
        '--num_radial',
        type=int,
        default=6,
        help='number of frequencies for distance embedding')
    p.add_argument(
        '--models_to_save',
        type=list,
        default=[],
        help='specify after which epochs to remember the best model')

    p.add_argument('--model_type', type=str, default='MPNN',
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model_parameters',
        type=dict,
        help='dictionary of model parameters')

    p.add_argument('--model3d_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model3d_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--critic_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--critic_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--trainer', type=str, default='contrastive',
                   help='[contrastive, byol, alternating, philosophy]')
    p.add_argument('--train_sampler', type=str, default=None,
                   help='any of pytorchs samplers or a custom sampler')

    p.add_argument('--eval_on_test', type=bool, default=True,
                   help='runs evaluation on test set if true')
    p.add_argument(
        '--force_random_split',
        type=bool,
        default=False,
        help='use random split for ogb')
    p.add_argument(
        '--reuse_pre_train_data',
        type=bool,
        default=False,
        help='use all data instead of ignoring that used during pre-training')
    p.add_argument(
        '--transfer_3d',
        type=bool,
        default=True,
        help='set true to load the 3d network instead of the 2d network')
    p.add_argument(
        '--smiles_txt_path',
        type=str,
        default='dataset/inference_smiles.txt',
        help='')
    return p.parse_args()

def parse_arguments_4():
    """Interprets the many argumneants that are provided to the model class"""
    p = argparse.ArgumentParser()
    p.add_argument(
        '--config',
        type=argparse.FileType(
            mode='r'),
        default='configs_clean/pre-train_GEOM-Drugs.yml')
    p.add_argument(
        '--experiment_name',
        type=str,
        help='name that will be added to the runs folder output')
    p.add_argument(
        '--logdir',
        type=str,
        default='runs',
        help='tensorboard logdirectory')
    p.add_argument('--num_epochs', type=int, default=2500,
                   help='number of times to iterate through all samples')
    p.add_argument('--batch_size', type=int, default=1024,
                   help='samples that will be processed in parallel')
    p.add_argument(
        '--patience',
        type=int,
        default=20,
        help='stop training after no improvement in this many epochs')
    p.add_argument('--minimum_epochs', type=int, default=0,
                   help='minimum numer of epochs to run')
    p.add_argument('--dataset', type=str, default='qm9',
                   help='[qm9, zinc, drugs, geom_qm9, molhiv]')
    p.add_argument('--num_train', type=int, default=-
                   1, help='n samples of the model samples to use for train')
    p.add_argument('--seed', type=int, default=123,
                   help='seed for reproducibility')
    p.add_argument(
        '--num_val',
        type=int,
        default=None,
        help='n samples of the model samples to use for validation')
    p.add_argument(
        '--multithreaded_seeds',
        type=list,
        default=[],
        help='if this is non empty, multiple threads will be started, training the same model but with the different seeds')
    p.add_argument(
        '--seed_data',
        type=int,
        default=123,
        help='if you want to use a different seed for the datasplit')
    p.add_argument('--loss_func', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--critic_loss', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--critic_loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--optimizer', type=str, default='Adam',
                   help='Class name of torch.optim like [Adam, SGD, AdamW]')
    p.add_argument(
        '--optimizer_params',
        type=dict,
        help='parameters with keywords of the chosen optimizer like lr')
    p.add_argument(
        '--lr_scheduler',
        type=str,
        help='Class name of torch.optim.lr_scheduler like [CosineAnnealingLR, ExponentialLR, LambdaLR]')
    p.add_argument(
        '--lr_scheduler_params',
        type=dict,
        help='parameters with keywords of the chosen lr_scheduler')
    p.add_argument('--scheduler_step_per_batch', default=True, type=bool,
                   help='step every batch if true step every epoch otherwise')
    p.add_argument(
        '--log_iterations',
        type=int,
        default=-
        1,
        help='log every log_iterations iterations (-1 for only logging after each epoch)')
    p.add_argument(
        '--expensive_log_iterations',
        type=int,
        default=100,
        help='frequency with which to do expensive logging operations')
    p.add_argument(
        '--eval_per_epochs',
        type=int,
        default=0,
        help='frequency with which to do run the function run_eval_per_epoch that can do some expensive calculations on the val set or sth like that. If this is zero, then the function will never be called')
    p.add_argument(
        '--linear_probing_samples',
        type=int,
        default=500,
        help='number of samples to use for linear probing in the run_eval_per_epoch function of the self supervised trainer')
    p.add_argument(
        '--num_conformers',
        type=int,
        default=3,
        help='number of conformers to use if we are using multiple conformers on the 3d side')
    p.add_argument(
        '--metrics',
        default=[],
        help='tensorboard metrics [mae, mae_denormalized, qm9_properties ...]')
    p.add_argument(
        '--main_metric',
        default='mae_denormalized',
        help='for early stopping etc.')
    p.add_argument('--main_metric_goal', type=str, default='min',
                   help='controls early stopping. [max, min]')
    p.add_argument(
        '--val_per_batch',
        type=bool,
        default=True,
        help='run evaluation every batch and then average over the eval results. When running the molhiv benchmark for example, this needs to be Fale because we need to evaluate on all val data at once since the metric is rocauc')
    p.add_argument('--tensorboard_functions', default=[],
                   help='choices of the TENSORBOARD_FUNCTIONS in utils')
    p.add_argument(
        '--checkpoint',
        type=str,
        help='path to directory that contains a checkpoint to continue training')
    p.add_argument(
        '--pretrain_checkpoint',
        type=str,
        help='Specify path to finetune from a pretrained checkpoint')
    p.add_argument(
        '--transfer_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--frozen_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--exclude_from_transfer',
        default=[],
        help='parameters that usually should not be transferred like batchnorm params')
    p.add_argument('--transferred_lr', type=float, default=None,
                   help='set to use a different LR for transfer layers')
    p.add_argument(
        '--num_epochs_local_only',
        type=int,
        default=1,
        help='when training with OptimalTransportTrainer, this specifies for how many epochs only the local predictions will get a loss')

    p.add_argument(
        '--required_data',
        default=[],
        help='what will be included in a batch like [dgl_graph, targets, dgl_graph3d]')
    p.add_argument('--collate_function', default='graph_collate',
                   help='the collate function to use for DataLoader')
    p.add_argument(
        '--collate_params',
        type=dict,
        default={},
        help='parameters with keywords of the chosen collate function')
    p.add_argument('--use_e_features', default=True, type=bool,
                   help='ignore edge features if set to False')
    p.add_argument(
        '--targets',
        default=[],
        help='properties that should be predicted')
    p.add_argument('--device', type=str, default='cuda',
                   help='What device to train on: cuda or cpu')

    p.add_argument('--dist_embedding', type=bool, default=False,
                   help='add dist embedding to complete graphs edges')
    p.add_argument(
        '--num_radial',
        type=int,
        default=6,
        help='number of frequencies for distance embedding')
    p.add_argument(
        '--models_to_save',
        type=list,
        default=[],
        help='specify after which epochs to remember the best model')

    p.add_argument('--model_type', type=str, default='MPNN',
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model_parameters',
        type=dict,
        help='dictionary of model parameters')

    p.add_argument('--model3d_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model3d_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--critic_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--critic_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--trainer', type=str, default='contrastive',
                   help='[contrastive, byol, alternating, philosophy]')
    p.add_argument('--train_sampler', type=str, default=None,
                   help='any of pytorchs samplers or a custom sampler')

    p.add_argument('--eval_on_test', type=bool, default=True,
                   help='runs evaluation on test set if true')
    p.add_argument(
        '--force_random_split',
        type=bool,
        default=False,
        help='use random split for ogb')
    p.add_argument(
        '--reuse_pre_train_data',
        type=bool,
        default=False,
        help='use all data instead of ignoring that used during pre-training')
    p.add_argument(
        '--transfer_3d',
        type=bool,
        default=True,
        help='set true to load the 3d network instead of the 2d network')
    p.add_argument(
        '--smiles_txt_path',
        type=str,
        default='dataset/inference_smiles.txt',
        help='')
    return p.parse_args()

def parse_arguments_5():
    """Interprets the many argumneants that are provided to the model class"""
    p = argparse.ArgumentParser()
    p.add_argument(
        '--config',
        type=argparse.FileType(
            mode='r'),
        default='configs_clean/pre-train_graphCL_baseline.yml')
    p.add_argument(
        '--experiment_name',
        type=str,
        help='name that will be added to the runs folder output')
    p.add_argument(
        '--logdir',
        type=str,
        default='runs',
        help='tensorboard logdirectory')
    p.add_argument('--num_epochs', type=int, default=2500,
                   help='number of times to iterate through all samples')
    p.add_argument('--batch_size', type=int, default=1024,
                   help='samples that will be processed in parallel')
    p.add_argument(
        '--patience',
        type=int,
        default=20,
        help='stop training after no improvement in this many epochs')
    p.add_argument('--minimum_epochs', type=int, default=0,
                   help='minimum numer of epochs to run')
    p.add_argument('--dataset', type=str, default='qm9',
                   help='[qm9, zinc, drugs, geom_qm9, molhiv]')
    p.add_argument('--num_train', type=int, default=-
                   1, help='n samples of the model samples to use for train')
    p.add_argument('--seed', type=int, default=123,
                   help='seed for reproducibility')
    p.add_argument(
        '--num_val',
        type=int,
        default=None,
        help='n samples of the model samples to use for validation')
    p.add_argument(
        '--multithreaded_seeds',
        type=list,
        default=[],
        help='if this is non empty, multiple threads will be started, training the same model but with the different seeds')
    p.add_argument(
        '--seed_data',
        type=int,
        default=123,
        help='if you want to use a different seed for the datasplit')
    p.add_argument('--loss_func', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--critic_loss', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--critic_loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--optimizer', type=str, default='Adam',
                   help='Class name of torch.optim like [Adam, SGD, AdamW]')
    p.add_argument(
        '--optimizer_params',
        type=dict,
        help='parameters with keywords of the chosen optimizer like lr')
    p.add_argument(
        '--lr_scheduler',
        type=str,
        help='Class name of torch.optim.lr_scheduler like [CosineAnnealingLR, ExponentialLR, LambdaLR]')
    p.add_argument(
        '--lr_scheduler_params',
        type=dict,
        help='parameters with keywords of the chosen lr_scheduler')
    p.add_argument('--scheduler_step_per_batch', default=True, type=bool,
                   help='step every batch if true step every epoch otherwise')
    p.add_argument(
        '--log_iterations',
        type=int,
        default=-
        1,
        help='log every log_iterations iterations (-1 for only logging after each epoch)')
    p.add_argument(
        '--expensive_log_iterations',
        type=int,
        default=100,
        help='frequency with which to do expensive logging operations')
    p.add_argument(
        '--eval_per_epochs',
        type=int,
        default=0,
        help='frequency with which to do run the function run_eval_per_epoch that can do some expensive calculations on the val set or sth like that. If this is zero, then the function will never be called')
    p.add_argument(
        '--linear_probing_samples',
        type=int,
        default=500,
        help='number of samples to use for linear probing in the run_eval_per_epoch function of the self supervised trainer')
    p.add_argument(
        '--num_conformers',
        type=int,
        default=3,
        help='number of conformers to use if we are using multiple conformers on the 3d side')
    p.add_argument(
        '--metrics',
        default=[],
        help='tensorboard metrics [mae, mae_denormalized, qm9_properties ...]')
    p.add_argument(
        '--main_metric',
        default='mae_denormalized',
        help='for early stopping etc.')
    p.add_argument('--main_metric_goal', type=str, default='min',
                   help='controls early stopping. [max, min]')
    p.add_argument(
        '--val_per_batch',
        type=bool,
        default=True,
        help='run evaluation every batch and then average over the eval results. When running the molhiv benchmark for example, this needs to be Fale because we need to evaluate on all val data at once since the metric is rocauc')
    p.add_argument('--tensorboard_functions', default=[],
                   help='choices of the TENSORBOARD_FUNCTIONS in utils')
    p.add_argument(
        '--checkpoint',
        type=str,
        help='path to directory that contains a checkpoint to continue training')
    p.add_argument(
        '--pretrain_checkpoint',
        type=str,
        help='Specify path to finetune from a pretrained checkpoint')
    p.add_argument(
        '--transfer_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--frozen_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--exclude_from_transfer',
        default=[],
        help='parameters that usually should not be transferred like batchnorm params')
    p.add_argument('--transferred_lr', type=float, default=None,
                   help='set to use a different LR for transfer layers')
    p.add_argument(
        '--num_epochs_local_only',
        type=int,
        default=1,
        help='when training with OptimalTransportTrainer, this specifies for how many epochs only the local predictions will get a loss')

    p.add_argument(
        '--required_data',
        default=[],
        help='what will be included in a batch like [dgl_graph, targets, dgl_graph3d]')
    p.add_argument('--collate_function', default='graph_collate',
                   help='the collate function to use for DataLoader')
    p.add_argument(
        '--collate_params',
        type=dict,
        default={},
        help='parameters with keywords of the chosen collate function')
    p.add_argument('--use_e_features', default=True, type=bool,
                   help='ignore edge features if set to False')
    p.add_argument(
        '--targets',
        default=[],
        help='properties that should be predicted')
    p.add_argument('--device', type=str, default='cuda',
                   help='What device to train on: cuda or cpu')

    p.add_argument('--dist_embedding', type=bool, default=False,
                   help='add dist embedding to complete graphs edges')
    p.add_argument(
        '--num_radial',
        type=int,
        default=6,
        help='number of frequencies for distance embedding')
    p.add_argument(
        '--models_to_save',
        type=list,
        default=[],
        help='specify after which epochs to remember the best model')

    p.add_argument('--model_type', type=str, default='MPNN',
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model_parameters',
        type=dict,
        help='dictionary of model parameters')

    p.add_argument('--model3d_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model3d_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--critic_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--critic_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--trainer', type=str, default='contrastive',
                   help='[contrastive, byol, alternating, philosophy]')
    p.add_argument('--train_sampler', type=str, default=None,
                   help='any of pytorchs samplers or a custom sampler')

    p.add_argument('--eval_on_test', type=bool, default=True,
                   help='runs evaluation on test set if true')
    p.add_argument(
        '--force_random_split',
        type=bool,
        default=False,
        help='use random split for ogb')
    p.add_argument(
        '--reuse_pre_train_data',
        type=bool,
        default=False,
        help='use all data instead of ignoring that used during pre-training')
    p.add_argument(
        '--transfer_3d',
        type=bool,
        default=True,
        help='set true to load the 3d network instead of the 2d network')
    p.add_argument(
        '--smiles_txt_path',
        type=str,
        default='dataset/inference_smiles.txt',
        help='')
    return p.parse_args()

def parse_arguments_6():
    """Interprets the many argumneants that are provided to the model class"""
    p = argparse.ArgumentParser()
    p.add_argument(
        '--config',
        type=argparse.FileType(
            mode='r'),
        default='configs_clean/pre-train_Optimal_Transport_baseline.yml')
    p.add_argument(
        '--experiment_name',
        type=str,
        help='name that will be added to the runs folder output')
    p.add_argument(
        '--logdir',
        type=str,
        default='runs',
        help='tensorboard logdirectory')
    p.add_argument('--num_epochs', type=int, default=2500,
                   help='number of times to iterate through all samples')
    p.add_argument('--batch_size', type=int, default=1024,
                   help='samples that will be processed in parallel')
    p.add_argument(
        '--patience',
        type=int,
        default=20,
        help='stop training after no improvement in this many epochs')
    p.add_argument('--minimum_epochs', type=int, default=0,
                   help='minimum numer of epochs to run')
    p.add_argument('--dataset', type=str, default='qm9',
                   help='[qm9, zinc, drugs, geom_qm9, molhiv]')
    p.add_argument('--num_train', type=int, default=-
                   1, help='n samples of the model samples to use for train')
    p.add_argument('--seed', type=int, default=123,
                   help='seed for reproducibility')
    p.add_argument(
        '--num_val',
        type=int,
        default=None,
        help='n samples of the model samples to use for validation')
    p.add_argument(
        '--multithreaded_seeds',
        type=list,
        default=[],
        help='if this is non empty, multiple threads will be started, training the same model but with the different seeds')
    p.add_argument(
        '--seed_data',
        type=int,
        default=123,
        help='if you want to use a different seed for the datasplit')
    p.add_argument('--loss_func', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--critic_loss', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--critic_loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--optimizer', type=str, default='Adam',
                   help='Class name of torch.optim like [Adam, SGD, AdamW]')
    p.add_argument(
        '--optimizer_params',
        type=dict,
        help='parameters with keywords of the chosen optimizer like lr')
    p.add_argument(
        '--lr_scheduler',
        type=str,
        help='Class name of torch.optim.lr_scheduler like [CosineAnnealingLR, ExponentialLR, LambdaLR]')
    p.add_argument(
        '--lr_scheduler_params',
        type=dict,
        help='parameters with keywords of the chosen lr_scheduler')
    p.add_argument('--scheduler_step_per_batch', default=True, type=bool,
                   help='step every batch if true step every epoch otherwise')
    p.add_argument(
        '--log_iterations',
        type=int,
        default=-
        1,
        help='log every log_iterations iterations (-1 for only logging after each epoch)')
    p.add_argument(
        '--expensive_log_iterations',
        type=int,
        default=100,
        help='frequency with which to do expensive logging operations')
    p.add_argument(
        '--eval_per_epochs',
        type=int,
        default=0,
        help='frequency with which to do run the function run_eval_per_epoch that can do some expensive calculations on the val set or sth like that. If this is zero, then the function will never be called')
    p.add_argument(
        '--linear_probing_samples',
        type=int,
        default=500,
        help='number of samples to use for linear probing in the run_eval_per_epoch function of the self supervised trainer')
    p.add_argument(
        '--num_conformers',
        type=int,
        default=3,
        help='number of conformers to use if we are using multiple conformers on the 3d side')
    p.add_argument(
        '--metrics',
        default=[],
        help='tensorboard metrics [mae, mae_denormalized, qm9_properties ...]')
    p.add_argument(
        '--main_metric',
        default='mae_denormalized',
        help='for early stopping etc.')
    p.add_argument('--main_metric_goal', type=str, default='min',
                   help='controls early stopping. [max, min]')
    p.add_argument(
        '--val_per_batch',
        type=bool,
        default=True,
        help='run evaluation every batch and then average over the eval results. When running the molhiv benchmark for example, this needs to be Fale because we need to evaluate on all val data at once since the metric is rocauc')
    p.add_argument('--tensorboard_functions', default=[],
                   help='choices of the TENSORBOARD_FUNCTIONS in utils')
    p.add_argument(
        '--checkpoint',
        type=str,
        help='path to directory that contains a checkpoint to continue training')
    p.add_argument(
        '--pretrain_checkpoint',
        type=str,
        help='Specify path to finetune from a pretrained checkpoint')
    p.add_argument(
        '--transfer_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--frozen_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--exclude_from_transfer',
        default=[],
        help='parameters that usually should not be transferred like batchnorm params')
    p.add_argument('--transferred_lr', type=float, default=None,
                   help='set to use a different LR for transfer layers')
    p.add_argument(
        '--num_epochs_local_only',
        type=int,
        default=1,
        help='when training with OptimalTransportTrainer, this specifies for how many epochs only the local predictions will get a loss')

    p.add_argument(
        '--required_data',
        default=[],
        help='what will be included in a batch like [dgl_graph, targets, dgl_graph3d]')
    p.add_argument('--collate_function', default='graph_collate',
                   help='the collate function to use for DataLoader')
    p.add_argument(
        '--collate_params',
        type=dict,
        default={},
        help='parameters with keywords of the chosen collate function')
    p.add_argument('--use_e_features', default=True, type=bool,
                   help='ignore edge features if set to False')
    p.add_argument(
        '--targets',
        default=[],
        help='properties that should be predicted')
    p.add_argument('--device', type=str, default='cuda',
                   help='What device to train on: cuda or cpu')

    p.add_argument('--dist_embedding', type=bool, default=False,
                   help='add dist embedding to complete graphs edges')
    p.add_argument(
        '--num_radial',
        type=int,
        default=6,
        help='number of frequencies for distance embedding')
    p.add_argument(
        '--models_to_save',
        type=list,
        default=[],
        help='specify after which epochs to remember the best model')

    p.add_argument('--model_type', type=str, default='MPNN',
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model_parameters',
        type=dict,
        help='dictionary of model parameters')

    p.add_argument('--model3d_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model3d_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--critic_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--critic_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--trainer', type=str, default='contrastive',
                   help='[contrastive, byol, alternating, philosophy]')
    p.add_argument('--train_sampler', type=str, default=None,
                   help='any of pytorchs samplers or a custom sampler')

    p.add_argument('--eval_on_test', type=bool, default=True,
                   help='runs evaluation on test set if true')
    p.add_argument(
        '--force_random_split',
        type=bool,
        default=False,
        help='use random split for ogb')
    p.add_argument(
        '--reuse_pre_train_data',
        type=bool,
        default=False,
        help='use all data instead of ignoring that used during pre-training')
    p.add_argument(
        '--transfer_3d',
        type=bool,
        default=True,
        help='set true to load the 3d network instead of the 2d network')
    p.add_argument(
        '--smiles_txt_path',
        type=str,
        default='dataset/inference_smiles.txt',
        help='')
    return p.parse_args()

def parse_arguments_7():
    """Interprets the many argumneants that are provided to the model class"""
    p = argparse.ArgumentParser()
    p.add_argument(
        '--config',
        type=argparse.FileType(
            mode='r'),
        default='configs_clean/pre-train_QMugs.yml')
    p.add_argument(
        '--experiment_name',
        type=str,
        help='name that will be added to the runs folder output')
    p.add_argument(
        '--logdir',
        type=str,
        default='runs',
        help='tensorboard logdirectory')
    p.add_argument('--num_epochs', type=int, default=2500,
                   help='number of times to iterate through all samples')
    p.add_argument('--batch_size', type=int, default=1024,
                   help='samples that will be processed in parallel')
    p.add_argument(
        '--patience',
        type=int,
        default=20,
        help='stop training after no improvement in this many epochs')
    p.add_argument('--minimum_epochs', type=int, default=0,
                   help='minimum numer of epochs to run')
    p.add_argument('--dataset', type=str, default='qm9',
                   help='[qm9, zinc, drugs, geom_qm9, molhiv]')
    p.add_argument('--num_train', type=int, default=-
                   1, help='n samples of the model samples to use for train')
    p.add_argument('--seed', type=int, default=123,
                   help='seed for reproducibility')
    p.add_argument(
        '--num_val',
        type=int,
        default=None,
        help='n samples of the model samples to use for validation')
    p.add_argument(
        '--multithreaded_seeds',
        type=list,
        default=[],
        help='if this is non empty, multiple threads will be started, training the same model but with the different seeds')
    p.add_argument(
        '--seed_data',
        type=int,
        default=123,
        help='if you want to use a different seed for the datasplit')
    p.add_argument('--loss_func', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--critic_loss', type=str, default='MSELoss',
                   help='Class name of torch.nn like [MSELoss, L1Loss]')
    p.add_argument('--critic_loss_params', type=dict, default={},
                   help='parameters with keywords of the chosen loss function')
    p.add_argument('--optimizer', type=str, default='Adam',
                   help='Class name of torch.optim like [Adam, SGD, AdamW]')
    p.add_argument(
        '--optimizer_params',
        type=dict,
        help='parameters with keywords of the chosen optimizer like lr')
    p.add_argument(
        '--lr_scheduler',
        type=str,
        help='Class name of torch.optim.lr_scheduler like [CosineAnnealingLR, ExponentialLR, LambdaLR]')
    p.add_argument(
        '--lr_scheduler_params',
        type=dict,
        help='parameters with keywords of the chosen lr_scheduler')
    p.add_argument('--scheduler_step_per_batch', default=True, type=bool,
                   help='step every batch if true step every epoch otherwise')
    p.add_argument(
        '--log_iterations',
        type=int,
        default=-
        1,
        help='log every log_iterations iterations (-1 for only logging after each epoch)')
    p.add_argument(
        '--expensive_log_iterations',
        type=int,
        default=100,
        help='frequency with which to do expensive logging operations')
    p.add_argument(
        '--eval_per_epochs',
        type=int,
        default=0,
        help='frequency with which to do run the function run_eval_per_epoch that can do some expensive calculations on the val set or sth like that. If this is zero, then the function will never be called')
    p.add_argument(
        '--linear_probing_samples',
        type=int,
        default=500,
        help='number of samples to use for linear probing in the run_eval_per_epoch function of the self supervised trainer')
    p.add_argument(
        '--num_conformers',
        type=int,
        default=3,
        help='number of conformers to use if we are using multiple conformers on the 3d side')
    p.add_argument(
        '--metrics',
        default=[],
        help='tensorboard metrics [mae, mae_denormalized, qm9_properties ...]')
    p.add_argument(
        '--main_metric',
        default='mae_denormalized',
        help='for early stopping etc.')
    p.add_argument('--main_metric_goal', type=str, default='min',
                   help='controls early stopping. [max, min]')
    p.add_argument(
        '--val_per_batch',
        type=bool,
        default=True,
        help='run evaluation every batch and then average over the eval results. When running the molhiv benchmark for example, this needs to be Fale because we need to evaluate on all val data at once since the metric is rocauc')
    p.add_argument('--tensorboard_functions', default=[],
                   help='choices of the TENSORBOARD_FUNCTIONS in utils')
    p.add_argument(
        '--checkpoint',
        type=str,
        help='path to directory that contains a checkpoint to continue training')
    p.add_argument(
        '--pretrain_checkpoint',
        type=str,
        help='Specify path to finetune from a pretrained checkpoint')
    p.add_argument(
        '--transfer_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--frozen_layers',
        default=[],
        help='strings contained in the keys of the weights that are transferred')
    p.add_argument(
        '--exclude_from_transfer',
        default=[],
        help='parameters that usually should not be transferred like batchnorm params')
    p.add_argument('--transferred_lr', type=float, default=None,
                   help='set to use a different LR for transfer layers')
    p.add_argument(
        '--num_epochs_local_only',
        type=int,
        default=1,
        help='when training with OptimalTransportTrainer, this specifies for how many epochs only the local predictions will get a loss')

    p.add_argument(
        '--required_data',
        default=[],
        help='what will be included in a batch like [dgl_graph, targets, dgl_graph3d]')
    p.add_argument('--collate_function', default='graph_collate',
                   help='the collate function to use for DataLoader')
    p.add_argument(
        '--collate_params',
        type=dict,
        default={},
        help='parameters with keywords of the chosen collate function')
    p.add_argument('--use_e_features', default=True, type=bool,
                   help='ignore edge features if set to False')
    p.add_argument(
        '--targets',
        default=[],
        help='properties that should be predicted')
    p.add_argument('--device', type=str, default='cuda',
                   help='What device to train on: cuda or cpu')

    p.add_argument('--dist_embedding', type=bool, default=False,
                   help='add dist embedding to complete graphs edges')
    p.add_argument(
        '--num_radial',
        type=int,
        default=6,
        help='number of frequencies for distance embedding')
    p.add_argument(
        '--models_to_save',
        type=list,
        default=[],
        help='specify after which epochs to remember the best model')

    p.add_argument('--model_type', type=str, default='MPNN',
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model_parameters',
        type=dict,
        help='dictionary of model parameters')

    p.add_argument('--model3d_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--model3d_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--critic_type', type=str, default=None,
                   help='Classname of one of the models in the models dir')
    p.add_argument(
        '--critic_parameters',
        type=dict,
        help='dictionary of model parameters')
    p.add_argument('--trainer', type=str, default='contrastive',
                   help='[contrastive, byol, alternating, philosophy]')
    p.add_argument('--train_sampler', type=str, default=None,
                   help='any of pytorchs samplers or a custom sampler')

    p.add_argument('--eval_on_test', type=bool, default=True,
                   help='runs evaluation on test set if true')
    p.add_argument(
        '--force_random_split',
        type=bool,
        default=False,
        help='use random split for ogb')
    p.add_argument(
        '--reuse_pre_train_data',
        type=bool,
        default=False,
        help='use all data instead of ignoring that used during pre-training')
    p.add_argument(
        '--transfer_3d',
        type=bool,
        default=True,
        help='set true to load the 3d network instead of the 2d network')
    p.add_argument(
        '--smiles_txt_path',
        type=str,
        default='dataset/inference_smiles.txt',
        help='')
    return p.parse_args()

def get_arguments(test_no):
    """a helper fucntions that parses the parameters of the various benchmarks"""
    if test_no==1:
        args = parse_arguments_1()
    if test_no==2:
        args = parse_arguments_2()
    if test_no==3:
        args = parse_arguments_3()
    if test_no==4:
        args = parse_arguments_4()
    if test_no==5:
        args = parse_arguments_5()
    if test_no==6:
        args = parse_arguments_6()
    if test_no==7:
        args = parse_arguments_7()
    if args.config:
        config_dict = yaml.load(args.config, Loader=yaml.FullLoader)
        arg_dict = args.__dict__
        for key, value in config_dict.items():
            if isinstance(value, list):
                for v in value:
                    arg_dict[key].append(v)
            else:
                arg_dict[key] = value
    else:
        config_dict = {}

    if args.checkpoint:  # overwrite args with args from checkpoint except for the args that were contained in the config file
        arg_dict = args.__dict__
        with open(os.path.join(os.path.dirname(args.checkpoint), 'train_arguments.yaml'), 'r') as arg_file:
            checkpoint_dict = yaml.load(arg_file, Loader=yaml.FullLoader)
        for key, value in checkpoint_dict.items():
            if key not in config_dict.keys():
                if isinstance(value, list):
                    for v in value:
                        arg_dict[key].append(v)
                else:
                    arg_dict[key] = value

    return args

@pytest.mark.parametrize(
    "args",[get_arguments(1)]
)
def test_args_2D_Model(args):
    '''
    Tests if the argument parsing function is working or is empty. If this doesn't work, no data will reach our mdoel.
    '''
    assert args != argparse.Namespace()

@pytest.mark.parametrize(
    "args",[get_arguments(2)]
)
def test_args_3D_Model(args):
    '''
    Tests if the argument parsing function is working or is empty. If this doesn't work, no data will reach our mdoel.
    '''
    assert args != argparse.Namespace()

@pytest.mark.parametrize(
    "args",[get_arguments(3)]
)
def test_args_Distance_Predictor_Baseline(args):
    '''
    Tests if the argument parsing function is working or is empty. If this doesn't work, no data will reach our mdoel.
    '''
    assert args != argparse.Namespace()

@pytest.mark.parametrize(
    "args",[get_arguments(4)]
)
def test_args_GEOM_Drugs(args):
    '''
    Tests if the argument parsing function is working or is empty. If this doesn't work, no data will reach our mdoel.
    '''
    assert args != argparse.Namespace()

@pytest.mark.parametrize(
    "args",[get_arguments(5)]
)
def test_args_graphCL_baseline(args):
    '''
    Tests if the argument parsing function is working or is empty. If this doesn't work, no data will reach our mdoel.
    '''
    assert args != argparse.Namespace()

@pytest.mark.parametrize(
    "args",[get_arguments(6)]
)
def test_args_Optimal_Transport_baseline(args):
    '''
    Tests if the argument parsing function is working or is empty. If this doesn't work, no data will reach our mdoel.
    '''
    assert args != argparse.Namespace()

@pytest.mark.parametrize(
    "args",[get_arguments(7)]
)
def test_args_QMugs(args):
    '''
    Tests if the argument parsing function is working or is empty. If this doesn't work, no data will reach our mdoel.
    '''
    assert args != argparse.Namespace()

