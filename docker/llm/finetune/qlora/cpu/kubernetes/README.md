## Run Distributed QLoRA Fine-Tuning on Kubernetes with OneCCL

![image](https://github.com/intel-analytics/BigDL/assets/60865256/825f47d9-c864-4f39-a331-adb1e3cb528e)

BigDL here provides a CPU optimization to accelerate the QLoRA finetuning of Llama2-7b, in the power of mixed-precision and distributed training. Detailedly, [Intel OneCCL](https://www.intel.com/content/www/us/en/developer/tools/oneapi/oneccl.html), an available Hugging Face backend, is able to speed up the Pytorch computation with BF16 datatype on CPUs, as well as parallel processing on Kubernetes enabled by [Intel MPI](https://www.intel.com/content/www/us/en/developer/tools/oneapi/mpi-library.html). Moreover, advanaced quantization of BigDL-LLM has been applied to improve memory utilization, which makes CPU large-scale fine-tuning possible with runtime NF4 model storage and BF16 computing types.

The architecture is illustrated in the following:

As above, BigDL implements its MPI training with [Kubeflow MPI operator](https://github.com/kubeflow/mpi-operator/tree/master), which encapsulates the deployment as MPIJob CRD, and assists users to handle the construction of a MPI worker cluster on Kubernetes, such as public key distribution, SSH connection, and log collection. 

Now, let's go to deploy a QLoRA finetuning to create a new LLM from Llama2-7b.

**Note: Please make sure you have already have an available Kubernetes infrastructure and NFS shared storage, and install [Helm CLI](https://helm.sh/docs/helm/helm_install/) for Kubernetes job submission.**

### 1. Install Kubeflow MPI Operator

Follow [here](https://github.com/kubeflow/mpi-operator/tree/master#installation) to install a Kubeflow MPI operator in your Kubernetes, which will listen and receive the following MPIJob request at backend.

### 2. Download Image, Base Model and Finetuning Data

Follow [here](https://github.com/intel-analytics/BigDL/tree/main/docker/llm/finetune/qlora/cpu/docker#1-prepare-docker-image) to prepare BigDL QLoRA Finetuning image in your cluster.

As finetuning is from a base model, first download [Llama2-7b model from the public download site of Hugging Face](https://huggingface.co/meta-llama/Llama-2-7b). Then, download [cleaned alpaca data](https://raw.githubusercontent.com/tloen/alpaca-lora/main/alpaca_data_cleaned_archive.json), which contains all kinds of general knowledge and has already been cleaned. Next, move the downloaded files to a shared directory on your NFS server.

### 3. Deploy through Helm Chart

You are allowed to edit and experiment with different parameters in `./kubernetes/values.yaml` to improve finetuning performance and accuracy. For example, you can adjust `trainerNum` and `cpuPerPod` according to node and CPU core numbers in your cluster to make full use of these resources, and different `microBatchSize` result in different training speed and loss (here note that `microBatchSize`×`trainerNum` should not more than 128, as it is the batch size).

**Note: `dataSubPath` and `modelSubPath` need to have the same names as files under the NFS directory in step 2.**

After preparing parameters in `./kubernetes/values.yaml`, submit the job as beflow:

```bash
cd ./kubernetes
helm install bigdl-qlora-finetuning .
```

### 4. Check Deployment
```bash
kubectl get all -n bigdl-qlora-finetuning # you will see launcher and worker pods running
```

### 5. Check Finetuning Process

After deploying successfully, you can find a launcher pod, and then go inside this pod and check the logs collected from all workers.

```bash
kubectl get all -n bigdl-qlora-finetuning # you will see a launcher pod
kubectl exec -it <launcher_pod_name> bash -n bigdl-qlora-finetuning # enter launcher pod
cat launcher.log # display logs collected from other workers
```

From the log, you can see whether finetuning process has been invoked successfully in all MPI worker pods, and a progress bar with finetuning speed and estimated time will be showed after some data preprocessing steps (this may take quiet a while).

For the fine-tuned model, it is written by the worker 0 (who holds rank 0), so you can find the model output inside the pod, which can be saved to host by command tools like `kubectl cp` or `scp`.
