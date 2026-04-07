# 蛋白组数据

|                     | Gallus | Anas  | Columba |
| ------------------- | ------ | ----- | ------- |
| Identified peptides | 20460  | 30914 | 45495   |
| Unique peptides     | 18111  | 20411 | 44537   |
| Identified Protein  | 3156   | 3978  | 5040    |
| Comparable Protein  | 2874   | 3763  | 4894    |

## orthofinder

[orthofinder](https://orthovenn2.bioinfotoolkits.net/home "蛋白质组跨物种比对")

### 参数设定

#### Algorithm

OrthoFinder (效率高于OrthoMCL)

#### Expansions and contractions analysis

基因家族扩张及收缩分系，通过物种演化时间信息计算

Gallus | Anas | Columba

GvsA 83.37 | GvsC 90.84 million years ago

#### P-value (蛋白质比对显著性)

    1e-5 | 1e-10

#### inflation value (膨胀系数，在保证cluste数稳定前提下，选择较小的系数)

    1.5 | 2 | 2.5 | 3 | 4 | 5 | 6

|                    |             | Cluster No.    | Single copy cluster | All Protein     | Single Tone    | Percentage of singletons | times            |
| ------------------ | ----------- | -------------- | ------------------- | --------------- | -------------- | ------------------------ | ---------------- |
| E-value            | Inflation   |                |                     |                 |                |                          |                  |
| 1.00E-05           | 1.5         | 3227           | 1202                | 11504           | 1043           | 9.07                     | 15:46            |
|                    | 2           | 3227           | 1202                | 11504           | 1043           | 9.07                     | 15:37            |
|                    | 2.5         | 3227           | 1202                | 11504           | 1043           | 9.07                     | 15:17            |
|                    | 3           | 3227           | 1202                | 11504           | 1043           | 9.07                     | 15:38            |
|                    | 4 MCL       | 3342           | 1591                | 11504           | 2121           | 18.44                    | 15:40            |
|                    | 4 Finder    | 3227           | 1202                | 11504           | 1043           | 9.07                     | 16:04            |
|                    | 5           | 3227           | 1202                | 11504           | 1043           | 9.07                     | 15:57            |
|                    | 6           | 3227           | 1202                | 11504           | 1043           | 9.07                     | 16:01            |
|                    | 1           | 3227           | 1202                | 11504           | 1043           | 9.07                     | 16:10            |
| **1.00E-10** | **2** | **3250** | **1232**      | **11504** | **1176** | **10.22**          |                  |
|                    | 1.5         | 3250           | 1232                | 11504           | 1176           | 10.22                    |                  |
|                    | 3           | 3250           | 1232                | 11504           | 1176           | 10.22                    | 2025/10/24 10:02 |

确定参数 1e-10 | 2

#### GO分析

使用三种鸟类的所有蛋白条目同源性进行建库，3250为背景，Count+Enrichment共同为GO分析总结果

##### Gallus & Anas Overlap

**Enrichment outcomes**

**protein glycosylation@bagdonaiteGlycoproteomics2022 | N-glycan processing | protein folding | proteolysis(蛋白质水解)**

##### Columba Unique

ubiquitin-dependent protein catabolic process (依赖泛素性蛋白的代谢过程)

##### Contractions Gallus & Anas with Columba (Hit all)

**nervous system development (神经系统发育) @olkowiczBirdsHavePrimatelike2016**| homophilic cell adhesion via plasma membrane adhesion molecules 鸽子孵化

##### Contractions Columba

Immunology relevant

## GlycoShape

[A GlycoProtein Builder](https://glycoshape.org/reglyco)

下载Glycan的数据库，用extract.py将压缩包中的json文件提取，选择Glycan Chain ID和Mass

使用Mass进行匹配

### Blastp

Blastp E-Value: 1e-5 | NumofHits: 500 | NumofAligns: 250

| Reference | Uniprot_ID | Gallus     | Anas                                                                                   | Columba                                                                                                    |
| --------- | ---------- | ---------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| OC116     | F1NSM7     | A0A8V0XA58 | A0A8B9ZY54<br />R0LL03                                                                 | A0A2I0MGY6                                                                                                 |
| TRFE      | P02789     | A0A8V1A6Y9 | A0A493TBB4                                                                             | A0A2I0LUS7                                                                                                 |
| OVAL      | P01012     | P01012     | A0A493TL04<br />A0A8B9QNT8<br />A0A8B9UXD7<br />U3IKY8<br />A0A493T078<br />A0A8B9UUI8 | A0A1R7T3L5<br />A0A2I0MW20<br />A0A2I0MWA2<br />A0A2I0MED6<br />A0A2I0M204<br />A0A2I0MP02<br />A0A2I0MTU8 |
| OC17      | V5NUE7     | V5NUE7     | A0A8B9TFJ7<br />A0A8B9TTS0                                                             | A0A2I0MIT9                                                                                                 |

进一步进行筛选

* 平均Max Identity ≥ 0.8
* 若Query_NonOverlapped_Hsp_Num ≠ Subject_NonOverlapped_Hsp_Num  则 Max Identity ≥ 0.5

| Reference       | Uniprot_ID | Gallus     | Anas       | Columba    |
| --------------- | ---------- | ---------- | ---------- | ---------- |
| **OVAL**  | P01012     | P01012     | A0A8B9QNT8 | A0A2I0MWA2 |
| **OC116** | F1NSM7     | A0A8V0XA58 | A0A8B9ZY54 | A0A2I0MGY6 |
| **TRFE**  | P02789     | A0A8V1A6Y9 | A0A493TBB4 | A0A2I0LUS7 |
| OC17            | V5NUE7     | V5NUE7     |            |            |

基质蛋白三物种糖链汇总.xlsx ——> 蛋白质糖基化具体信息

# 模型建立

## 3DSlicer 建模

1）阈值分割法建立蛋壳模型

2）选取半径为1mm的区域

3）keep largest island

4）meidian 5x5x5 gallus

5）keep largest island

6）fill holes 9x9x9 gallus

4）导出到stl文件

## Geomagic wrap 反向建模

1）不要使用网格医生，去噪模式，强度为2

2）简化三角形，30w左右

3）重新画网格，0.01mm

4）使用网格医生处理所有缺陷，一直到缺陷都为0

5）精确曲面，使用自动曲面化，有机，自动评估曲面片数量，曲面细节中间，最小公差

4）不修复任何划分错误

5）保存x_t文件

## ~~Ansys显式动力学分析~~

~~1）使用Calcium作为蛋壳材料，IRON CRAM作为破壳齿材料~~

~~2）在spaceclaim中，画个圆锥做为破壳齿，0.1mm—0.5mm，高0.5mm~~

~~3）进入模型，添加虚拟拓扑（如果网格划分有问题的话~~

~~4）设置蛋壳为柔性，破壳齿为刚性~~

~~5）几何体交互，有摩擦的，系数为0.2~~

~~6）全自动网格划分~~

~~7）添加速度30000mm/s，Y分量~~

~~8）分析设置为步长2e-004s~~

~~9）添加固定支撑在蛋壳周围~~

~~10）求解总变形、等效弹性应变、等效应力~~

## Ansys LS-DYNA

更改单位mm/kg/N/s/mV/mA

1）使用一般非线性材料铝合金作为材料模板，修改如下参数，得到蛋壳材料（改名字为eggshell）

    杨氏模量 3E+10 Pa；屈服强度 1.5E+7 Pa；切线模量 0；

    添加参数塑性应变失败—>最大等效塑性应变EPS 0.05

2）破壳齿模型为0.1mm和0.5mm半径的圆台，高度0.5mm，材料为IRON-ARMCO，显式材料

3）删除连接，新增接触，目标几何体为破壳齿，接触集合体为蛋壳模型，类型摩擦的，摩擦系数0.2

4）网格鸡蛋0.05mm，鸽子蛋0.03mm，评判标准为蛋壳剖面的网格数>6，锥体网格0.1mm

5）初始条件，破壳齿分量速度50000mm/s

6）添加固定支撑，蛋壳破面四个方向对称选择

7）添加位移，破壳齿三面，分量，X、Z分量为常熟0、

8）分析设置结束时间1E-4s，时步安全系数0.7，自动质量缩放是，时间步长1E-8s

    CPU数24

    求解器精度双倍

    输出应变是，计算结果等距点，---值100

9）添加RCFORC，**R**esultant **C**ontact **Forc**e (合接触力)，这是 LS-DYNA 计算出的 **接触界面上的相互作用力** ，代表了**破壳齿（Impactor）撞击蛋壳瞬间，蛋壳给破壳齿的反作用力**。

    再LS-DYNA中，添加命令输入

*DATABASE_RCFORC

$ DT (Time interval)

1.0E-06

10）求解总变形，等效应力
