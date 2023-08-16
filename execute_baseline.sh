export WANDB_API_KEY="21d72275648132f2136abaa14ddd913550563d16"
source environ/bin/activate
CUDA_LAUNCH_BLOCKING=1 CUDA_VISIBLE_DEVICES=0 python main.py \
	--dataset c10 \
	--model mlp_mixer \
	--autoaugment \
	--cutmix-prob 0.5 \
	--seed 1337 \
	--valid-ratio 0.5
