#!/bin/bash

#SBATCH -N 1                      # Number of nodes requested
#SBATCH -n 1                      # Number of tasks (i.e. processes)
#SBATCH --cpus-per-task=4         # Number of cores per task
#SBATCH --gres=gpu:l40s:1         # Request a L40S GPU
#SBATCH --nodelist=al-l40s-0.grasp.maas
#SBATCH --qos=al-high-2gpu        # QoS
#SBATCH --partition=aloque-compute
#SBATCH -t 1-00:00                # Maximum time (24h)
#SBATCH -D /home/waybaba/code/ese651_project

##SBATCH -o slurm.%N.%j.out
##SBATCH -e slurm.%N.%j.err

# Print some info for context
pwd
hostname
date

echo "Starting reward tuning job..."

source ~/.bashrc
conda activate env_isaaclab
export PYTHONPATH=$PYTHONPATH:/home/waybaba/code/ese651_project/src

export PYTHONUNBUFFERED=1

# Reward tuning parameters - 重点调优gamma和gate_passed_reward
# Test different gamma values (discount factor)
gamma_values=(0.99 0.999)
# Test different gate passed reward scales
gate_reward_values=(1.0 10.0)
# Test different time reward scales
time_reward_values=(0.0 -0.01)

# Sequentially launch experiments
run_id=1
for gamma in "${gamma_values[@]}"; do
    for gate_reward in "${gate_reward_values[@]}"; do
        for time_reward in "${time_reward_values[@]}"; do
            echo "Running experiment $run_id: gamma=$gamma, gate_reward=$gate_reward, time_reward=$time_reward"
            
            # Run training with modified reward parameters
            python scripts/rsl_rl/train_race.py \
                --task Isaac-Quadcopter-Race-v0 \
                --num_envs 8192 \
                --max_iterations 5000 \
                --headless \
                --logger wandb \
                --seed 42 \
                --gamma $gamma \
                --gate_passed_reward_scale $gate_reward \
                --time_reward_scale $time_reward
            
            echo "Finished experiment $run_id"
            run_id=$((run_id + 1))
            
            wait
            sleep 30
        done
    done
done

# Print completion time
date
echo "All reward tuning experiments completed!"
