# ResNset for PaddlePaddle

<!--命名规则 {model_name}-{dataset}-{framework}-->

[TOC]

## 模型简介

RestNet是2015年由微软团队提出的，在当时获得分类任务，目标检测，图像分割第一名。该论文的四位作者何恺明、张祥雨、任少卿和孙剑如今在人工智能领域里都是响当当的名字，当时他们都是微软亚研的一员。实验结果显示，残差网络更容易优化，并且加深网络层数有助于提高正确率。在ImageNet上使用152层的残差网络（VGG net的8倍深度，但残差网络复杂度更低）。对这些网络使用集成方法实现了3.75%的错误率。获得了ILSVRC 2015竞赛的第一名。
                        
原文链接：https://blog.csdn.net/lsb2002/article/details/130748991

<!--可选-->论文：[《Deep Residual Learning for Image Recognition》](https://www.cv-foundation.org/openaccess/content_cvpr_2016/papers/He_Deep_Residual_Learning_CVPR_2016_paper.pdf)

开源模型链接：https://github.com/PaddlePaddle/PaddleClas/blob/231de43cddb4ae0870870eab889c347468d36404/ppcls/arch/backbone/model_zoo/resnext.py

数据集（ImageNet）：http://www.image-net.org/

## 资源准备

1. 数据集资源下载

	ImageNet是一个不可用于商业目的的数据集，必须通过教育网邮箱注册登录后下载, 请前往官方自行下载[ImageNet](http://image-net.org/)。

2. 模型资源下载

	[resnet50.pdparams](https://paddle-imagenet-models-name.bj.bcebos.com/dygraph/ResNeXt50_32x4d_pretrained.pdparams)
	
> 注意:这里`resnet50.pdparams`是动态模型，需要先转成静态模型`resnet50.pdmodel,resnet50.pdiparams`

3. 清微github modelzoo仓库下载

	```git clone https://github.com/tsingmicro-toolchain/ts.knight-modelzoo.git```

## Knight环境准备

1. 联系清微智能获取Knight工具链版本包 ```ReleaseDeliverables/ts.knight-x.x.x.x.tar.gz ```。下面以ts.knight-2.0.0.4.tar.gz为例演示。

2. 检查docker环境

	​默认服务器中已安装docker（版本>=19.03）, 如未安装可参考文档ReleaseDocuments/《TS.Knight-使用指南综述_V1.4.pdf》。
	
	```
	docker -v   
	```

3. 加载镜像
	
	```
	docker load -i ts.knight-2.0.0.4.tar.gz
	```

4. 启动docker容器

	```
	docker run -v ${localhost_dir}/ts.knight-modelzoo:/ts.knight-modelzoo -it ts.knight:2.0.0.4 /bin/bash
	```
	
	localhost_dir为宿主机目录。

## 快速体验

在docker 容器内运行以下命令:

```
cd /ts.knight-modelzoo/paddlepaddle/builtin/cv/classification/
```

```
sh resnet50/scripts/run.sh
```

## 模型移植流程

### 1. 量化

-   模型准备
	
	如上述"Knight环境准备"章节所述，准备好resnet50重文件。
	

-   量化数据准备

    在数据集中选200张图片作为量化校准数据集, 通过命令行参数```-i 200```指定图片数量，```-d```指定数据集路径。

-   模型转换函数、推理函数准备
	
	已提供量化依赖的模型转换和推理函数py文件: ```/ts.knight-modelzoo/paddlepaddle/builtin/cv/classification/resnet50/src/resnet50.py```

-   执行量化命令

	在容器内执行如下量化命令，生成量化后的文件 `resnet50_quantize.onnx` 存放在 -s 指定输出目录。

    	Knight --chip TX5368AV200 quant onnx 
			-m /ts.knight-modelzoo/paddlepaddle/builtin/cv/classification/resnet50/weight/resnet50.pdmodel
    		-w /ts.knight-modelzoo/paddlepaddle/builtin/cv/classification/resnet50/weight/resnet50.pdiparams
    		-f paddle 
    		-uds /ts.knight-modelzoo/paddlepaddle/builtin/cv/classification/resnet50/src/resnet50.py 
    		-if infer_imagenet_benchmark 
			-s ./tmp/resnet50
    		-d /ts.knight-modelzoo/paddlepaddle/builtin/cv/classification/resnet50/data/imagenet/images/val 
    		-bs 1 -i 200


### 2. 编译


    Knight --chip TX5368AV200 rne-compile --onnx resnet50_quantize.onnx --outpath resnet50_example/compile_result


### 3. 仿真

    #准备bin数据
    python3 make_resnet50_input_bin.py.py  
    #仿真
    Knight --chip TX5368A rne-sim --input input.bin --weight resnet50_quantize_r.weight --config  resnet50_quantize_r.cfg --outpath resnet50_quantize_example

### 4. 性能分析

```
Knight --chip TX5368A rne-profiling --weight  resnet50_quantize_r.weight --config  resnet50_quantize_r.cfg --outpath  resnet50_quantize_example/
```

### 5. 仿真库

### 6. 板端部署



## 支持芯片情况

| 芯片系列                                          | 是否支持 |
| ------------------------------------------------ | ------- |
| TX510x                                           | 支持     |
| TX5368x_TX5339x                                  | 支持     |
| TX5215x_TX5119x_TX5112x200_TX5239x200_TX5239x220 | 支持     |
| TX5112x201_TX5239x201                            | 支持     |
| TX5336AV200                                      | 支持     |



## 版本说明

2023/11/23  第一版



## LICENSE

ModelZoo Edge 的 License 具体内容请参见LICENSE文件

## 免责说明

您明确了解并同意，以上链接中的软件、数据或者模型由第三方提供并负责维护。在以上链接中出现的任何第三方的名称、商标、标识、产品或服务并不构成明示或暗示与该第三方或其软件、数据或模型的相关背书、担保或推荐行为。您进一步了解并同意，使用任何第三方软件、数据或者模型，包括您提供的任何信息或个人数据（不论是有意或无意地），应受相关使用条款、许可协议、隐私政策或其他此类协议的约束。因此，使用链接中的软件、数据或者模型可能导致的所有风险将由您自行承担。


