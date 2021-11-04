import pickle

import numpy as np
import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F

import onconet.transformers.factory as transformer_factory
from onconet.models.factory import get_model
from onconet.transformers.basic import ComposeTrans
from onconet.utils import parsing


def load_model(args):
    args.cuda = args.cuda and torch.cuda.is_available()

    if args.model_name == 'mirai_full':
        model = get_model(args)
    else:
        model = torch.load(args.snapshot, map_location='cpu')

    # Unpack models taht were trained as data parallel
    if isinstance(model, nn.DataParallel):
        model = model.module

    # Add use precomputed hiddens for models trained before it was introduced.
    # Assumes a resnet WHybase backbone
    try:
        model._model.args.use_precomputed_hiddens = args.use_precomputed_hiddens
        model._model.args.cuda = args.cuda
    except Exception as e:
        pass

    return model


def load_callibrator(args):
    # Load callibrator if desired
    if args.callibrator_path is not None:
        callibrator = pickle.load(open(args.callibrator_path, 'rb'))
    else:
        callibrator = None

    return callibrator


def process_image_joint(batch, model, callibrator, args, risk_factor_vector=None):
    ## Apply transformers
    x = batch['x']
    risk_factors = autograd.Variable(risk_factor_vector.unsqueeze(0)) if risk_factor_vector is not None else None

    if args.cuda:
        x = x.cuda()
        model = model.cuda()
    else:
        model = model.cpu()

    ## Index 0 to toss batch dimension
    logit, _, _ = model(x, risk_factors, batch)
    probs = F.sigmoid(logit).cpu().data.numpy()
    pred_y = np.zeros(probs.shape[1])

    if callibrator is not None:
        print("Raw Probs: {}".format(probs))
        for i in callibrator.keys():
            pred_y[i] = callibrator[i].predict_proba(probs[0, i].reshape(-1, 1))[0, 1]

    return pred_y.tolist()


def process_exam(images, risk_factor_vector, args):
    test_image_transformers = parsing.parse_transformers(args.test_image_transformers)
    test_tensor_transformers = parsing.parse_transformers(args.test_tensor_transformers)
    test_transformers = transformer_factory.get_transformers(test_image_transformers, test_tensor_transformers, args)
    transforms = ComposeTrans(test_transformers)

    batch = collate_batch(images, transforms)
    model = load_model(args)
    callibrator = load_callibrator(args)
    y = process_image_joint(batch, model, callibrator, args, risk_factor_vector)

    return y


def collate_batch(images, transforms):
    batch = {}

    batch['side_seq'] = torch.cat([torch.tensor(b['side_seq']).unsqueeze(0) for b in images], dim=0).unsqueeze(0)
    batch['view_seq'] = torch.cat([torch.tensor(b['view_seq']).unsqueeze(0) for b in images], dim=0).unsqueeze(0)
    batch['time_seq'] = torch.zeros_like(batch['view_seq'])

    batch['x'] = torch.cat(
        (lambda imgs: [transforms(b['x']).unsqueeze(0) for b in imgs])(images), dim=0
    ).unsqueeze(0).transpose(1, 2)

    return batch
