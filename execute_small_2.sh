export WANDB_API_KEY="21d72275648132f2136abaa14ddd913550563d16"
source environ/bin/activate
CUDA_LAUNCH_BLOCKING=1 CUDA_VISIBLE_DEVICES=5 python main.py --dataset c10 --model mlp_mixer --autoaugment --cutmix-prob 0.5 --seed 123456 --hidden-size 64 --hidden-c 256 --hidden-s 32 --batch-size 128 --num-layers 4
