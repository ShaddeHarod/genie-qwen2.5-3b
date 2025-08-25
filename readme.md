

#### 将文件及文件夹放入到` data/local/tmp/genie-qwen2.5-3b`中并运行` run_adb_shell.sh`脚本

1. 在手机adb shell的` data/local/tmp`里创建` genie-qwen2.5-3b`文件夹

2. 在` genie-qwen2.5-3b`文件夹中，将文件夹` model_files`里的所有文件(注意是把此文件夹里的文件全部放到` genie-qwen2.5-3b`文件夹中，不是把此文件夹放进去)、` prompts_by_subject`文件夹、` required_json`文件夹、`read_all_subjects_prompts.sh`、` read_prompts.sh`、` run_adb_model.sh`放进去，用adb push指令。最终` genie-qwen2.5-3b`文件夹里的文件有：

   ```shell
   # model_files 里的所有文件
   # prompts_by_subject 文件夹
   # required_json 文件夹
   # `read_all_subjects_prompts.sh` shell 脚本
   # `read_prompts.sh` shell 脚本
   # `run_adb_model.sh` shell 脚本
   ```



3. **在ADB Shell `genie-qwen2.5-3b`中运行:**

``` shell
sh run_adb_model.sh
```

4. 模型运行后会将每道题目、每个科目的结果放到` genie-qwen2.5-3b/result`中



#### 运行` run_after_adb_complete.ps1`分析Qwen2.5-3B在MMLU各科目的表现

1. 在adb 连接的情况下，**在主机工作区，在powershell中运行powershell脚本：**

``` 
.\run_after_adb_complete.ps1
```

​	模型给出的答案会放入` subjects_answers_from_model`文件夹中，并将性能结果(csv、xlsx、png文件)放置于` subjects_perf_results`文件夹中。

> $fileList = adb shell ls data/local/tmp/genie-qwen2.5-3b/result/*_LLM_Answer.json 检查路径是否正确



#### P.S.

1. 如果出了错误，模型需要从头跑所有的科目的题目，请把`required_json`文件夹重新ADB push到` genie-qwen2.5-3b` 中。因为` finished_subjects.json`记录了各科目跑完的题目数量，全部归零就是从头开始跑。

2. ` htp_backend_ext_config.json`的修改(如果用小米14，则不用做修改)，可以在手机的设置中看芯片型号。其中，json文件中的` soc_model`后的value不用加引号，` dsp_arch`的value需要加半角引号

   | Generation          | `soc_model` | `dsp_arch` |
   | ------------------- | ----------- | ---------- |
   | Snapdragon® Gen 2   | 43          | v73        |
   | Snapdragon® Gen 3   | 57          | v75        |
   | Snapdragon® 8 Elite | 69          | v79        |
   | Snapdragon® X Elite | 60          | v73        |
   | Snapdragon® X Plus  | 60          | v73        |

3. ` .so`和` genie-t2t-run`的粘贴，此` genie_bundle`即为` data/local/tmp/genie-qwen2.5-3b`文件夹。(如果用小米14，则不用做修改)粘贴一下内容前，请先把` genie-qwen2.5-3b`中的` *.so`文件删掉。

   ```
   # For 8 Gen 2
   cp $QNN_SDK_ROOT/lib/hexagon-v73/unsigned/* genie_bundle
   # For 8 Gen 3
   cp $QNN_SDK_ROOT/lib/hexagon-v75/unsigned/* genie_bundle
   # For 8 Elite
   cp $QNN_SDK_ROOT/lib/hexagon-v79/unsigned/* genie_bundle
   # For all devices
   cp $QNN_SDK_ROOT/lib/aarch64-android/* genie_bundle
   cp $QNN_SDK_ROOT/bin/aarch64-android/genie-t2t-run genie_bundle
   ```

4. ` run_adb_model.sh`脚本运行有中断续测的功能，下次运行只需重新运行此脚本就可以了。