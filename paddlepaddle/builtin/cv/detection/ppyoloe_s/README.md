# PPYOLOE for PaddlePaddle

<!--命名规则 {model_name}-{dataset}-{framework}-->

[TOC]

## 模型简介

PP-YOLOE是基于PP-YOLOv2的卓越的单阶段Anchor-free模型，超越了多种流行的YOLO模型。PP-YOLOE有一系列的模型，即s/m/l/x，可以通过width multiplier和depth multiplier配置。PP-YOLOE避免了使用诸如Deformable Convolution或者Matrix NMS之类的特殊算子，以使其能轻松地部署在多种多样的硬件上

<!--可选-->
论文地址：[PP-YOLOE: An evolved version of YOLO](https://arxiv.org/abs/2203.16250)

Github工程地址：[ppyoloe](https://github.com/PaddlePaddle/PaddleDetection/tree/release/2.7/configs/ppyoloe) [yolov6 后处理](https://github.com/meituan/YOLOv6) 

数据集（COCO）：https://cocodataset.org/

## 资源准备

1. 数据集资源下载

	COCO数据集是一个可用于图像检测（image detection），语义分割（semantic segmentation）和图像标题生成（image captioning）的大规模数据集。这里只需要下载2017 Train images\2017 Val images\和对应的annotation。下载请前往[COCO官网](https://github.com/ultralytics/yolov5/releases/download/v1.0/coco128_with_yaml.zip)。

2. 模型权重下载

	百度网盘： [ppyoloe_s.pdmodel, ppyoloe_s.pdiparams](https://pan.baidu.com/s/1KWW-coMIYTJ2V4-Caq5G-g?pwd=k5pa)。

3. 清微github modelzoo仓库下载

	```git clone https://github.com/tsingmicro-toolchain/ts.knight-modelzoo.git```

## Knight环境准备

1. 联系清微智能获取Knight工具链版本包 ```ReleaseDeliverables/ts.knight-x.x.x.x.tar.gz ```。下面以ts.knight-3.0.0.11.build1.tar.gz为例演示。

2. 检查docker环境

	​默认服务器中已安装docker（版本>=19.03）, 如未安装可参考文档ReleaseDocuments/《TS.Knight-使用指南综述_V1.4.pdf》。
	
	```
	docker -v   
	```

3. 加载镜像
	
	```
	docker load -i ts.knight-3.0.0.11.build1.tar.gz
	```

4. 启动docker容器

	```
	docker run -v ${localhost_dir}/ts.knight-modelzoo:/ts.knight-modelzoo -it ts.knight:3.0.0.11.build1 /bin/bash
	```
	
	localhost_dir为宿主机目录。

## 快速体验

在docker 容器内运行以下命令:

```
cd /ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/
```

```
sh ppyoloe_s/scripts/run.sh
```

## 模型部署流程

### 1. 量化

-   模型准备
	
	如上述"Knight环境准备"章节所述，准备好ppyoloe_s的paddlepaddle权重文件以及下载yolov6工程放到`src`下。由于ppyoloe_s的后处理已经放在infer函数中处理，所以需要对原工程yolov6目录下的[line134](https://github.com/meituan/YOLOv6/blob/e9656c307ae62032f40b39c7a7a5ccc31c2f0242/yolov6/models/heads/effidehead_distill_ns.py#L134) 增加如下一行代码：  
	`return cls_score_list, reg_lrtb_list`
	

-   量化数据准备

    这里使用[COCO128](https://github.com/ultralytics/yolov5/releases/download/v1.0/coco128_with_yaml.zip)数据集作为量化校准数据集,将数据放在`${localhost_dir}/ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/data/`， 通过命令行参数```-i 128```指定图片数量,```-d```指定coco128.yaml所在的路径。

-   模型转换函数、推理函数准备
	
	已提供量化依赖的模型转换和推理函数py文件: ```/ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/src/ppyoloe_s.py```

-   执行量化命令

	在容器内执行如下量化命令，生成量化后的文件 yolov6_quantize.onnx 存放在 -s 指定输出目录。
		
		#paddle转onnx
    	Knight --chip TX5368AV200 quant onnx -m /ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/weight/ppyoloe_s.pdmodel
    		-w /ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/weight/ppyoloe_s.pdiparams
    		-f paddle 
    		-r convert
			-s ./tmp/ppyoloe_s
    	
		# 后处理部分裁剪掉
		cd /ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/src
		python cut_graph.py --model ./tmp/ppyoloe_s/ppyoloe_s.onnx -on transpose_3.tmp_0 p2o.Concat.31 -sn ppyoloe_s -s ./tmp/ppyoloe_s
		
		#对裁剪后onnx模型进行量化
		Knight --chip TX5368AV200 quant onnx -m tmp/ppyoloe_s/ppyoloe_s.onnx 
    		-uds /ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/src/ppyoloe_s.py 
    		-if ppyoloe_s
			-s ./tmp/ppyoloe_s
    		-d /ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/data/coco128.yaml
    		-bs 1 -i 128


### 2. 编译


    Knight --chip TX5368AV200 rne-compile --onnx ppyoloe_s_quantize.onnx --outpath .


### 3. 仿真

    #准备bin数据
    python3 src/make_image_input_onnx.py  --input /ts.knight-modelzoo/paddlepaddle/builtin/cv/detection/ppyoloe_s/data/images/train2017 --outpath .
    #仿真
    Knight --chip TX5368AV200 rne-sim --input model_input.bin --weight ppyoloe_s_quantize_r.weight --config  ppyoloe_s_quantize_r.cfg --outpath .

### 4. 性能分析

```
Knight --chip TX5368AV200 rne-profiling --config  ppyoloe_s_quantize_r.cfg --outpath .
```

### 5. 仿真库

### 6. 板端部署



## 支持芯片情况

| 芯片系列                                          | 是否支持 |
| ------------------------------------------------ | ------- |
| TX510x                                           | 支持     |
| TX5368x_TX5339x                                  | 支持     |
| TX5215x_TX5239x200_TX5239x220 | 支持     |
| TX5112x201_TX5239x201                            | 支持     |
| TX5336AV200                                      | 支持     |



## 版本说明

2023/11/23  第一版



## LICENSE

ModelZoo Edge 的 License 具体内容请参见LICENSE文件

## 免责说明

您明确了解并同意，以上链接中的软件、数据或者模型由第三方提供并负责维护。在以上链接中出现的任何第三方的名称、商标、标识、产品或服务并不构成明示或暗示与该第三方或其软件、数据或模型的相关背书、担保或推荐行为。您进一步了解并同意，使用任何第三方软件、数据或者模型，包括您提供的任何信息或个人数据（不论是有意或无意地），应受相关使用条款、许可协议、隐私政策或其他此类协议的约束。因此，使用链接中的软件、数据或者模型可能导致的所有风险将由您自行承担。



