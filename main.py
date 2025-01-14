import argparse
import torch
import random
from datetime import datetime
import wandb
import os
import json
wandb.login(key=os.environ["WANDB_API_KEY"])

from dataloader import get_dataloaders
from utils import get_model
from train import Trainer

parser = argparse.ArgumentParser()
parser.add_argument('--project', type=str, default="mlp_mixer")
parser.add_argument('--output', type=str, default=f"./out")
parser.add_argument('--experiment', type=str, default=f"experiment_{datetime.now().strftime('%Y-%m-%d_%H:%M:%S')}")
parser.add_argument('--dataset', required=True, choices=['c10', 'c100', 'svhn'])
parser.add_argument('--model', required=True, choices=['mlp_mixer'])
parser.add_argument('--batch-size', type=int, default=128)
parser.add_argument('--eval-batch-size', type=int, default=1024)
parser.add_argument('--valid-ratio', type=float, default=0.5)
parser.add_argument('--num-workers', type=int, default=4)
parser.add_argument('--seed', type=int, default=random.randint(1, 1e5))
parser.add_argument('--epochs', type=int, default=300)
# parser.add_argument('--precision', type=int, default=16)

parser.add_argument('--patch-size', type=int, default=4)
parser.add_argument('--hidden-size', type=int, default=128)
parser.add_argument('--hidden-c', type=int, default=512)
parser.add_argument('--hidden-s', type=int, default=64)
parser.add_argument('--num-layers', type=int, default=8)
parser.add_argument('--drop-p', type=int, default=0.)
parser.add_argument('--off-act', action='store_true', help='Disable activation function')
parser.add_argument('--is-cls-token', action='store_true', help='Introduce a class token.')

parser.add_argument('--lr', type=float, default=1e-3)
parser.add_argument('--min-lr', type=float, default=1e-6)
parser.add_argument('--momentum', type=float, default=0.9)
parser.add_argument('--optimizer', default='adam', choices=['adam', 'sgd'])
parser.add_argument('--scheduler', default='cosine', choices=['step', 'cosine'])
parser.add_argument('--beta1', type=float, default=0.9)
parser.add_argument('--beta2', type=float, default=0.99)
parser.add_argument('--weight-decay', type=float, default=5e-5)
parser.add_argument('--off-nesterov', action='store_true')
parser.add_argument('--label-smoothing', type=float, default=0.1)
parser.add_argument('--gamma', type=float, default=0.1)
parser.add_argument('--warmup-epoch', type=int, default=5)
parser.add_argument('--autoaugment', action='store_true')
parser.add_argument('--clip-grad', type=float, default=0, help="0 means disabling clip-grad")
parser.add_argument('--cutmix-beta', type=float, default=1.0)
parser.add_argument('--cutmix-prob', type=float, default=0.)

args = parser.parse_args()
args.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
args.nesterov = not args.off_nesterov
torch.random.manual_seed(args.seed)


if __name__ == '__main__':
    with wandb.init(project=args.project, config=args, name=args.experiment):
        config = args.__dict__.copy()
        config['device'] = config['device'].__str__()
        path = os.path.join(args.output, args.experiment)
        os.makedirs(path, exist_ok=True)
        with open(path + '/params.json', 'w') as ff:
            json.dump(config, ff, indent=4, sort_keys=True)

        train_dl, valid_dl, test_dl = get_dataloaders(args)
        model = get_model(args)
        trainer = Trainer(model, args)
        trainer.fit(train_dl, valid_dl, test_dl, args)

